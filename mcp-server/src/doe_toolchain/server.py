"""Gate 0 MCP server skeleton for the DOE Scientific Toolchain."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import itertools
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from doe_toolchain import LAUNCH_TOOL_NAMES, WORKBENCH_TOOL_NAMES, __version__

try:  # pragma: no cover - exercised by MCP startup smoke checks.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - lets import smoke tests explain missing deps.
    FastMCP = None  # type: ignore[assignment]


SERVER_NAME = "doe-scientific-toolchain"
SCHEMA_VERSION = "1.0.0"
METHOD_VERSION = "1.0.0"
ID_RE = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
STATUS_VALUES = {"active", "archived", "superseded", "failed_validation"}
DEFAULT_DOMAIN_TEMPLATE = "general"
REPO_ROOT = Path(__file__).resolve().parents[3]
RECOMMENDATION_MODES = {
    "minimize_runs",
    "screen_important_factors",
    "estimate_interactions",
    "fit_curvature",
    "optimize_response",
    "respect_material_time_constraints",
    "prepare_scale_up_robustness",
    "custom_weighted_objective",
}
CAPABILITY_KEYS = (
    "main_effects",
    "two_factor_interactions",
    "quadratic_terms",
    "curvature_detection",
    "pure_error_estimate",
    "blocking",
    "randomization",
    "missing_run_robustness",
    "sequential_augmentation_path",
)
SUPPORTED_CANDIDATE_FAMILIES = {"d_optimal", "box_behnken", "fractional_factorial", "full_factorial"}
DEFAULT_CANDIDATE_FAMILIES = ("d_optimal", "box_behnken", "fractional_factorial")
FULL_FACTORIAL_LIMIT = 32

mcp = FastMCP(SERVER_NAME) if FastMCP is not None else None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}_{uuid.uuid4().hex[:4]}"


def _workspace_root() -> Path:
    configured = os.environ.get("DOE_TOOLCHAIN_WORKSPACE_ROOT")
    if configured:
        return Path(configured).resolve()
    return REPO_ROOT.resolve()


def _relative_to_workspace(path: Path) -> str:
    return path.resolve().relative_to(_workspace_root()).as_posix()


def _study_dir(study_id: str) -> Path:
    root = (_workspace_root() / "outputs" / "studies").resolve()
    path = (root / study_id).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Study path escapes outputs/studies.")
    return path


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _artifact_hash(artifact: dict[str, Any]) -> str:
    content = copy.deepcopy(artifact)
    metadata = content.get("artifact_metadata")
    if isinstance(metadata, dict):
        metadata["artifact_hash"] = None
    return _canonical_hash(content)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _token(value: Any, length: int = 8) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:length]


def _slug(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug:
        slug = fallback
    if not slug[0].isalpha():
        slug = f"{fallback}_{slug}"
    return slug


def _artifact_metadata(
    *,
    artifact_type: str,
    study_id: str,
    run_id: str,
    tool_name: str,
    input_hash: str,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "artifact_id": f"artifact_{artifact_type}_{uuid.uuid4().hex[:8]}",
        "artifact_type": artifact_type,
        "study_id": study_id,
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "method_version": METHOD_VERSION,
        "tool_name": tool_name,
        "tool_version": __version__,
        "generated_at": _utc_now(),
        "input_hash": input_hash,
        "artifact_hash": "sha256:" + ("0" * 64),
        "warnings": warnings or [],
    }


def _source_artifact_ref(path: Path, artifact_type: str, artifact_hash: str | None = None) -> dict[str, str]:
    return {
        "artifact_type": artifact_type,
        "path": _relative_to_workspace(path),
        "artifact_hash": artifact_hash or _file_hash(path),
    }


def _availability(
    status: str,
    reason: str | None = None,
    required_inputs: list[str] | None = None,
    source_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "required_inputs": required_inputs or [],
        "source_artifacts": source_artifacts or [],
    }


def _invalid_study_envelope(study_id: str | None, run_id: str, field: str = "study_id") -> dict[str, Any] | None:
    if isinstance(study_id, str) and ID_RE.match(study_id):
        return None
    return _envelope(
        study_id=study_id if isinstance(study_id, str) else None,
        run_id=run_id,
        status="failed_validation",
        summary="Study ID failed validation.",
        errors=[
            _error(
                "invalid_study_id",
                "study_id must match ^[a-z][a-z0-9_]*[a-z0-9]$.",
                field,
                {"study_id": study_id},
            )
        ],
    )


def _simple_factor(factor: dict[str, Any], index: int) -> dict[str, Any]:
    raw_name = factor.get("name") or factor.get("display_name") or f"factor_{index + 1}"
    name = _slug(str(raw_name), fallback="factor")
    kind = factor.get("kind", "continuous")
    levels = factor.get("levels") if isinstance(factor.get("levels"), list) else None
    low = factor.get("low")
    high = factor.get("high")
    if kind == "continuous":
        low = float(low if isinstance(low, (int, float)) else 0)
        high = float(high if isinstance(high, (int, float)) else 1)
        default_value: Any = factor.get("default_value")
        if not isinstance(default_value, (int, float)):
            default_value = (low + high) / 2
    else:
        default_value = factor.get("default_value")
        if default_value is None and levels:
            default_value = levels[0]
    return {
        "factor_id": factor.get("factor_id") or f"factor_{name}",
        "name": name,
        "display_name": str(factor.get("display_name") or raw_name),
        "kind": str(kind),
        "units": str(factor.get("units") or "ratio"),
        "low": low if kind == "continuous" else None,
        "high": high if kind == "continuous" else None,
        "levels": levels,
        "default_value": default_value,
        "fixed": bool(factor.get("fixed", False)),
        "transform": factor.get("transform") or {"name": "none", "parameters": {}},
        "coding": factor.get("coding")
        or {"method": "center_scale" if kind == "continuous" else "dummy", "low_coded": -1, "high_coded": 1},
        "role": str(factor.get("role") or "process_factor"),
        "description": str(factor.get("description") or ""),
        "source": str(factor.get("source") or "user_input"),
    }


def _simple_response(response: dict[str, Any], index: int) -> dict[str, Any]:
    raw_name = response.get("name") or response.get("display_name") or f"response_{index + 1}"
    name = _slug(str(raw_name), fallback="response")
    return {
        "response_id": response.get("response_id") or f"response_{name}",
        "name": name,
        "display_name": str(response.get("display_name") or raw_name),
        "role": str(response.get("role") or "productivity"),
        "value_type": str(response.get("value_type") or "measured"),
        "goal": str(response.get("goal") or "maximize"),
        "units": str(response.get("units") or "score"),
        "weight": float(response.get("weight", 1)),
        "threshold": response.get("threshold"),
        "assay": response.get("assay") or {"name": "unspecified", "scale": None, "semi_quantitative": False},
        "source": str(response.get("source") or "user_input"),
    }


def _load_study_document(study_id: str) -> dict[str, Any] | None:
    path = _study_dir(study_id) / "study.json"
    if not path.exists():
        return None
    return _read_json(path)


def _load_setup_from_request_or_disk(
    study_id: str,
    request: dict[str, Any],
    run_id: str,
    tool_name: str,
    input_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, str]]:
    artifact_paths: list[str] = []
    artifact_hashes: dict[str, str] = {}
    study_path = _study_dir(study_id)

    factors_source = request.get("factors")
    if factors_source is None and isinstance(request.get("factor_space"), dict):
        factors_source = request["factor_space"].get("factors")
    responses_source = request.get("responses")

    if isinstance(factors_source, list) and factors_source:
        factors = [_simple_factor(factor, index) for index, factor in enumerate(factors_source) if isinstance(factor, dict)]
        factor_artifact = {
            "artifact_metadata": _artifact_metadata(
                artifact_type="factor_space",
                study_id=study_id,
                run_id=run_id,
                tool_name=tool_name,
                input_hash=input_hash,
            ),
            "factor_space": {
                "factors": factors,
                "constraints": request.get("constraints", []),
                "fixed_conditions": request.get("fixed_conditions", []),
                "normalization": {
                    "internal_name_policy": "lower_snake_case",
                    "default_continuous_coding": "center_scale_to_minus_one_plus_one",
                },
            },
        }
        factor_artifact["artifact_metadata"]["artifact_hash"] = _artifact_hash(factor_artifact)
        factor_path = study_path / "factor_space.json"
        _write_json(factor_path, factor_artifact)
        artifact_paths.append(_relative_to_workspace(factor_path))
        artifact_hashes["factor_space"] = factor_artifact["artifact_metadata"]["artifact_hash"]
    else:
        factor_path = study_path / "factor_space.json"
        if factor_path.exists():
            factor_artifact = _read_json(factor_path)
            factors = list(factor_artifact.get("factor_space", {}).get("factors", []))
            artifact_paths.append(_relative_to_workspace(factor_path))
            artifact_hashes["factor_space"] = str(
                factor_artifact.get("artifact_metadata", {}).get("artifact_hash") or _file_hash(factor_path)
            )
        else:
            factors = []

    if isinstance(responses_source, list) and responses_source:
        responses = [
            _simple_response(response, index)
            for index, response in enumerate(responses_source)
            if isinstance(response, dict)
        ]
        response_artifact = {
            "artifact_metadata": _artifact_metadata(
                artifact_type="responses",
                study_id=study_id,
                run_id=run_id,
                tool_name=tool_name,
                input_hash=input_hash,
            ),
            "responses": responses,
        }
        response_artifact["artifact_metadata"]["artifact_hash"] = _artifact_hash(response_artifact)
        response_path = study_path / "responses.json"
        _write_json(response_path, response_artifact)
        artifact_paths.append(_relative_to_workspace(response_path))
        artifact_hashes["responses"] = response_artifact["artifact_metadata"]["artifact_hash"]
    else:
        response_path = study_path / "responses.json"
        if response_path.exists():
            response_artifact = _read_json(response_path)
            responses = list(response_artifact.get("responses", []))
            artifact_paths.append(_relative_to_workspace(response_path))
            artifact_hashes["responses"] = str(
                response_artifact.get("artifact_metadata", {}).get("artifact_hash") or _file_hash(response_path)
            )
        else:
            responses = []

    return factors, responses, artifact_paths, artifact_hashes


def _continuous_factor_count(factors: list[dict[str, Any]]) -> int:
    return sum(1 for factor in factors if factor.get("kind") == "continuous" and not factor.get("fixed", False))


def _full_quadratic_column_count(n_factors: int) -> int:
    return 1 + n_factors + (n_factors * (n_factors - 1) // 2) + n_factors


def _model_matrix(
    coded_rows: list[list[float]],
    *,
    include_interactions: bool,
    include_quadratics: bool,
    selected_only: bool,
) -> np.ndarray:
    rows: list[list[float]] = []
    n_factors = len(coded_rows[0]) if coded_rows else 0
    interaction_pairs = list(itertools.combinations(range(n_factors), 2))
    if selected_only:
        interaction_pairs = interaction_pairs[: max(1, n_factors - 1)]
        quadratic_factors = list(range(min(2, n_factors)))
    else:
        quadratic_factors = list(range(n_factors))
    for coded in coded_rows:
        row = [1.0]
        row.extend(coded)
        if include_interactions:
            row.extend(coded[i] * coded[j] for i, j in interaction_pairs)
        if include_quadratics:
            row.extend(coded[i] ** 2 for i in quadratic_factors)
        rows.append(row)
    return np.asarray(rows, dtype=float)


def _diagnostics_for_matrix(
    coded_rows: list[list[float]],
    *,
    family: str,
    n_factors: int,
) -> dict[str, Any]:
    if family == "fractional_factorial":
        matrix = _model_matrix(
            coded_rows,
            include_interactions=False,
            include_quadratics=False,
            selected_only=True,
        )
        denominator = _full_quadratic_column_count(n_factors)
    elif family == "d_optimal":
        matrix = _model_matrix(
            coded_rows,
            include_interactions=True,
            include_quadratics=True,
            selected_only=True,
        )
        denominator = _full_quadratic_column_count(n_factors)
    elif family in {"box_behnken", "full_factorial"}:
        matrix = _model_matrix(
            coded_rows,
            include_interactions=True,
            include_quadratics=family == "box_behnken",
            selected_only=False,
        )
        denominator = matrix.shape[1]
    else:
        return {
            "model_matrix_rank": None,
            "n_model_columns": None,
            "condition_number": None,
            "estimable_term_fraction": None,
        }
    rank = int(np.linalg.matrix_rank(matrix)) if matrix.size else 0
    try:
        condition_number = float(np.linalg.cond(matrix))
    except np.linalg.LinAlgError:
        condition_number = float("inf")
    if not np.isfinite(condition_number):
        condition_number_value: float | None = None
    else:
        condition_number_value = round(condition_number, 3)
    return {
        "model_matrix_rank": rank,
        "n_model_columns": int(matrix.shape[1]),
        "condition_number": condition_number_value,
        "estimable_term_fraction": round(min(1.0, rank / max(1, denominator)), 3),
    }


def _fractional_coded_rows(n_factors: int) -> list[list[float]]:
    rows = [list(map(float, combo)) for combo in itertools.product((-1, 1), repeat=n_factors)]
    if n_factors <= 3:
        return rows
    return [row for row in rows if int(np.prod(row)) == 1]


def _box_behnken_coded_rows(n_factors: int) -> list[list[float]]:
    rows: list[list[float]] = []
    for i, j in itertools.combinations(range(n_factors), 2):
        for a, b in itertools.product((-1.0, 1.0), repeat=2):
            row = [0.0] * n_factors
            row[i] = a
            row[j] = b
            rows.append(row)
    rows.extend([[0.0] * n_factors for _ in range(3)])
    return rows


def _d_optimal_coded_rows(n_factors: int, target_runs: int) -> list[list[float]]:
    fractional = _fractional_coded_rows(n_factors)
    axial: list[list[float]] = []
    for index in range(n_factors):
        for value in (-1.0, 1.0):
            row = [0.0] * n_factors
            row[index] = value
            axial.append(row)
    rows = fractional + [[0.0] * n_factors] + axial + [list(map(float, row)) for row in itertools.product((-1, 1), repeat=n_factors)]
    unique: list[list[float]] = []
    seen: set[tuple[float, ...]] = set()
    for row in rows:
        key = tuple(row)
        if key not in seen:
            unique.append(row)
            seen.add(key)
        if len(unique) >= target_runs:
            break
    while len(unique) < target_runs:
        unique.append([0.0] * n_factors)
    return unique


def _full_factorial_coded_rows(n_factors: int) -> list[list[float]]:
    return [list(map(float, combo)) for combo in itertools.product((-1, 1), repeat=n_factors)]


def _coded_to_actual_rows(coded_rows: list[list[float]], factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_factors = [factor for factor in factors if factor.get("kind") == "continuous" and not factor.get("fixed", False)]
    rows: list[dict[str, Any]] = []
    for row_index, coded in enumerate(coded_rows, start=1):
        is_center = all(value == 0 for value in coded)
        rendered: dict[str, Any] = {
            "run_id": f"run_{row_index:03d}",
            "run_order": row_index,
            "run_type": "center_point" if is_center else "model_building",
        }
        for factor, coded_value in zip(active_factors, coded, strict=True):
            low = float(factor.get("low", 0))
            high = float(factor.get("high", 1))
            center = (low + high) / 2
            half_range = (high - low) / 2
            value = center + (coded_value * half_range)
            rendered[str(factor["name"])] = round(value, 6)
        rows.append(rendered)
    return rows


def _write_matrix_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _capabilities_for_family(family: str, status: str) -> dict[str, str]:
    if status == "unsupported":
        return {
            "main_effects": "unknown",
            "two_factor_interactions": "unknown",
            "quadratic_terms": "unknown",
            "curvature_detection": "unknown",
            "pure_error_estimate": "unknown",
            "blocking": "unknown",
            "randomization": "not_applicable",
            "missing_run_robustness": "unknown",
            "sequential_augmentation_path": "unknown",
        }
    if family == "box_behnken":
        return {
            "main_effects": "supported",
            "two_factor_interactions": "supported",
            "quadratic_terms": "supported",
            "curvature_detection": "supported",
            "pure_error_estimate": "partially_supported",
            "blocking": "unknown",
            "randomization": "supported",
            "missing_run_robustness": "partially_supported",
            "sequential_augmentation_path": "supported",
        }
    if family == "d_optimal":
        return {
            "main_effects": "supported",
            "two_factor_interactions": "partially_supported",
            "quadratic_terms": "partially_supported",
            "curvature_detection": "partially_supported",
            "pure_error_estimate": "unsupported",
            "blocking": "unknown",
            "randomization": "supported",
            "missing_run_robustness": "partially_supported",
            "sequential_augmentation_path": "supported",
        }
    if family == "full_factorial":
        return {
            "main_effects": "supported",
            "two_factor_interactions": "supported",
            "quadratic_terms": "unsupported",
            "curvature_detection": "unsupported",
            "pure_error_estimate": "unsupported",
            "blocking": "unknown",
            "randomization": "supported",
            "missing_run_robustness": "partially_supported",
            "sequential_augmentation_path": "partially_supported",
        }
    return {
        "main_effects": "supported",
        "two_factor_interactions": "unsupported",
        "quadratic_terms": "unsupported",
        "curvature_detection": "unsupported",
        "pure_error_estimate": "unsupported",
        "blocking": "unknown",
        "randomization": "supported",
        "missing_run_robustness": "unsupported",
        "sequential_augmentation_path": "partially_supported",
    }


def _ranking_score(family: str, recommendation_mode: str, run_count: int | None, max_runs: int | None) -> float | None:
    if run_count is None:
        return None
    mode_scores: dict[str, dict[str, float]] = {
        "fit_curvature": {"d_optimal": 0.88, "box_behnken": 0.78, "fractional_factorial": 0.41, "full_factorial": 0.46},
        "estimate_interactions": {"box_behnken": 0.84, "d_optimal": 0.78, "full_factorial": 0.72, "fractional_factorial": 0.36},
        "screen_important_factors": {"fractional_factorial": 0.86, "d_optimal": 0.66, "full_factorial": 0.62, "box_behnken": 0.52},
        "minimize_runs": {"fractional_factorial": 0.87, "d_optimal": 0.69, "full_factorial": 0.58, "box_behnken": 0.44},
    }
    score = mode_scores.get(recommendation_mode, mode_scores["fit_curvature"]).get(family, 0.5)
    if max_runs and run_count > max_runs:
        score -= min(0.2, (run_count - max_runs) / max(max_runs, 1) * 0.25)
    return round(max(0.0, min(1.0, score)), 3)


def _learnability_for_candidate(
    *,
    family: str,
    capabilities: dict[str, str],
    metadata_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    metadata_ref = _relative_to_workspace(metadata_path)
    learnable: list[dict[str, Any]] = []
    not_learnable: list[dict[str, Any]] = []
    if capabilities["main_effects"] == "supported":
        learnable.append(
            {
                "claim": "main_effects_estimable",
                "label": "Main effects for active factors are estimable.",
                "support": "supported",
                "reason_code": None,
                "source_ref": f"{metadata_ref}#diagnostics.model_matrix_rank",
            }
        )
    if capabilities["two_factor_interactions"] in {"supported", "partially_supported"}:
        learnable.append(
            {
                "claim": "interaction_terms_estimable",
                "label": "Interaction terms are represented according to the candidate family.",
                "support": capabilities["two_factor_interactions"],
                "reason_code": None,
                "source_ref": f"{metadata_ref}#diagnostics.estimable_term_fraction",
            }
        )
    if capabilities["curvature_detection"] in {"supported", "partially_supported"}:
        learnable.append(
            {
                "claim": "curvature_terms_estimable",
                "label": "Curvature support is available for this response-surface strategy.",
                "support": capabilities["curvature_detection"],
                "reason_code": None,
                "source_ref": f"{metadata_ref}#capabilities.curvature_detection",
            }
        )
    if capabilities["quadratic_terms"] == "unsupported":
        not_learnable.append(
            {
                "claim": "curvature_not_estimable",
                "label": "Curvature cannot be estimated from this candidate design.",
                "support": "unsupported",
                "reason_code": "two_level_design_no_curvature",
                "source_ref": f"{metadata_ref}#warnings",
            }
        )
    elif family == "d_optimal":
        not_learnable.append(
            {
                "claim": "full_quadratic_model_not_estimable",
                "label": "A full quadratic model is not asserted for this reduced candidate.",
                "support": "unsupported",
                "reason_code": "selected_terms_only",
                "source_ref": f"{metadata_ref}#capabilities.quadratic_terms",
            }
        )
    if capabilities["pure_error_estimate"] == "unsupported":
        not_learnable.append(
            {
                "claim": "pure_error_unavailable",
                "label": "Pure error is unavailable without replicated design points.",
                "support": "unsupported",
                "reason_code": "replicates_not_included",
                "source_ref": f"{metadata_ref}#capabilities.pure_error_estimate",
            }
        )
    if not learnable:
        not_learnable.append(
            {
                "claim": "capability_not_computed",
                "label": "This candidate family is not computed by the launch MCP implementation.",
                "support": "unknown",
                "reason_code": "unsupported_design_type",
                "source_ref": f"{metadata_ref}#status",
            }
        )
    return {"learnable": learnable, "not_learnable": not_learnable}


def _latest_child_file(parent: Path, filename: str) -> Path | None:
    if not parent.exists():
        return None
    candidates = [path / filename for path in parent.iterdir() if path.is_dir() and (path / filename).exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _candidate_set_path(study_id: str, candidate_set_id: str | None = None) -> Path | None:
    base = _study_dir(study_id) / "candidate_design_sets"
    if candidate_set_id:
        path = base / candidate_set_id / "candidate_design_set.json"
        return path if path.exists() else None
    return _latest_child_file(base, "candidate_design_set.json")


def _comparison_path(study_id: str, comparison_id: str | None = None) -> Path | None:
    base = _study_dir(study_id) / "comparisons"
    if comparison_id:
        path = base / comparison_id / "design_comparison.json"
        return path if path.exists() else None
    return _latest_child_file(base, "design_comparison.json")


def _run_plan_path(study_id: str, run_plan_id: str | None = None) -> Path | None:
    base = _study_dir(study_id) / "run_plans"
    if run_plan_id:
        path = base / run_plan_id / "run_plan.json"
        return path if path.exists() else None
    return _latest_child_file(base, "run_plan.json")


def _snapshot_path(study_id: str, snapshot_id: str) -> Path | None:
    path = _study_dir(study_id) / "snapshots" / snapshot_id / "snapshot.json"
    return path if path.exists() else None


def _load_candidate_set(study_id: str, candidate_set_id: str | None = None) -> tuple[Path, dict[str, Any]] | None:
    path = _candidate_set_path(study_id, candidate_set_id)
    if path is None:
        return None
    return path, _read_json(path)


def _candidate_by_id(candidate_set: dict[str, Any], candidate_design_id: str) -> dict[str, Any] | None:
    for candidate in candidate_set.get("candidates", []):
        if candidate.get("candidate_design_id") == candidate_design_id:
            return candidate
    return None


def _append_audit(
    *,
    study_id: str,
    run_id: str,
    tool_name: str,
    status: str,
    input_hash: str,
    output_hash: str,
    duration_ms: int,
    artifact_paths: list[str],
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    seed: int | None = None,
) -> None:
    study_path = _study_dir(study_id)
    study_path.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _utc_now(),
        "study_id": study_id,
        "run_id": run_id,
        "tool_name": tool_name,
        "tool_version": __version__,
        "method_version": METHOD_VERSION,
        "schema_version": SCHEMA_VERSION,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "status": status,
        "duration_ms": duration_ms,
        "seed": seed,
        "artifact_paths": artifact_paths,
        "warnings": warnings,
        "errors": errors,
    }
    with (study_path / "audit_log.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _error(code: str, message: str, field: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "field": field,
        "recoverable": True,
        "details": details or {},
    }


def _warning(code: str, message: str, field: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "warning",
        "message": message,
        "field": field,
        "details": details or {},
    }


def _envelope(
    *,
    study_id: str | None,
    run_id: str,
    status: str,
    summary: str,
    artifact_paths: list[str] | None = None,
    artifact_hashes: dict[str, str] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    structured_content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "run_id": run_id,
        "status": status,
        "summary": summary,
        "artifact_paths": artifact_paths or [],
        "artifact_hashes": artifact_hashes or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "structured_content": structured_content or {},
    }


def _slugify_study_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug or not slug[0].isalpha():
        slug = f"study_{slug or 'untitled'}"
    if len(slug) > 40:
        slug = slug[:40].rstrip("_")
    return f"{slug}_{uuid.uuid4().hex[:6]}"


def _register(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    if mcp is not None:
        return mcp.tool()(func)
    return func


@_register
def create_or_update_study(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create or update a study shell and append a Gate 0 audit entry."""

    started = time.perf_counter()
    tool_name = "create_or_update_study"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )

    title = request.get("title")
    if not isinstance(title, str) or not title.strip():
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Study title is required.",
            errors=[_error("missing_required_columns", "request.title is required.", "request.title")],
        )

    resolved_study_id = study_id or request.get("study_id") or _slugify_study_id(title)
    if not isinstance(resolved_study_id, str) or not ID_RE.match(resolved_study_id):
        return _envelope(
            study_id=resolved_study_id if isinstance(resolved_study_id, str) else None,
            run_id=run_id,
            status="failed_validation",
            summary="Study ID failed validation.",
            errors=[
                _error(
                    "invalid_study_id",
                    "study_id must match ^[a-z][a-z0-9_]*[a-z0-9]$.",
                    "study_id",
                    {"study_id": resolved_study_id},
                )
            ],
        )

    status_value = request.get("status", "active")
    if status_value not in STATUS_VALUES:
        return _envelope(
            study_id=resolved_study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Study status failed validation.",
            errors=[
                _error(
                    "invalid_status",
                    "Study status must be active, archived, superseded, or failed_validation.",
                    "request.status",
                    {"status": status_value},
                )
            ],
        )

    now = _utc_now()
    study_path = _study_dir(resolved_study_id)
    existing_path = study_path / "study.json"
    existing_study: dict[str, Any] = {}
    if existing_path.exists():
        existing_study = json.loads(existing_path.read_text(encoding="utf-8")).get("study", {})

    created_at = existing_study.get("created_at", now)
    artifact = {
        "artifact_metadata": {
            "artifact_id": f"artifact_study_{uuid.uuid4().hex[:8]}",
            "artifact_type": "study",
            "study_id": resolved_study_id,
            "run_id": run_id,
            "schema_version": SCHEMA_VERSION,
            "method_version": METHOD_VERSION,
            "tool_name": tool_name,
            "tool_version": __version__,
            "generated_at": now,
            "input_hash": input_hash,
            "artifact_hash": "sha256:" + ("0" * 64),
            "warnings": [],
        },
        "study": {
            "study_id": resolved_study_id,
            "title": title.strip(),
            "domain_template": request.get(
                "domain_template", existing_study.get("domain_template", DEFAULT_DOMAIN_TEMPLATE)
            ),
            "status": status_value,
            "created_at": created_at,
            "updated_at": now,
            "active_design_id": request.get("active_design_id", existing_study.get("active_design_id")),
            "active_fit_id": request.get("active_fit_id", existing_study.get("active_fit_id")),
            "active_construct_id": request.get(
                "active_construct_id", existing_study.get("active_construct_id")
            ),
            "artifact_index": existing_study.get("artifact_index", []),
            "metadata": request.get("metadata", existing_study.get("metadata", {})),
        },
    }
    artifact["artifact_metadata"]["artifact_hash"] = _artifact_hash(artifact)
    _write_json(existing_path, artifact)

    artifact_paths = [_relative_to_workspace(existing_path)]
    artifact_hashes = {"study": artifact["artifact_metadata"]["artifact_hash"]}
    output_hash = _canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths})
    duration_ms = int((time.perf_counter() - started) * 1000)
    _append_audit(
        study_id=resolved_study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=duration_ms,
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )

    action = "Updated" if existing_study else "Created"
    return _envelope(
        study_id=resolved_study_id,
        run_id=run_id,
        status="success",
        summary=f"{action} study {resolved_study_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={
            "study_id": resolved_study_id,
            "study_path": artifact_paths[0],
        },
    )


def _candidate_family_rows(family: str, n_factors: int, max_runs: int | None) -> list[list[float]] | None:
    if family == "fractional_factorial":
        return _fractional_coded_rows(n_factors)
    if family == "box_behnken":
        if n_factors < 3:
            return None
        return _box_behnken_coded_rows(n_factors)
    if family == "d_optimal":
        target = max(1 + n_factors, min(max_runs or (2 * n_factors + 8), 2 * n_factors + 8))
        return _d_optimal_coded_rows(n_factors, target)
    if family == "full_factorial":
        rows = _full_factorial_coded_rows(n_factors)
        return rows if len(rows) <= FULL_FACTORIAL_LIMIT else None
    return None


def _candidate_label(family: str, status: str, recommendation_mode: str) -> str:
    if status == "recommended":
        return "Recommended"
    if status == "unsupported":
        return "Unsupported by launch MCP implementation"
    labels = {
        "d_optimal": "Balanced custom candidate",
        "box_behnken": "Strong curvature support, higher run count",
        "fractional_factorial": "Efficient screening only",
        "full_factorial": "Complete two-level coverage",
    }
    if recommendation_mode == "minimize_runs" and family == "fractional_factorial":
        return "Most run-efficient"
    return labels.get(family, family.replace("_", " ").title())


def _candidate_best_for(family: str) -> list[str]:
    return {
        "d_optimal": ["Selected interactions", "Curvature-oriented first pass", "Fixed run budget"],
        "box_behnken": ["Curvature", "Response-surface interpretation", "Reduced corner exposure"],
        "fractional_factorial": ["Fast main-effect screening", "Low run count"],
        "full_factorial": ["Complete two-level coverage", "Interaction visibility without fractions"],
    }.get(family, ["Capability not computed"])


def _candidate_tradeoffs(family: str, max_runs: int | None, run_count: int | None) -> list[str]:
    tradeoffs = {
        "d_optimal": [
            "Does not assert every two-factor interaction.",
            "Pure error requires adding replicate or center-point policy.",
        ],
        "box_behnken": [
            "Run count can exceed a preferred early-study budget.",
            "Does not sample factor-space corners.",
        ],
        "fractional_factorial": [
            "Cannot fit curvature.",
            "Interactions are aliased with lower-order effects.",
        ],
        "full_factorial": [
            "Run count grows exponentially with factor count.",
            "Two-level factors do not estimate curvature.",
        ],
    }.get(family, ["This design family is not implemented in the launch workbench MCP slice."])
    if max_runs and run_count and run_count > max_runs:
        tradeoffs.append(f"Run count exceeds the preferred {max_runs}-run budget.")
    return tradeoffs


def _candidate_warnings(
    family: str,
    *,
    max_runs: int | None,
    run_count: int | None,
    strict_max_runs: bool,
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if family in {"fractional_factorial", "full_factorial"}:
        warnings.append(
            _warning(
                "curvature_not_supported",
                "Two-level designs do not estimate curvature.",
                "capabilities.curvature_detection",
            )
        )
    if family == "d_optimal":
        warnings.append(
            _warning(
                "pure_error_unavailable",
                "Pure error is unavailable unless replicated points are added to the committed plan.",
                "capabilities.pure_error_estimate",
            )
        )
    if max_runs and run_count and run_count > max_runs:
        warnings.append(
            _warning(
                "run_count_exceeds_preferred_budget" if not strict_max_runs else "run_count_exceeds_hard_budget",
                f"This design has {run_count} runs; the requested budget is {max_runs}.",
                "run_count",
                {"run_count": run_count, "max_runs": max_runs, "strict": strict_max_runs},
            )
        )
    return warnings


def _write_design_artifacts(
    *,
    study_id: str,
    run_id: str,
    tool_name: str,
    input_hash: str,
    candidate_set_id: str,
    candidate_design_id: str,
    design_id: str | None,
    family: str,
    status: str,
    factors: list[dict[str, Any]],
    coded_rows: list[list[float]] | None,
    diagnostics: dict[str, Any],
    capabilities: dict[str, str],
    warnings: list[dict[str, Any]],
    unavailable_reasons: list[str],
) -> tuple[Path, str, Path | None]:
    design_dir = _study_dir(study_id) / "designs" / (design_id or f"design_{candidate_design_id.removeprefix('candidate_')}")
    matrix_path: Path | None = None
    if coded_rows is not None:
        matrix_path = design_dir / "design_matrix.csv"
        _write_matrix_csv(matrix_path, _coded_to_actual_rows(coded_rows, factors))
    metadata_path = design_dir / "design_metadata.json"
    metadata = {
        "artifact_metadata": _artifact_metadata(
            artifact_type="design_metadata",
            study_id=study_id,
            run_id=run_id,
            tool_name=tool_name,
            input_hash=input_hash,
            warnings=warnings,
        ),
        "candidate_set_id": candidate_set_id,
        "candidate_design_id": candidate_design_id,
        "design_id": design_id,
        "design_family": family,
        "status": status,
        "matrix_path": _relative_to_workspace(matrix_path) if matrix_path else None,
        "diagnostics": diagnostics,
        "capabilities": capabilities,
        "unavailable_reasons": unavailable_reasons,
    }
    metadata["artifact_metadata"]["artifact_hash"] = _artifact_hash(metadata)
    _write_json(metadata_path, metadata)
    return metadata_path, metadata["artifact_metadata"]["artifact_hash"], matrix_path


@_register
def generate_candidate_designs(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a persisted candidate design set for the workbench."""

    started = time.perf_counter()
    tool_name = "generate_candidate_designs"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )

    recommendation_mode = str(request.get("recommendation_mode") or "fit_curvature")
    if recommendation_mode not in RECOMMENDATION_MODES:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Recommendation mode failed validation.",
            errors=[
                _error(
                    "invalid_recommendation_mode",
                    "recommendation_mode is not supported by the workbench contract.",
                    "request.recommendation_mode",
                    {"recommendation_mode": recommendation_mode},
                )
            ],
        )

    factors, responses, setup_paths, setup_hashes = _load_setup_from_request_or_disk(
        study_id, request, run_id, tool_name, input_hash
    )
    n_factors = _continuous_factor_count(factors)
    if n_factors < 2:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="At least two continuous active factors are required for candidate generation.",
            artifact_paths=setup_paths,
            artifact_hashes=setup_hashes,
            errors=[
                _error(
                    "insufficient_factor_count",
                    "Provide at least two continuous non-fixed factors.",
                    "request.factors",
                    {"active_continuous_factors": n_factors},
                )
            ],
        )

    candidate_families = request.get("candidate_families")
    if not isinstance(candidate_families, list) or not candidate_families:
        candidate_families = list(DEFAULT_CANDIDATE_FAMILIES)
    candidate_families = [_slug(str(family), fallback="design") for family in candidate_families]
    max_runs_value = request.get("max_runs") or request.get("preferred_max_runs")
    if max_runs_value is None and isinstance(request.get("execution_constraints"), dict):
        max_runs_value = request["execution_constraints"].get("max_runs")
    max_runs = int(max_runs_value) if isinstance(max_runs_value, (int, float)) else 20
    strict_max_runs = bool(request.get("strict_max_runs", False))
    candidate_set_id = str(request.get("candidate_set_id") or f"candidate_set_{_token({'study_id': study_id, 'input': input_hash})}")

    raw_candidates: list[dict[str, Any]] = []
    for family in candidate_families:
        unsupported = family not in SUPPORTED_CANDIDATE_FAMILIES
        coded_rows = None if unsupported else _candidate_family_rows(family, n_factors, max_runs)
        if coded_rows is None:
            unsupported = True
        run_count = len(coded_rows) if coded_rows is not None else None
        unavailable_reasons = ["unsupported_design_type"] if unsupported else []
        if family == "full_factorial" and unsupported:
            unavailable_reasons = ["full_factorial_run_count_exceeds_launch_limit"]
        status = "unsupported" if unsupported else "available"
        capabilities = _capabilities_for_family(family, status)
        diagnostics = _diagnostics_for_matrix(coded_rows or [], family=family, n_factors=n_factors)
        score = None if unsupported else _ranking_score(family, recommendation_mode, run_count, max_runs)
        warnings = (
            [
                _warning(
                    "unsupported_design_type",
                    f"{family} is represented as unavailable in the launch workbench MCP slice.",
                    "candidate_design.design_family",
                    {"design_family": family},
                )
            ]
            if unsupported
            else _candidate_warnings(
                family,
                max_runs=max_runs,
                run_count=run_count,
                strict_max_runs=strict_max_runs,
            )
        )
        if strict_max_runs and run_count and run_count > max_runs:
            status = "infeasible"
            score = None
            unavailable_reasons.append("run_count_exceeds_hard_budget")
        family_token = family.replace("_", "")
        candidate_design_id = f"candidate_{family_token}_{run_count or 'unavailable'}"
        design_id = None if unsupported else f"design_{family_token}_{run_count}_{_token({'set': candidate_set_id, 'family': family}, 6)}"
        raw_candidates.append(
            {
                "candidate_design_id": candidate_design_id,
                "design_id": design_id,
                "design_family": family,
                "status": status,
                "run_count": run_count,
                "ranking_score": score,
                "capabilities": capabilities,
                "diagnostics": diagnostics,
                "warnings": warnings,
                "coded_rows": coded_rows,
                "unavailable_reasons": unavailable_reasons,
            }
        )

    ranked = [candidate for candidate in raw_candidates if isinstance(candidate.get("ranking_score"), (int, float))]
    preferred = max(ranked, key=lambda candidate: float(candidate["ranking_score"]), default=None)
    preferred_id = preferred["candidate_design_id"] if preferred else None
    final_candidates: list[dict[str, Any]] = []
    artifact_paths = list(setup_paths)
    artifact_hashes = dict(setup_hashes)
    warnings: list[dict[str, Any]] = []

    for raw_candidate in raw_candidates:
        status = str(raw_candidate["status"])
        if raw_candidate["candidate_design_id"] == preferred_id:
            status = "recommended"
        elif status == "available" and raw_candidate["warnings"]:
            status = "available_with_warnings"
        elif status == "available" and float(raw_candidate.get("ranking_score") or 0) < 0.5:
            status = "not_recommended"
        metadata_path, metadata_hash, matrix_path = _write_design_artifacts(
            study_id=study_id,
            run_id=run_id,
            tool_name=tool_name,
            input_hash=input_hash,
            candidate_set_id=candidate_set_id,
            candidate_design_id=str(raw_candidate["candidate_design_id"]),
            design_id=raw_candidate["design_id"],
            family=str(raw_candidate["design_family"]),
            status=status,
            factors=factors,
            coded_rows=raw_candidate["coded_rows"],
            diagnostics=raw_candidate["diagnostics"],
            capabilities=raw_candidate["capabilities"],
            warnings=raw_candidate["warnings"],
            unavailable_reasons=raw_candidate["unavailable_reasons"],
        )
        artifact_paths.append(_relative_to_workspace(metadata_path))
        artifact_hashes[str(raw_candidate["candidate_design_id"])] = metadata_hash
        if matrix_path:
            artifact_paths.append(_relative_to_workspace(matrix_path))
        candidate = {
            "candidate_design_id": raw_candidate["candidate_design_id"],
            "design_id": raw_candidate["design_id"],
            "design_family": raw_candidate["design_family"],
            "status": status,
            "run_count": raw_candidate["run_count"],
            "recommendation_label": _candidate_label(str(raw_candidate["design_family"]), status, recommendation_mode),
            "ranking_score": raw_candidate["ranking_score"],
            "best_for": _candidate_best_for(str(raw_candidate["design_family"])),
            "capabilities": raw_candidate["capabilities"],
            "diagnostics": raw_candidate["diagnostics"],
            "tradeoffs": _candidate_tradeoffs(
                str(raw_candidate["design_family"]), max_runs, raw_candidate["run_count"]
            ),
            "unavailable_reasons": raw_candidate["unavailable_reasons"],
            "learnability": _learnability_for_candidate(
                family=str(raw_candidate["design_family"]),
                capabilities=raw_candidate["capabilities"],
                metadata_path=metadata_path,
            ),
            "source_artifacts": [_source_artifact_ref(metadata_path, "design_metadata", metadata_hash)],
            "warnings": raw_candidate["warnings"],
        }
        warnings.extend(raw_candidate["warnings"])
        final_candidates.append(candidate)

    candidate_set = {
        "candidate_set_id": candidate_set_id,
        "study_id": study_id,
        "source_snapshot_id": request.get("source_snapshot_id"),
        "recommendation_mode": recommendation_mode,
        "generated_at": _utc_now(),
        "generator_tool": tool_name,
        "input_hash": input_hash,
        "candidates": final_candidates,
        "ranking_summary": {
            "preferred_candidate_design_id": preferred_id,
            "ranking_basis": "Candidates ranked by the declared recommendation mode using MCP-derived capability and run-count diagnostics.",
            "weights": {
                "curvature_support": 0.3 if recommendation_mode == "fit_curvature" else 0.15,
                "model_rank": 0.25,
                "run_count_efficiency": 0.2,
                "execution_burden": 0.15,
            },
        },
        "warnings": warnings,
    }
    candidate_set_path = _study_dir(study_id) / "candidate_design_sets" / candidate_set_id / "candidate_design_set.json"
    _write_json(candidate_set_path, candidate_set)
    candidate_set_hash = _canonical_hash(candidate_set)
    artifact_paths.append(_relative_to_workspace(candidate_set_path))
    artifact_hashes["candidate_design_set"] = candidate_set_hash
    output_hash = _canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths})
    duration_ms = int((time.perf_counter() - started) * 1000)
    status = "success_with_warnings" if warnings else "success"
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status=status,
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=duration_ms,
        artifact_paths=artifact_paths,
        warnings=warnings,
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status=status,
        summary=f"Generated {len(final_candidates)} workbench candidate designs for {study_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        warnings=warnings,
        structured_content={
            "candidate_set_id": candidate_set_id,
            "preferred_candidate_design_id": preferred_id,
            "candidate_count": len(final_candidates),
        },
    )


@_register
def rank_candidate_designs(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic rankings for an existing candidate design set."""

    started = time.perf_counter()
    tool_name = "rank_candidate_designs"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    loaded = _load_candidate_set(study_id, request.get("candidate_set_id"))
    if loaded is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Candidate design set was not found.",
            errors=[
                _error(
                    "candidate_set_not_found",
                    "Generate candidate designs before ranking.",
                    "request.candidate_set_id",
                )
            ],
        )
    path, candidate_set = loaded
    rankings = sorted(
        [
            {
                "candidate_design_id": candidate["candidate_design_id"],
                "ranking_score": candidate["ranking_score"],
                "status": candidate["status"],
            }
            for candidate in candidate_set.get("candidates", [])
            if isinstance(candidate.get("ranking_score"), (int, float))
        ],
        key=lambda item: float(item["ranking_score"]),
        reverse=True,
    )
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    output_hash = _canonical_hash({"rankings": rankings})
    artifact_paths = [_relative_to_workspace(path)]
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Ranked {len(rankings)} candidate designs.",
        artifact_paths=artifact_paths,
        artifact_hashes={"candidate_design_set": _canonical_hash(candidate_set)},
        structured_content={"rankings": rankings},
    )


@_register
def compare_candidate_designs(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a side-by-side comparison artifact for candidate designs."""

    started = time.perf_counter()
    tool_name = "compare_candidate_designs"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    loaded = _load_candidate_set(study_id, request.get("candidate_set_id"))
    if loaded is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Candidate design set was not found.",
            errors=[_error("candidate_set_not_found", "Generate candidates before comparison.", "request.candidate_set_id")],
        )
    candidate_set_path, candidate_set = loaded
    requested_ids = request.get("selected_candidate_design_ids")
    all_ids = [candidate["candidate_design_id"] for candidate in candidate_set.get("candidates", [])]
    selected_ids = [item for item in requested_ids if item in all_ids] if isinstance(requested_ids, list) else all_ids
    if not selected_ids:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="No selected candidates were found in the candidate set.",
            errors=[
                _error(
                    "candidate_design_not_found",
                    "selected_candidate_design_ids must reference candidates in the candidate set.",
                    "request.selected_candidate_design_ids",
                )
            ],
        )
    preferred_id = candidate_set.get("ranking_summary", {}).get("preferred_candidate_design_id")
    if preferred_id not in selected_ids:
        preferred_id = selected_ids[0]
    comparison_id = str(
        request.get("comparison_id")
        or f"comparison_{candidate_set['candidate_set_id'].removeprefix('candidate_set_')}"
    )
    comparison = {
        "comparison_id": comparison_id,
        "candidate_set_id": candidate_set["candidate_set_id"],
        "selected_candidate_design_ids": selected_ids,
        "active_metrics": request.get("active_metrics")
        or [
            "run_count",
            "main_effects",
            "two_factor_interactions",
            "quadratic_terms",
            "condition_number",
            "pure_error_estimate",
        ],
        "preferred_candidate_design_id": preferred_id,
        "user_selected_candidate_design_id": request.get("user_selected_candidate_design_id") or preferred_id,
        "decision_notes": request.get("decision_notes")
        or "Comparison generated from persisted candidate design diagnostics.",
        "generated_at": _utc_now(),
    }
    comparison_path = _study_dir(study_id) / "comparisons" / comparison_id / "design_comparison.json"
    _write_json(comparison_path, comparison)
    comparison_hash = _canonical_hash(comparison)
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    artifact_paths = [_relative_to_workspace(candidate_set_path), _relative_to_workspace(comparison_path)]
    artifact_hashes = {"candidate_design_set": _canonical_hash(candidate_set), "design_comparison": comparison_hash}
    output_hash = _canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths})
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Compared {len(selected_ids)} candidate designs.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={"comparison_id": comparison_id, "preferred_candidate_design_id": preferred_id},
    )


@_register
def commit_run_plan(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Commit a selected candidate design to a stable run-plan artifact."""

    started = time.perf_counter()
    tool_name = "commit_run_plan"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    comparison_path = _comparison_path(study_id, request.get("comparison_id"))
    if comparison_path is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Design comparison was not found.",
            errors=[_error("comparison_not_found", "Compare candidates before committing a run plan.", "request.comparison_id")],
        )
    comparison = _read_json(comparison_path)
    loaded = _load_candidate_set(study_id, comparison["candidate_set_id"])
    if loaded is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Source candidate design set was not found.",
            errors=[_error("candidate_set_not_found", "The comparison source candidate set is missing.", "comparison.candidate_set_id")],
        )
    candidate_set_path, candidate_set = loaded
    selected_id = (
        request.get("candidate_design_id")
        or comparison.get("user_selected_candidate_design_id")
        or comparison.get("preferred_candidate_design_id")
    )
    candidate = _candidate_by_id(candidate_set, str(selected_id))
    if candidate is None or candidate.get("status") in {"unsupported", "infeasible", "failed_validation"}:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Selected candidate cannot be committed.",
            errors=[
                _error(
                    "candidate_not_committable",
                    "Only computed, feasible candidate designs can be committed.",
                    "request.candidate_design_id",
                    {"candidate_design_id": selected_id},
                )
            ],
        )
    metadata_ref = candidate["source_artifacts"][0]["path"]
    metadata_path = (_workspace_root() / metadata_ref).resolve()
    metadata = _read_json(metadata_path)
    source_matrix_ref = metadata.get("matrix_path")
    if not isinstance(source_matrix_ref, str):
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Source candidate design matrix is unavailable.",
            errors=[_error("design_matrix_not_found", "The selected candidate has no matrix artifact.", "candidate.source_artifacts")],
        )
    source_matrix_path = (_workspace_root() / source_matrix_ref).resolve()
    run_plan_id = str(request.get("run_plan_id") or f"run_plan_{_token({'comparison': comparison['comparison_id'], 'candidate': selected_id})}")
    run_plan_dir = _study_dir(study_id) / "run_plans" / run_plan_id
    run_matrix_path = run_plan_dir / "run_matrix.csv"
    protocol_notes_path = run_plan_dir / "protocol_notes.md"
    run_plan_dir.mkdir(parents=True, exist_ok=True)
    run_matrix_path.write_text(source_matrix_path.read_text(encoding="utf-8"), encoding="utf-8")
    protocol_notes = "\n".join(
        [
            f"# Run Plan {run_plan_id}",
            "",
            f"- Source candidate: {candidate['candidate_design_id']}",
            f"- Source comparison: {comparison['comparison_id']}",
            f"- Design family: {candidate['design_family']}",
            f"- Run count: {candidate['run_count']}",
            "- Status: planned, not experimentally verified.",
            "",
            "## Source refs",
            f"- {_relative_to_workspace(candidate_set_path)}",
            f"- {_relative_to_workspace(comparison_path)}",
            f"- {metadata_ref}",
        ]
    )
    protocol_notes_path.write_text(protocol_notes + "\n", encoding="utf-8")
    run_plan = {
        "run_plan_id": run_plan_id,
        "source_candidate_design_id": candidate["candidate_design_id"],
        "source_comparison_id": comparison["comparison_id"],
        "committed_at": _utc_now(),
        "run_count": int(candidate["run_count"]),
        "run_matrix_path": _relative_to_workspace(run_matrix_path),
        "protocol_notes_path": _relative_to_workspace(protocol_notes_path),
        "source_artifacts": [
            _relative_to_workspace(candidate_set_path),
            _relative_to_workspace(comparison_path),
            metadata_ref,
        ],
    }
    run_plan_path = run_plan_dir / "run_plan.json"
    _write_json(run_plan_path, run_plan)
    run_plan_hash = _canonical_hash(run_plan)
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    artifact_paths = [
        _relative_to_workspace(run_plan_path),
        _relative_to_workspace(run_matrix_path),
        _relative_to_workspace(protocol_notes_path),
    ]
    artifact_hashes = {
        "run_plan": run_plan_hash,
        "run_matrix": _file_hash(run_matrix_path),
        "protocol_notes": _file_hash(protocol_notes_path),
    }
    output_hash = _canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths})
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Committed {candidate['candidate_design_id']} to run plan {run_plan_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={"run_plan_id": run_plan_id, "source_candidate_design_id": candidate["candidate_design_id"]},
    )


@_register
def create_study_snapshot(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a compact study-state snapshot for workbench versioning."""

    started = time.perf_counter()
    tool_name = "create_study_snapshot"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    candidate_path = _candidate_set_path(study_id, request.get("candidate_set_id"))
    comparison_path = _comparison_path(study_id, request.get("comparison_id"))
    run_plan_path = _run_plan_path(study_id, request.get("run_plan_id"))
    setup_parts: dict[str, Any] = {}
    for filename in ("study.json", "factor_space.json", "responses.json"):
        path = _study_dir(study_id) / filename
        if path.exists():
            setup_parts[filename] = _read_json(path)
    setup_hash = _canonical_hash(setup_parts)
    state_parts = {
        "setup": setup_parts,
        "candidate_set": _read_json(candidate_path) if candidate_path else None,
        "comparison": _read_json(comparison_path) if comparison_path else None,
        "run_plan": _read_json(run_plan_path) if run_plan_path else None,
    }
    snapshot_id = str(
        request.get("snapshot_id")
        or f"snapshot_{_token({'study_id': study_id, 'state': state_parts, 'label': request.get('label'), 'notes': request.get('notes')})}"
    )
    snapshot = {
        "snapshot_id": snapshot_id,
        "label": str(request.get("label") or f"Snapshot {snapshot_id.removeprefix('snapshot_')}"),
        "created_at": _utc_now(),
        "study_state_hash": _canonical_hash(state_parts),
        "setup_hash": setup_hash,
        "active_candidate_set_id": _read_json(candidate_path)["candidate_set_id"] if candidate_path else None,
        "active_comparison_id": _read_json(comparison_path)["comparison_id"] if comparison_path else None,
        "committed_run_plan_id": _read_json(run_plan_path)["run_plan_id"] if run_plan_path else None,
        "notes": request.get("notes"),
    }
    snapshot_path = _study_dir(study_id) / "snapshots" / snapshot_id / "snapshot.json"
    _write_json(snapshot_path, snapshot)
    snapshot_hash = _canonical_hash(snapshot)
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    artifact_paths = [_relative_to_workspace(snapshot_path)]
    artifact_hashes = {"study_snapshot": snapshot_hash}
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=_canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths}),
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Created snapshot {snapshot_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={"snapshot_id": snapshot_id},
    )


@_register
def diff_study_snapshots(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a structured diff between two study snapshots."""

    started = time.perf_counter()
    tool_name = "diff_study_snapshots"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    base_id = request.get("base_snapshot_id")
    compare_id = request.get("compare_snapshot_id")
    if not isinstance(base_id, str) or not isinstance(compare_id, str):
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Both base_snapshot_id and compare_snapshot_id are required.",
            errors=[
                _error("missing_required_columns", "base_snapshot_id is required.", "request.base_snapshot_id"),
                _error("missing_required_columns", "compare_snapshot_id is required.", "request.compare_snapshot_id"),
            ],
        )
    base_path = _snapshot_path(study_id, base_id)
    compare_path = _snapshot_path(study_id, compare_id)
    if base_path is None or compare_path is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="One or both snapshots were not found.",
            errors=[_error("snapshot_not_found", "Snapshot artifacts must exist before diffing.", "request")],
        )
    base = _read_json(base_path)
    compare = _read_json(compare_path)
    fields = [
        "study_state_hash",
        "setup_hash",
        "active_candidate_set_id",
        "active_comparison_id",
        "committed_run_plan_id",
    ]
    changes = [
        {"field": field, "before": base.get(field), "after": compare.get(field)}
        for field in fields
        if base.get(field) != compare.get(field)
    ]
    diff_id = str(request.get("diff_id") or f"snapshot_diff_{_token({'base': base, 'compare': compare})}")
    diff = {
        "diff_id": diff_id,
        "study_id": study_id,
        "base_snapshot_id": base_id,
        "compare_snapshot_id": compare_id,
        "generated_at": _utc_now(),
        "changes": changes,
        "source_refs": [_relative_to_workspace(base_path), _relative_to_workspace(compare_path)],
    }
    diff_path = _study_dir(study_id) / "snapshots" / diff_id / "snapshot_diff.json"
    _write_json(diff_path, diff)
    diff_hash = _canonical_hash(diff)
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    artifact_paths = [_relative_to_workspace(diff_path)]
    artifact_hashes = {"snapshot_diff": diff_hash}
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=_canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths}),
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Diffed snapshots {base_id} and {compare_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={"diff_id": diff_id, "change_count": len(changes)},
    )


def _panel_for_candidate(
    *,
    candidate: dict[str, Any],
    candidate_set_path: Path,
    comparison_path: Path | None = None,
) -> dict[str, Any]:
    source_refs = [candidate["candidate_design_id"], _relative_to_workspace(candidate_set_path)]
    if comparison_path:
        source_refs.append(_relative_to_workspace(comparison_path))
    for artifact in candidate.get("source_artifacts", []):
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
            source_refs.append(f"{artifact['path']}#diagnostics")
    run_count = candidate.get("run_count")
    family = str(candidate.get("design_family", "candidate")).replace("_", " ")
    if candidate.get("status") == "unsupported":
        summary = (
            f"{family} is recorded as unsupported by the launch MCP implementation. "
            "The workbench can display the unavailable state, but it must not present this candidate as successful."
        )
    else:
        summary = (
            f"{family} is explained from persisted candidate diagnostics. "
            f"The run count shown here is {run_count}, sourced from the candidate design artifact."
        )
    return {
        "panel_id": f"ai_panel_{_slug(str(candidate['candidate_design_id']).removeprefix('candidate_'), fallback='candidate')}",
        "object_type": "candidate_design",
        "object_id": candidate["candidate_design_id"],
        "title": "Why this design?",
        "summary": summary,
        "best_for": list(candidate.get("best_for", [])),
        "tradeoffs": list(candidate.get("tradeoffs", [])),
        "watch_out_for": [
            warning.get("message", warning.get("code", "Review warning."))
            for warning in candidate.get("warnings", [])
        ]
        or ["Do not treat planned or model-based recommendations as verified experimental results."],
        "source_refs": source_refs,
    }


@_register
def explain_study_object(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a source-cited contextual AI panel from persisted workbench artifacts."""

    started = time.perf_counter()
    tool_name = "explain_study_object"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    loaded = _load_candidate_set(study_id, request.get("candidate_set_id"))
    if loaded is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Candidate design set was not found.",
            errors=[_error("candidate_set_not_found", "Generate candidate designs before explanation.", "request.candidate_set_id")],
        )
    candidate_set_path, candidate_set = loaded
    comparison_path = _comparison_path(study_id, request.get("comparison_id"))
    object_id = request.get("object_id") or candidate_set.get("ranking_summary", {}).get("preferred_candidate_design_id")
    candidate = _candidate_by_id(candidate_set, str(object_id))
    if candidate is None:
        return _envelope(
            study_id=study_id,
            run_id=run_id,
            status="failed_validation",
            summary="Requested study object was not found.",
            errors=[_error("study_object_not_found", "object_id must reference a candidate design.", "request.object_id")],
        )
    panel = _panel_for_candidate(candidate=candidate, candidate_set_path=candidate_set_path, comparison_path=comparison_path)
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    output_hash = _canonical_hash(panel)
    artifact_paths = [_relative_to_workspace(candidate_set_path)]
    if comparison_path:
        artifact_paths.append(_relative_to_workspace(comparison_path))
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Generated source-cited explanation panel for {candidate['candidate_design_id']}.",
        artifact_paths=artifact_paths,
        artifact_hashes={"contextual_ai_panel": output_hash},
        structured_content={"contextual_ai_panel": panel},
    )


def _study_summary_for_payload(study_id: str) -> dict[str, Any]:
    study_document = _load_study_document(study_id)
    study = study_document.get("study", {}) if study_document else {}
    return {
        "study_id": study_id,
        "title": str(study.get("title") or study_id.replace("_", " ").title()),
        "domain_template": str(study.get("domain_template") or DEFAULT_DOMAIN_TEMPLATE),
        "status": str(study.get("status") or "active"),
        "active_design_id": study.get("active_design_id"),
        "active_fit_id": study.get("active_fit_id"),
        "active_construct_id": study.get("active_construct_id"),
    }


def _factor_space_for_payload(study_id: str) -> dict[str, Any] | None:
    path = _study_dir(study_id) / "factor_space.json"
    if not path.exists():
        return None
    return _read_json(path).get("factor_space")


def _responses_for_payload(study_id: str) -> list[dict[str, Any]]:
    path = _study_dir(study_id) / "responses.json"
    if not path.exists():
        return []
    return list(_read_json(path).get("responses", []))


def _dashboard_app_dir() -> Path:
    return (REPO_ROOT / "apps" / "dashboard").resolve()


def _dashboard_payload_path(study_id: str) -> Path:
    return _study_dir(study_id) / "dashboard_payload.json"


def _dashboard_http_host(host: str) -> str:
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def _validated_dashboard_host(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    host = value.strip().lower()
    return host if host in {"127.0.0.1", "localhost", "::1"} else None


def _validated_dashboard_port(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if not isinstance(value, int):
        return None
    return value if 1 <= value <= 65535 else None


def _dashboard_payload_fetch_path(payload_path: Path) -> str:
    return f"/@fs/{payload_path.resolve().as_posix()}"


def _dashboard_route(study_id: str, value: Any) -> str:
    default = f"/studies/{study_id}"
    if not isinstance(value, str):
        return default
    route = value.strip()
    if not route.startswith("/") or "://" in route or "?" in route or "#" in route or ".." in route:
        return default
    return route


def _dashboard_preview_url(route: str, host: str, port: int, payload_path: Path) -> str:
    query = urllib.parse.urlencode({"payloadUrl": _dashboard_payload_fetch_path(payload_path)})
    return f"http://{_dashboard_http_host(host)}:{port}{route}?{query}"


def _dashboard_static_file_url(study_id: str, payload_path: Path, index_path: Path) -> str:
    query = urllib.parse.urlencode({"payloadUrl": payload_path.resolve().as_uri(), "studyId": study_id})
    return f"{index_path.resolve().as_uri()}?{query}"


def _probe_dashboard_server(host: str, port: int) -> bool:
    url = f"http://{_dashboard_http_host(host)}:{port}/"
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return response.status < 500
    except (OSError, urllib.error.URLError):
        return False


def _start_dashboard_dev_server(host: str, port: int, timeout_sec: float) -> tuple[str, int | None, str | None]:
    app_dir = _dashboard_app_dir()
    package_runner = shutil.which("pnpm")
    command_prefix = [package_runner, "dev"] if package_runner else None
    if command_prefix is None:
        package_runner = shutil.which("npm")
        command_prefix = [package_runner, "run", "dev"] if package_runner else None
    if command_prefix is None:
        return "failed", None, "Neither pnpm nor npm was found on PATH."

    stdout_path = app_dir / "vite.stdout.log"
    stderr_path = app_dir / "vite.stderr.log"
    command = [
        *command_prefix,
        "--",
        "--host",
        host,
        "--port",
        str(port),
        "--strictPort",
    ]
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(
            command,
            cwd=app_dir,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
        )

    deadline = time.perf_counter() + timeout_sec
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            return "failed", process.pid, f"dashboard dev server exited with code {process.returncode}."
        if _probe_dashboard_server(host, port):
            return "started", process.pid, None
        time.sleep(0.25)

    process.terminate()
    return "failed", process.pid, f"dashboard dev server did not respond within {timeout_sec:g} seconds."


@_register
def generate_dashboard_payload(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a dashboard payload with an optional MCP-backed workbench section."""

    started = time.perf_counter()
    tool_name = "generate_dashboard_payload"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    candidate_loaded = _load_candidate_set(study_id, request.get("candidate_set_id"))
    comparison_path = _comparison_path(study_id, request.get("comparison_id"))
    comparison = _read_json(comparison_path) if comparison_path else None
    run_plan_path = _run_plan_path(study_id, request.get("run_plan_id"))
    run_plan = _read_json(run_plan_path) if run_plan_path else None
    snapshots_dir = _study_dir(study_id) / "snapshots"
    snapshots = []
    if snapshots_dir.exists():
        snapshots = [
            _read_json(path / "snapshot.json")
            for path in snapshots_dir.iterdir()
            if path.is_dir() and (path / "snapshot.json").exists()
        ]
        snapshots.sort(key=lambda snapshot: snapshot["created_at"])

    candidate_set_path: Path | None = None
    candidate_set: dict[str, Any] | None = None
    contextual_panels: list[dict[str, Any]] = []
    if candidate_loaded:
        candidate_set_path, candidate_set = candidate_loaded
        preferred_id = (
            comparison.get("preferred_candidate_design_id") if comparison else None
        ) or candidate_set.get("ranking_summary", {}).get("preferred_candidate_design_id")
        preferred = _candidate_by_id(candidate_set, str(preferred_id)) or (
            candidate_set.get("candidates", [None])[0] if candidate_set.get("candidates") else None
        )
        if isinstance(preferred, dict):
            contextual_panels.append(
                _panel_for_candidate(
                    candidate=preferred,
                    candidate_set_path=candidate_set_path,
                    comparison_path=comparison_path,
                )
            )

    source_artifacts: list[dict[str, str]] = []
    if candidate_set_path and candidate_set:
        source_artifacts.append(_source_artifact_ref(candidate_set_path, "candidate_design_set", _canonical_hash(candidate_set)))
    if comparison_path and comparison:
        source_artifacts.append(_source_artifact_ref(comparison_path, "design_comparison", _canonical_hash(comparison)))
    if run_plan_path and run_plan:
        source_artifacts.append(_source_artifact_ref(run_plan_path, "run_plan", _canonical_hash(run_plan)))
    for snapshot in snapshots:
        snapshot_path = _snapshot_path(study_id, snapshot["snapshot_id"])
        if snapshot_path:
            source_artifacts.append(_source_artifact_ref(snapshot_path, "study_snapshot", _canonical_hash(snapshot)))

    workbench = {
        "mode": "run_plan" if run_plan else "candidate_comparison",
        "study_stage": "run_plan_committed" if run_plan else ("candidates_compared" if comparison else "candidates_generated"),
        "recommendation_mode": (
            candidate_set.get("recommendation_mode") if candidate_set else request.get("recommendation_mode")
        )
        or "fit_curvature",
        "candidate_design_sets": [candidate_set] if candidate_set else [],
        "active_comparison": comparison,
        "committed_run_plan": run_plan,
        "snapshots": snapshots,
        "stale_state": {"is_stale": False, "stale_due_to": [], "affected_objects": []},
        "contextual_ai_panels": contextual_panels,
    }
    workbench_available = bool(candidate_set)
    source_paths = [artifact["path"] for artifact in source_artifacts]
    sections = {
        "workbench": _availability(
            "available" if workbench_available else "unavailable_not_run",
            None if workbench_available else "Candidate designs have not been generated.",
            [] if workbench_available else ["generate_candidate_designs"],
            source_paths,
        ),
        "experiment_matrix": _availability(
            "available" if run_plan else "unavailable_not_run",
            None if run_plan else "No candidate design has been committed into a run plan.",
            [] if run_plan else ["commit_run_plan"],
            [run_plan["run_matrix_path"]] if run_plan else [],
        ),
        "endpoint_results": _availability(
            "unavailable_not_run",
            "Observed endpoint data has not been imported.",
            ["import_endpoint_observations"],
            [],
        ),
        "time_courses": _availability(
            "unavailable_missing_input",
            "Time-resolved observations were not supplied.",
            ["time_resolved_observations"],
            [],
        ),
        "effects": _availability("unavailable_not_run", "No model fit exists.", ["fit_response_surface"], []),
        "relative_yield": _availability(
            "unavailable_missing_input",
            "Construct sequence or nucleotide composition was not supplied.",
            ["construct_sequence_or_composition"],
            [],
        ),
        "economics": _availability(
            "unavailable_missing_input",
            "Direct component costs were not supplied.",
            ["component_costs"],
            [],
        ),
        "recommendations": _availability(
            "available" if candidate_set else "unavailable_not_run",
            None if candidate_set else "Candidate ranking has not been generated.",
            [] if candidate_set else ["generate_candidate_designs"],
            source_paths,
        ),
        "verification": _availability(
            "unavailable_not_run",
            "Verification planning begins after observed results or explicit verification inputs exist.",
            ["plan_verification_runs"],
            [],
        ),
        "diagnostics": _availability(
            "available" if candidate_set else "unavailable_not_run",
            None if candidate_set else "No diagnostics are available.",
            [] if candidate_set else ["generate_candidate_designs"],
            source_paths,
        ),
    }
    now = _utc_now()
    payload = {
        "version": SCHEMA_VERSION,
        "payload_metadata": {
            "payload_id": f"payload_{study_id}_{_token({'run_id': run_id, 'workbench': workbench}, 8)}",
            "study_id": study_id,
            "run_id": run_id,
            "generated_at": now,
            "schema_version": SCHEMA_VERSION,
            "payload_hash": "sha256:" + ("0" * 64),
            "source_artifacts": source_artifacts,
        },
        "study": _study_summary_for_payload(study_id),
        "factor_space": _factor_space_for_payload(study_id),
        "responses": _responses_for_payload(study_id),
        "constructs": [],
        "designs": [],
        "observations": {},
        "models": [],
        "derived": {},
        "dashboard_state": {"active_workbench_view": workbench["mode"]},
        "sections": sections,
        "warnings": candidate_set.get("warnings", []) if candidate_set else [],
        "audit": {
            "generated_by": tool_name,
            "generated_at": now,
            "method_versions": {
                "generate_candidate_designs": METHOD_VERSION,
                "compare_candidate_designs": METHOD_VERSION,
                "commit_run_plan": METHOD_VERSION,
            },
        },
        "workbench": workbench,
    }
    payload["payload_metadata"]["payload_hash"] = _canonical_hash(payload)
    payload_path = _study_dir(study_id) / "dashboard_payload.json"
    _write_json(payload_path, payload)
    payload_hash = payload["payload_metadata"]["payload_hash"]
    artifact_paths = [_relative_to_workspace(payload_path)]
    artifact_hashes = {"dashboard_payload": payload_hash}
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )
    _append_audit(
        study_id=study_id,
        run_id=run_id,
        tool_name=tool_name,
        status="success",
        input_hash=input_hash,
        output_hash=_canonical_hash({"artifact_hashes": artifact_hashes, "artifact_paths": artifact_paths}),
        duration_ms=int((time.perf_counter() - started) * 1000),
        artifact_paths=artifact_paths,
        warnings=[],
        errors=[],
        seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
    )
    return _envelope(
        study_id=study_id,
        run_id=run_id,
        status="success",
        summary=f"Generated dashboard/workbench payload for {study_id}.",
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        structured_content={"payload_path": artifact_paths[0], "workbench_available": workbench_available},
    )


@_register
def launch_dashboard_preview(
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or start a local dashboard preview for a generated study payload."""

    started = time.perf_counter()
    tool_name = "launch_dashboard_preview"
    request = request or {}
    options = options or {}
    run_id = run_id or _run_id()
    invalid = _invalid_study_envelope(study_id, run_id)
    if invalid:
        return invalid
    assert study_id is not None
    input_hash = _canonical_hash(
        {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
    )

    def finish(
        *,
        status: str,
        summary: str,
        structured_content: dict[str, Any],
        warnings: list[dict[str, Any]] | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        envelope = _envelope(
            study_id=study_id,
            run_id=run_id,
            status=status,
            summary=summary,
            warnings=warnings or [],
            errors=errors or [],
            structured_content=structured_content,
        )
        _append_audit(
            study_id=study_id,
            run_id=run_id,
            tool_name=tool_name,
            status=status,
            input_hash=input_hash,
            output_hash=_canonical_hash(envelope),
            duration_ms=int((time.perf_counter() - started) * 1000),
            artifact_paths=[],
            warnings=warnings or [],
            errors=errors or [],
            seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
        )
        return envelope

    payload_path = _dashboard_payload_path(study_id)
    payload_rel = _relative_to_workspace(payload_path)
    base_structured = {
        "payload_path": payload_rel,
        "server_status": "failed",
        "url": None,
    }
    if not payload_path.exists():
        error = _error(
            "dashboard_payload_not_found",
            "dashboard_payload.json must exist before launching the dashboard preview.",
            "study_id",
            {"payload_path": payload_rel},
        )
        return finish(
            status="failed_validation",
            summary=f"Dashboard payload was not found for {study_id}.",
            structured_content={
                **base_structured,
                "instructions": "Run generate_dashboard_payload before launching the dashboard preview.",
            },
            errors=[error],
        )

    host = _validated_dashboard_host(request.get("host", "127.0.0.1"))
    if host is None:
        error = _error(
            "invalid_host",
            "Dashboard preview host must be localhost, 127.0.0.1, or ::1.",
            "request.host",
            {"host": request.get("host")},
        )
        return finish(
            status="failed_validation",
            summary="Dashboard preview host failed validation.",
            structured_content=base_structured,
            errors=[error],
        )

    port = _validated_dashboard_port(request.get("port", 5173))
    if port is None:
        error = _error(
            "invalid_port",
            "Dashboard preview port must be an integer from 1 to 65535.",
            "request.port",
            {"port": request.get("port")},
        )
        return finish(
            status="failed_validation",
            summary="Dashboard preview port failed validation.",
            structured_content=base_structured,
            errors=[error],
        )

    mode = request.get("mode", "return_url_only")
    allowed_modes = {"return_url_only", "check_existing_server", "start_dev_server", "static_file"}
    if not isinstance(mode, str) or mode not in allowed_modes:
        error = _error(
            "invalid_mode",
            "Dashboard preview mode must be return_url_only, check_existing_server, start_dev_server, or static_file.",
            "request.mode",
            {"mode": mode},
        )
        return finish(
            status="failed_validation",
            summary="Dashboard preview mode failed validation.",
            structured_content=base_structured,
            errors=[error],
        )

    app_dir = _dashboard_app_dir()
    if not (app_dir / "package.json").exists():
        error = _error(
            "dashboard_app_not_found",
            "Dashboard app package.json was not found.",
            "apps/dashboard",
            {"dashboard_app_dir": str(app_dir)},
        )
        return finish(
            status="failed_runtime",
            summary="Dashboard app was not found.",
            structured_content=base_structured,
            errors=[error],
        )

    route = _dashboard_route(study_id, request.get("route"))
    url = _dashboard_preview_url(route, host, port, payload_path)
    payload_url = _dashboard_payload_fetch_path(payload_path)
    structured_content: dict[str, Any] = {
        "url": url,
        "server_status": "not_started",
        "payload_path": payload_rel,
        "payload_url": payload_url,
        "instructions": "Open the URL after the dashboard dev server is running.",
    }

    if mode == "static_file":
        index_path = app_dir / "dist" / "index.html"
        if not index_path.exists():
            error = _error(
                "dashboard_app_not_found",
                "Dashboard static build was not found. Run the dashboard build before static_file mode.",
                "apps/dashboard/dist/index.html",
                {"dashboard_app_dir": str(app_dir)},
            )
            return finish(
                status="failed_runtime",
                summary="Dashboard static build was not found.",
                structured_content=structured_content,
                errors=[error],
            )
        structured_content["url"] = _dashboard_static_file_url(study_id, payload_path, index_path)
        structured_content["server_status"] = "static_file_ready"
        structured_content["instructions"] = "Open the static dashboard file URL."
        return finish(
            status="success",
            summary=f"Dashboard static preview URL is {structured_content['url']}.",
            structured_content=structured_content,
        )

    if _probe_dashboard_server(host, port):
        structured_content["server_status"] = "already_running"
        structured_content["instructions"] = "Open the returned dashboard preview URL."
        return finish(
            status="success",
            summary=f"Dashboard preview URL is {url}.",
            structured_content=structured_content,
        )

    if mode in {"return_url_only", "check_existing_server"}:
        return finish(
            status="success",
            summary=f"Dashboard preview URL is {url}.",
            structured_content=structured_content,
        )

    timeout_raw = request.get("startup_timeout_sec", 10)
    timeout_sec = float(timeout_raw) if isinstance(timeout_raw, (int, float)) and timeout_raw > 0 else 10.0
    server_status, pid, error_message = _start_dashboard_dev_server(host, port, timeout_sec)
    structured_content["server_status"] = server_status
    if pid is not None:
        structured_content["pid"] = pid
    if error_message is not None:
        error = _error(
            "dev_server_start_failed",
            error_message,
            "request.mode",
            {"mode": mode, "host": host, "port": port},
        )
        return finish(
            status="failed_runtime",
            summary="Dashboard dev server failed to start.",
            structured_content=structured_content,
            errors=[error],
        )

    structured_content["instructions"] = "Open the returned dashboard preview URL."
    return finish(
        status="success",
        summary=f"Dashboard preview URL is {url}.",
        structured_content=structured_content,
    )


def _placeholder_tool(
    tool_name: str,
    study_id: str | None = None,
    run_id: str | None = None,
    request: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    run_id = run_id or _run_id()
    request = request or {}
    options = options or {}
    warning = _warning(
        "payload_section_unavailable",
        f"{tool_name} is registered for Gate 0 but its scientific implementation starts after Gate 0.",
        "tool",
        {"gate": "Gate 0"},
    )
    envelope = _envelope(
        study_id=study_id,
        run_id=run_id,
        status="skipped",
        summary=f"{tool_name} is registered as a Gate 0 placeholder.",
        warnings=[warning],
        structured_content={"registered": True, "gate": "Gate 0"},
    )
    if study_id and ID_RE.match(study_id):
        input_hash = _canonical_hash(
            {"study_id": study_id, "run_id": run_id, "request": request, "options": options}
        )
        _append_audit(
            study_id=study_id,
            run_id=run_id,
            tool_name=tool_name,
            status="skipped",
            input_hash=input_hash,
            output_hash=_canonical_hash(envelope),
            duration_ms=int((time.perf_counter() - started) * 1000),
            artifact_paths=[],
            warnings=[warning],
            errors=[],
            seed=options.get("seed") if isinstance(options.get("seed"), int) else None,
        )
    return envelope


def _make_placeholder(name: str) -> None:
    def tool(
        study_id: str | None = None,
        run_id: str | None = None,
        request: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return _placeholder_tool(name, study_id=study_id, run_id=run_id, request=request, options=options)

    tool.__name__ = name
    tool.__doc__ = f"Gate 0 placeholder for {name}."
    globals()[name] = _register(tool)


for _tool_name in LAUNCH_TOOL_NAMES:
    if _tool_name not in globals():
        _make_placeholder(_tool_name)


def registered_launch_tools() -> list[str]:
    return list(LAUNCH_TOOL_NAMES)


def registered_workbench_tools() -> list[str]:
    return list(WORKBENCH_TOOL_NAMES)


def dependency_versions() -> dict[str, str]:
    distributions = {
        "mcp": "mcp",
        "pydantic": "pydantic",
        "jsonschema": "jsonschema",
        "numpy": "numpy",
        "scipy": "scipy",
        "pandas": "pandas",
        "statsmodels": "statsmodels",
        "scikit-learn": "scikit-learn",
        "pytest": "pytest",
    }
    versions: dict[str, str] = {}
    for name, distribution in distributions.items():
        versions[name] = importlib.metadata.version(distribution)
    return versions


def _smoke_create_study() -> dict[str, Any]:
    return create_or_update_study(
        study_id="gate0_smoke_study",
        request={"title": "Gate 0 Smoke Study", "domain_template": "ivt_qbd"},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DOE Scientific Toolchain MCP server")
    parser.add_argument("--list-tools", action="store_true", help="Print registered launch tools as JSON.")
    parser.add_argument(
        "--startup-check",
        action="store_true",
        help="Verify the MCP server object can be constructed without entering the stdio loop.",
    )
    parser.add_argument("--versions", action="store_true", help="Print backend dependency versions as JSON.")
    parser.add_argument(
        "--smoke-create-study",
        action="store_true",
        help="Call create_or_update_study once and print the output envelope.",
    )
    args = parser.parse_args(argv)

    if args.list_tools:
        print(
            json.dumps(
                {
                    "server": SERVER_NAME,
                    "launch_tools": registered_launch_tools(),
                    "workbench_tools": registered_workbench_tools(),
                },
                indent=2,
            )
        )
        return 0
    if args.startup_check:
        if mcp is None:
            raise RuntimeError("The mcp package is not installed. Run uv --directory mcp-server sync --dev.")
        print(json.dumps({"server": SERVER_NAME, "status": "startup_ready"}, indent=2))
        return 0
    if args.versions:
        print(json.dumps({"doe_toolchain": __version__, "dependencies": dependency_versions()}, indent=2))
        return 0
    if args.smoke_create_study:
        print(json.dumps(_smoke_create_study(), indent=2, sort_keys=True))
        return 0
    if mcp is None:
        raise RuntimeError("The mcp package is not installed. Run uv --directory mcp-server sync --dev.")
    mcp.run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
