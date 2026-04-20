from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from doe_toolchain.server import create_or_update_study
from scripts.validate_schemas import _schema_store, _validator


def test_create_or_update_study_writes_study_and_audit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DOE_TOOLCHAIN_WORKSPACE_ROOT", str(tmp_path))

    envelope = create_or_update_study(
        study_id="gate0_test_study",
        run_id="run_20260420_190000_gate0",
        request={"title": "Gate 0 Test Study", "domain_template": "ivt_qbd"},
        options={"seed": 20260420},
    )

    assert envelope["status"] == "success"
    assert envelope["study_id"] == "gate0_test_study"
    assert envelope["artifact_paths"] == ["outputs/studies/gate0_test_study/study.json"]

    store = _schema_store()
    envelope_validator: Draft202012Validator = _validator("tool_envelope.schema.json", store)
    assert list(envelope_validator.iter_errors(envelope)) == []

    study_path = tmp_path / "outputs" / "studies" / "gate0_test_study" / "study.json"
    audit_path = tmp_path / "outputs" / "studies" / "gate0_test_study" / "audit_log.jsonl"
    assert study_path.exists()
    assert audit_path.exists()

    study_doc = json.loads(study_path.read_text(encoding="utf-8"))
    study_validator: Draft202012Validator = _validator("study.schema.json", store)
    assert list(study_validator.iter_errors(study_doc)) == []

    audit_doc = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    audit_validator: Draft202012Validator = _validator("audit_log_entry.schema.json", store)
    assert list(audit_validator.iter_errors(audit_doc)) == []
    assert audit_doc["tool_name"] == "create_or_update_study"
