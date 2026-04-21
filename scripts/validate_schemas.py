from __future__ import annotations

import json
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from jsonschema import RefResolver
except ImportError as exc:  # pragma: no cover - exercised only outside the managed env.
    raise SystemExit(
        "jsonschema is required. Run: uv --directory mcp-server run python ..\\scripts\\validate_schemas.py"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"
FIXTURE_ROOT = ROOT / "fixtures"

REQUIRED_SCHEMA_FILES = [
    "artifact_metadata.schema.json",
    "warning.schema.json",
    "error.schema.json",
    "tool_envelope.schema.json",
    "audit_log_entry.schema.json",
    "study.schema.json",
    "factor_space.schema.json",
    "responses.schema.json",
    "learnability_summary.schema.json",
    "candidate_design.schema.json",
    "candidate_design_set.schema.json",
    "design_comparison.schema.json",
    "run_plan_commit.schema.json",
    "study_snapshot.schema.json",
    "stale_state.schema.json",
    "contextual_ai_panel.schema.json",
    "workbench_payload.schema.json",
    "dashboard_payload.schema.json",
]

VALID_FIXTURES = [
    ("fixtures/studies/minimal_doe/study.json", "study.schema.json"),
    ("fixtures/studies/minimal_doe/factor_space.json", "factor_space.schema.json"),
    ("fixtures/studies/minimal_doe/responses.json", "responses.schema.json"),
    ("fixtures/studies/minimal_doe/dashboard_payload.json", "dashboard_payload.schema.json"),
    ("fixtures/dashboard/empty_payload_state.json", "dashboard_payload.schema.json"),
    ("fixtures/dashboard/perfect_latte_dummy_payload.json", "dashboard_payload.schema.json"),
    ("fixtures/dashboard/phase0_design_only_payload.json", "dashboard_payload.schema.json"),
    ("fixtures/dashboard/workbench_candidate_designs_payload.json", "dashboard_payload.schema.json"),
]

INVALID_FIXTURES = [
    (
        "fixtures/studies/invalid_bad_study_id/study.json",
        "study.schema.json",
        "invalid_study_id",
        "study.study_id",
    ),
    (
        "fixtures/studies/invalid_bad_factor_bounds/factor_space.json",
        "factor_space.schema.json",
        "invalid_factor_bounds",
        "factor_space.factors[0].low",
    ),
    (
        "fixtures/studies/invalid_duplicate_normalized_names/factor_space.json",
        "factor_space.schema.json",
        "duplicate_factor_name",
        "factor_space.factors[1].name",
    ),
    (
        "fixtures/studies/invalid_missing_metadata/study.json",
        "study.schema.json",
        "missing_metadata",
        "artifact_metadata",
    ),
    (
        "fixtures/studies/invalid_units/factor_space.json",
        "factor_space.schema.json",
        "invalid_units",
        "factor_space.factors[0].units",
    ),
    (
        "fixtures/dashboard/payload_validation_error.json",
        "dashboard_payload.schema.json",
        "schema_validation_failed",
        "version",
    ),
    (
        "fixtures/dashboard/invalid_contextual_ai_panel_missing_source_refs.json",
        "contextual_ai_panel.schema.json",
        "schema_validation_failed",
        "source_refs",
    ),
]

UNIT_REGISTRY = {
    "ratio",
    "mass_ratio",
    "fraction_total_dna",
    "percent",
    "%",
    "score",
    "mM",
    "uM",
    "nM",
    "g/L",
    "mg/L",
    "ug/mL",
    "ng/uL",
    "ug/10^6 cells",
    "10^6 viable cells/mL",
    "vg/mL",
    "TU/mL",
    "U/uL",
    "L",
    "mL",
    "uL",
    "h",
    "min",
    "s",
    "kg",
    "g",
    "mg",
    "ug",
    "ng",
    "mol",
    "mmol",
    "umol",
    "nmol",
    "USD",
    "EUR",
    "GBP",
    "USD/U",
    "EUR/U",
    "USD/ng",
    "EUR/ng",
    "USD/umol",
    "EUR/umol",
    "USD/batch",
    "EUR/batch",
}


@dataclass(frozen=True)
class ValidationIssue:
    source: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class FixtureExpectation:
    fixture: str
    schema: str
    expected_code: str
    expected_path: str
    matched: bool
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class ValidationRunResult:
    schema_errors: tuple[ValidationIssue, ...]
    valid_fixture_errors: tuple[ValidationIssue, ...]
    invalid_fixture_expectations: tuple[FixtureExpectation, ...]

    @property
    def ok(self) -> bool:
        return (
            not self.schema_errors
            and not self.valid_fixture_errors
            and all(expectation.matched for expectation in self.invalid_fixture_expectations)
        )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_store() -> dict[str, Any]:
    return {name: _load_json(SCHEMA_ROOT / name) for name in REQUIRED_SCHEMA_FILES}


def _path_from_parts(parts: list[Any]) -> str:
    rendered = ""
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}" if rendered else str(part)
    return rendered


def _schema_error_path(error: Any) -> str:
    parts = list(error.absolute_path)
    if error.validator == "required":
        match = re.search(r"'([^']+)' is a required property", error.message)
        if match:
            parts.append(match.group(1))
    return _path_from_parts(parts)


def _schema_error_code(error: Any) -> str:
    path = _schema_error_path(error)
    if error.validator == "required" and path == "artifact_metadata":
        return "missing_metadata"
    if error.validator == "pattern" and path == "study.study_id":
        return "invalid_study_id"
    return "schema_validation_failed"


def _validator(schema_name: str, store: dict[str, Any]) -> Draft202012Validator:
    schema = store[schema_name]
    resolver = RefResolver.from_schema(schema, store=store)
    return Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())


def _structural_issues(fixture: str, schema_name: str, store: dict[str, Any]) -> list[ValidationIssue]:
    document = _load_json(ROOT / fixture)
    validator = _validator(schema_name, store)
    issues: list[ValidationIssue] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path)):
        issues.append(
            ValidationIssue(
                source=fixture,
                code=_schema_error_code(error),
                path=_schema_error_path(error),
                message=error.message,
            )
        )
    return issues


def _normalized_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return re.sub(r"_+", "_", normalized)


def _semantic_issues(fixture: str, schema_name: str) -> list[ValidationIssue]:
    document = _load_json(ROOT / fixture)
    if schema_name == "factor_space.schema.json":
        return _factor_space_semantic_issues(fixture, document)
    if schema_name == "responses.schema.json":
        return _responses_semantic_issues(fixture, document)
    return []


def _factor_space_semantic_issues(fixture: str, document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    factors = document.get("factor_space", {}).get("factors", [])
    seen_names: dict[str, int] = {}
    for index, factor in enumerate(factors):
        name = factor.get("name")
        if isinstance(name, str):
            normalized = _normalized_name(name)
            if normalized in seen_names:
                issues.append(
                    ValidationIssue(
                        source=fixture,
                        code="duplicate_factor_name",
                        path=f"factor_space.factors[{index}].name",
                        message=f"Duplicate normalized factor name {normalized}.",
                    )
                )
            seen_names[normalized] = index

        units = factor.get("units")
        if units not in UNIT_REGISTRY:
            issues.append(
                ValidationIssue(
                    source=fixture,
                    code="invalid_units",
                    path=f"factor_space.factors[{index}].units",
                    message=f"Unit {units!r} is not in the launch unit registry.",
                )
            )

        if factor.get("kind") == "continuous":
            low = factor.get("low")
            high = factor.get("high")
            if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or low >= high:
                issues.append(
                    ValidationIssue(
                        source=fixture,
                        code="invalid_factor_bounds",
                        path=f"factor_space.factors[{index}].low",
                        message="Continuous factor low bound must be less than high bound.",
                    )
                )
    return issues


def _responses_semantic_issues(fixture: str, document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen_names: set[str] = set()
    for index, response in enumerate(document.get("responses", [])):
        name = response.get("name")
        if isinstance(name, str):
            normalized = _normalized_name(name)
            if normalized in seen_names:
                issues.append(
                    ValidationIssue(
                        source=fixture,
                        code="duplicate_response_name",
                        path=f"responses[{index}].name",
                        message=f"Duplicate normalized response name {normalized}.",
                    )
                )
            seen_names.add(normalized)
        units = response.get("units")
        if units not in UNIT_REGISTRY:
            issues.append(
                ValidationIssue(
                    source=fixture,
                    code="invalid_units",
                    path=f"responses[{index}].units",
                    message=f"Unit {units!r} is not in the launch unit registry.",
                )
            )
    return issues


def validate_fixture(fixture: str, schema_name: str, store: dict[str, Any]) -> list[ValidationIssue]:
    issues = _structural_issues(fixture, schema_name, store)
    if not issues:
        issues.extend(_semantic_issues(fixture, schema_name))
    return issues


def run_validation() -> ValidationRunResult:
    schema_errors: list[ValidationIssue] = []
    for name in REQUIRED_SCHEMA_FILES:
        path = SCHEMA_ROOT / name
        if not path.exists():
            schema_errors.append(
                ValidationIssue("schemas", "missing_schema", name, f"{name} does not exist.")
            )
            continue
        try:
            Draft202012Validator.check_schema(_load_json(path))
        except Exception as exc:  # noqa: BLE001 - report schema authoring failures clearly.
            schema_errors.append(ValidationIssue("schemas", "invalid_schema", name, str(exc)))

    store = _schema_store() if not schema_errors else {}
    valid_fixture_errors: list[ValidationIssue] = []
    for fixture, schema_name in VALID_FIXTURES:
        valid_fixture_errors.extend(validate_fixture(fixture, schema_name, store))

    invalid_expectations: list[FixtureExpectation] = []
    for fixture, schema_name, expected_code, expected_path in INVALID_FIXTURES:
        issues = validate_fixture(fixture, schema_name, store)
        matched = any(issue.code == expected_code and issue.path == expected_path for issue in issues)
        invalid_expectations.append(
            FixtureExpectation(
                fixture=fixture,
                schema=schema_name,
                expected_code=expected_code,
                expected_path=expected_path,
                matched=matched,
                issues=tuple(issues),
            )
        )

    return ValidationRunResult(
        schema_errors=tuple(schema_errors),
        valid_fixture_errors=tuple(valid_fixture_errors),
        invalid_fixture_expectations=tuple(invalid_expectations),
    )


def _print_result(result: ValidationRunResult) -> None:
    for issue in result.schema_errors:
        print(f"SCHEMA ERROR {issue.source} {issue.path} {issue.code}: {issue.message}")
    for issue in result.valid_fixture_errors:
        print(f"VALID FIXTURE ERROR {issue.source} {issue.path} {issue.code}: {issue.message}")
    for expectation in result.invalid_fixture_expectations:
        status = "matched" if expectation.matched else "missing"
        print(
            "INVALID FIXTURE "
            f"{status} {expectation.fixture}: "
            f"{expectation.expected_code} at {expectation.expected_path}"
        )
        if not expectation.matched:
            for issue in expectation.issues:
                print(f"  observed {issue.code} at {issue.path}: {issue.message}")
    if result.ok:
        print("Gate 0 schema validation passed.")


def main() -> int:
    result = run_validation()
    _print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
