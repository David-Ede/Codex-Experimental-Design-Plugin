from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from doe_toolchain.server import (
    commit_run_plan,
    compare_candidate_designs,
    create_candidate_run_plan,
    create_or_update_study,
    create_study_snapshot,
    diff_study_snapshots,
    explain_study_object,
    generate_candidate_designs,
    generate_dashboard_payload,
)
from scripts.validate_schemas import _schema_store, _validator


@pytest.fixture()
def workspace_root(monkeypatch: pytest.MonkeyPatch) -> Path:
    root = Path(__file__).resolve().parents[2] / ".tmp_pytest_workbench" / uuid.uuid4().hex
    root.mkdir(parents=True)
    monkeypatch.setenv("DOE_TOOLCHAIN_WORKSPACE_ROOT", str(root))
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _workbench_request(candidate_families: list[str] | None = None) -> dict[str, Any]:
    return {
        "recommendation_mode": "fit_curvature",
        "max_runs": 20,
        "factors": [
            {"name": "mg_ntp_ratio", "display_name": "Mg:NTP ratio", "units": "ratio", "low": 0.8, "high": 1.6},
            {"name": "ntp_concentration", "display_name": "NTP concentration", "units": "mM", "low": 6, "high": 12},
            {"name": "dna_template", "display_name": "DNA template", "units": "ng/uL", "low": 10, "high": 100},
            {"name": "t7_rnap", "display_name": "T7 RNAP", "units": "U/uL", "low": 2, "high": 15},
        ],
        "responses": [
            {"name": "mrna_yield", "display_name": "mRNA yield", "units": "g/L", "goal": "maximize"},
            {"name": "dsrna_score", "display_name": "dsRNA score", "units": "score", "goal": "upper_threshold"},
        ],
        **({"candidate_families": candidate_families} if candidate_families is not None else {}),
    }


def _assert_valid(document: dict[str, Any], schema_name: str, store: dict[str, Any]) -> None:
    validator: Draft202012Validator = _validator(schema_name, store)
    errors = list(validator.iter_errors(document))
    assert errors == []


def test_create_candidate_run_plan_one_call_persists_committed_artifacts(workspace_root: Path) -> None:
    study_id = "workbench_one_call"
    store = _schema_store()

    envelope = create_candidate_run_plan(
        study_id=study_id,
        run_id="run_20260421_workbench_one_call",
        request={
            "title": "Workbench One Call",
            "domain_template": "ivt_qbd",
            "run_plan_id": "run_plan_one_call",
            **_workbench_request(),
        },
    )

    assert envelope["status"] == "success_with_warnings"
    structured = envelope["structured_content"]
    assert structured["candidate_set_id"]
    assert structured["comparison_id"]
    assert structured["run_plan_id"] == "run_plan_one_call"
    assert structured["dashboard_payload_path"] == f"outputs/studies/{study_id}/dashboard_payload.json"
    assert [step["tool_name"] for step in structured["steps"]] == [
        "create_or_update_study",
        "generate_candidate_designs",
        "compare_candidate_designs",
        "commit_run_plan",
        "generate_dashboard_payload",
    ]

    run_plan_path = workspace_root / "outputs" / "studies" / study_id / "run_plans" / "run_plan_one_call" / "run_plan.json"
    payload_path = workspace_root / "outputs" / "studies" / study_id / "dashboard_payload.json"
    _assert_valid(json.loads(run_plan_path.read_text(encoding="utf-8")), "run_plan_commit.schema.json", store)
    _assert_valid(json.loads(payload_path.read_text(encoding="utf-8")), "dashboard_payload.schema.json", store)

    audit_log = (workspace_root / "outputs" / "studies" / study_id / "audit_log.jsonl").read_text(encoding="utf-8")
    assert '"tool_name": "create_candidate_run_plan"' in audit_log
    assert '"tool_name": "rank_candidate_designs"' not in audit_log
    assert '"tool_name": "launch_dashboard_preview"' not in audit_log


def test_workbench_artifact_flow_persists_schema_valid_artifacts(workspace_root: Path) -> None:
    study_id = "workbench_flow"
    store = _schema_store()

    create_envelope = create_or_update_study(
        study_id=study_id,
        run_id="run_20260421_workbench_create",
        request={"title": "Workbench Flow", "domain_template": "ivt_qbd"},
    )
    assert create_envelope["status"] == "success"

    candidate_envelope = generate_candidate_designs(
        study_id=study_id,
        run_id="run_20260421_workbench_candidates",
        request=_workbench_request(),
    )
    assert candidate_envelope["status"] == "success_with_warnings"
    candidate_set_path = workspace_root / candidate_envelope["artifact_paths"][-1]
    candidate_set = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    _assert_valid(candidate_set, "candidate_design_set.schema.json", store)
    assert len(candidate_set["candidates"]) == 3
    assert candidate_set["ranking_summary"]["preferred_candidate_design_id"]

    comparison_envelope = compare_candidate_designs(
        study_id=study_id,
        run_id="run_20260421_workbench_compare",
    )
    assert comparison_envelope["status"] == "success"
    comparison_path = workspace_root / comparison_envelope["artifact_paths"][-1]
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    _assert_valid(comparison, "design_comparison.schema.json", store)

    first_snapshot = create_study_snapshot(
        study_id=study_id,
        run_id="run_20260421_workbench_snapshot_a",
        request={"label": "Version A before commit"},
    )
    assert first_snapshot["status"] == "success"

    commit_envelope = commit_run_plan(
        study_id=study_id,
        run_id="run_20260421_workbench_commit",
    )
    assert commit_envelope["status"] == "success"
    run_plan_path = workspace_root / commit_envelope["artifact_paths"][0]
    run_plan = json.loads(run_plan_path.read_text(encoding="utf-8"))
    _assert_valid(run_plan, "run_plan_commit.schema.json", store)
    assert (workspace_root / run_plan["run_matrix_path"]).exists()
    assert (workspace_root / run_plan["protocol_notes_path"]).exists()

    second_snapshot = create_study_snapshot(
        study_id=study_id,
        run_id="run_20260421_workbench_snapshot_b",
        request={"label": "Version B after commit"},
    )
    assert second_snapshot["status"] == "success"
    snapshot_path = workspace_root / second_snapshot["artifact_paths"][0]
    _assert_valid(json.loads(snapshot_path.read_text(encoding="utf-8")), "study_snapshot.schema.json", store)

    diff_envelope = diff_study_snapshots(
        study_id=study_id,
        run_id="run_20260421_workbench_snapshot_diff",
        request={
            "base_snapshot_id": first_snapshot["structured_content"]["snapshot_id"],
            "compare_snapshot_id": second_snapshot["structured_content"]["snapshot_id"],
        },
    )
    assert diff_envelope["status"] == "success"
    assert diff_envelope["structured_content"]["change_count"] >= 1
    diff_path = workspace_root / diff_envelope["artifact_paths"][0]
    assert json.loads(diff_path.read_text(encoding="utf-8"))["source_refs"]

    explanation_envelope = explain_study_object(
        study_id=study_id,
        run_id="run_20260421_workbench_explain",
    )
    assert explanation_envelope["status"] == "success"
    panel = explanation_envelope["structured_content"]["contextual_ai_panel"]
    _assert_valid(panel, "contextual_ai_panel.schema.json", store)
    assert panel["source_refs"]

    payload_envelope = generate_dashboard_payload(
        study_id=study_id,
        run_id="run_20260421_workbench_payload",
    )
    assert payload_envelope["status"] == "success"
    payload_path = workspace_root / payload_envelope["artifact_paths"][0]
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    _assert_valid(payload, "dashboard_payload.schema.json", store)
    assert payload["workbench"]["committed_run_plan"]["run_plan_id"] == run_plan["run_plan_id"]
    assert payload["workbench"]["contextual_ai_panels"][0]["source_refs"]

    audit_log = (workspace_root / "outputs" / "studies" / study_id / "audit_log.jsonl").read_text(encoding="utf-8")
    for tool_name in [
        "generate_candidate_designs",
        "compare_candidate_designs",
        "commit_run_plan",
        "create_study_snapshot",
        "diff_study_snapshots",
        "explain_study_object",
        "generate_dashboard_payload",
    ]:
        assert f'"tool_name": "{tool_name}"' in audit_log


def test_unsupported_candidate_is_unavailable_not_successful(workspace_root: Path) -> None:
    study_id = "workbench_unsupported"
    store = _schema_store()
    create_or_update_study(study_id=study_id, request={"title": "Unsupported Candidate"})

    envelope = generate_candidate_designs(
        study_id=study_id,
        run_id="run_20260421_workbench_unsupported",
        request=_workbench_request(candidate_families=["central_composite"]),
    )

    assert envelope["status"] == "success_with_warnings"
    candidate_set_path = workspace_root / envelope["artifact_paths"][-1]
    candidate_set = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    _assert_valid(candidate_set, "candidate_design_set.schema.json", store)

    candidate = candidate_set["candidates"][0]
    assert candidate["status"] == "unsupported"
    assert candidate["ranking_score"] is None
    assert "recommended" not in candidate["recommendation_label"].lower()
    assert "supported" not in set(candidate["capabilities"].values())
    assert candidate["unavailable_reasons"] == ["unsupported_design_type"]
