from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from validate_schemas import _schema_store, _validator


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_BY_NAME = {
    "study.json": "study.schema.json",
    "factor_space.json": "factor_space.schema.json",
    "responses.json": "responses.schema.json",
    "candidate_design_set.json": "candidate_design_set.schema.json",
    "design_comparison.json": "design_comparison.schema.json",
    "run_plan.json": "run_plan_commit.schema.json",
    "dashboard_payload.json": "dashboard_payload.schema.json",
}


def _study_artifacts(study_id: str) -> list[Path]:
    study_dir = ROOT / "outputs" / "studies" / study_id
    paths: list[Path] = []
    for filename in ("study.json", "factor_space.json", "responses.json", "dashboard_payload.json"):
        path = study_dir / filename
        if path.exists():
            paths.append(path)
    for pattern in (
        "candidate_design_sets/*/candidate_design_set.json",
        "comparisons/*/design_comparison.json",
        "run_plans/*/run_plan.json",
    ):
        paths.extend(sorted(study_dir.glob(pattern)))
    return paths


def _resolve_artifacts(study_id: str | None, artifact_args: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    if study_id:
        paths.extend(_study_artifacts(study_id))
    for artifact in artifact_args:
        raw_path, _, _schema = artifact.partition(":")
        path = Path(raw_path)
        paths.append(path if path.is_absolute() else ROOT / path)
    return paths


def _schema_for(path: Path, artifact_arg: str | None = None) -> str | None:
    if artifact_arg and ":" in artifact_arg:
        return artifact_arg.rsplit(":", 1)[1]
    return SCHEMA_BY_NAME.get(path.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated DOE study artifacts with the repo schema set.")
    parser.add_argument("--study-id", help="Validate known artifacts under outputs/studies/<study-id>.")
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Validate an artifact path. Use path:schema.schema.json when the schema cannot be inferred.",
    )
    args = parser.parse_args(argv)

    artifact_args = list(args.artifact)
    paths = _resolve_artifacts(args.study_id, artifact_args)
    if not paths:
        print("No artifacts found to validate.", file=sys.stderr)
        return 1

    store = _schema_store()
    failures = 0
    artifact_arg_by_path = {
        str((Path(item.partition(":")[0]) if Path(item.partition(":")[0]).is_absolute() else ROOT / item.partition(":")[0]).resolve()): item
        for item in artifact_args
    }
    for path in paths:
        artifact_arg = artifact_arg_by_path.get(str(path.resolve()))
        schema_name = _schema_for(path, artifact_arg)
        if schema_name is None:
            print(f"SKIP {path.relative_to(ROOT).as_posix()} -> schema unknown")
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(_validator(schema_name, store).iter_errors(document), key=lambda item: list(item.absolute_path))
        rel = path.relative_to(ROOT).as_posix()
        if errors:
            failures += 1
            print(f"FAIL {rel} -> {schema_name}")
            for error in errors:
                location = "/".join(str(part) for part in error.absolute_path) or "."
                print(f"  {location}: {error.message}")
        else:
            print(f"OK {rel} -> {schema_name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
