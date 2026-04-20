from __future__ import annotations

from pathlib import Path

from scripts.validate_schemas import REQUIRED_SCHEMA_FILES, run_validation


def test_required_gate0_schema_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for schema_name in REQUIRED_SCHEMA_FILES:
        assert (repo_root / "schemas" / schema_name).exists()


def test_gate0_schema_validation_passes() -> None:
    result = run_validation()
    assert result.ok, result


def test_invalid_fixtures_fail_for_expected_reasons() -> None:
    result = run_validation()
    assert all(expectation.matched for expectation in result.invalid_fixture_expectations)
