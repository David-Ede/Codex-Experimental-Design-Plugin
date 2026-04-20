"""Gate 0 MCP server skeleton for the DOE Scientific Toolchain."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from doe_toolchain import LAUNCH_TOOL_NAMES, __version__

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
    if _tool_name != "create_or_update_study":
        _make_placeholder(_tool_name)


def registered_launch_tools() -> list[str]:
    return list(LAUNCH_TOOL_NAMES)


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
        print(json.dumps({"server": SERVER_NAME, "launch_tools": registered_launch_tools()}, indent=2))
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
