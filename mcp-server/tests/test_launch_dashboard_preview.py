from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import doe_toolchain.server as server
from doe_toolchain.server import create_or_update_study, generate_dashboard_payload, launch_dashboard_preview
from scripts.validate_schemas import _schema_store, _validator


@pytest.fixture()
def workspace_root(monkeypatch: pytest.MonkeyPatch) -> Path:
    root = Path(__file__).resolve().parents[2] / ".tmp_pytest_dashboard_launch" / uuid.uuid4().hex
    root.mkdir(parents=True)
    monkeypatch.setenv("DOE_TOOLCHAIN_WORKSPACE_ROOT", str(root))
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _assert_valid_envelope(envelope: dict[str, object]) -> None:
    store = _schema_store()
    validator: Draft202012Validator = _validator("tool_envelope.schema.json", store)
    assert list(validator.iter_errors(envelope)) == []


def _create_payload(study_id: str) -> None:
    create = create_or_update_study(
        study_id=study_id,
        request={"title": study_id.replace("_", " ").title(), "domain_template": "ivt_qbd"},
    )
    assert create["status"] == "success"
    payload = generate_dashboard_payload(study_id=study_id)
    assert payload["status"] == "success"


def test_launch_dashboard_preview_returns_stable_url_and_audits(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "dashboard_launch"
    _create_payload(study_id)
    monkeypatch.setattr(server, "_probe_dashboard_server", lambda host, port: False)

    envelope = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_launch",
        request={"mode": "return_url_only"},
    )

    _assert_valid_envelope(envelope)
    assert envelope["status"] == "success"
    structured = envelope["structured_content"]
    assert structured["server_status"] == "not_started"
    assert structured["payload_path"] == f"outputs/studies/{study_id}/dashboard_payload.json"
    assert f"/studies/{study_id}" in structured["url"]
    assert "payloadUrl=" in structured["url"]
    audit_log = (workspace_root / "outputs" / "studies" / study_id / "audit_log.jsonl").read_text(encoding="utf-8")
    assert '"tool_name": "launch_dashboard_preview"' in audit_log


def test_launch_dashboard_preview_reports_existing_server(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "dashboard_existing"
    _create_payload(study_id)
    monkeypatch.setattr(server, "_probe_dashboard_server", lambda host, port: True)

    envelope = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_existing",
        request={"mode": "check_existing_server"},
    )

    _assert_valid_envelope(envelope)
    assert envelope["status"] == "success"
    assert envelope["structured_content"]["server_status"] == "already_running"


def test_launch_dashboard_preview_starts_dev_server_when_requested(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "dashboard_start"
    _create_payload(study_id)
    monkeypatch.setattr(server, "_probe_dashboard_server", lambda host, port: False)
    monkeypatch.setattr(server, "_start_dashboard_dev_server", lambda host, port, timeout: ("started", 4321, None))

    envelope = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_start",
        request={"mode": "start_dev_server", "port": 5187},
    )

    _assert_valid_envelope(envelope)
    assert envelope["status"] == "success"
    assert envelope["structured_content"]["server_status"] == "started"
    assert envelope["structured_content"]["pid"] == 4321
    assert ":5187/studies/dashboard_start" in envelope["structured_content"]["url"]


def test_launch_dashboard_preview_requires_payload(workspace_root: Path) -> None:
    study_id = "dashboard_missing_payload"
    create = create_or_update_study(study_id=study_id, request={"title": "Missing Payload"})
    assert create["status"] == "success"

    envelope = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_missing_payload",
    )

    _assert_valid_envelope(envelope)
    assert envelope["status"] == "failed_validation"
    assert envelope["errors"][0]["code"] == "dashboard_payload_not_found"
    audit_log = (workspace_root / "outputs" / "studies" / study_id / "audit_log.jsonl").read_text(encoding="utf-8")
    assert '"tool_name": "launch_dashboard_preview"' in audit_log


def test_launch_dashboard_preview_validates_host_and_port(workspace_root: Path) -> None:
    study_id = "dashboard_validation"
    _create_payload(study_id)

    invalid_host = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_invalid_host",
        request={"host": "0.0.0.0"},
    )
    invalid_port = launch_dashboard_preview(
        study_id=study_id,
        run_id="run_20260421_dashboard_invalid_port",
        request={"port": 70000},
    )

    _assert_valid_envelope(invalid_host)
    _assert_valid_envelope(invalid_port)
    assert invalid_host["status"] == "failed_validation"
    assert invalid_host["errors"][0]["code"] == "invalid_host"
    assert invalid_port["status"] == "failed_validation"
    assert invalid_port["errors"][0]["code"] == "invalid_port"
