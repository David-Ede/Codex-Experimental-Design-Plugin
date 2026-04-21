from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _latest(path: Path, filename: str) -> Path | None:
    if not path.exists():
        return None
    candidates = sorted(item / filename for item in path.iterdir() if (item / filename).exists())
    return candidates[-1] if candidates else None


def _payload_or_artifacts(study_id: str) -> dict[str, Any]:
    study_dir = ROOT / "outputs" / "studies" / study_id
    payload = _load(study_dir / "dashboard_payload.json")
    if payload:
        return payload

    candidate_path = _latest(study_dir / "candidate_design_sets", "candidate_design_set.json")
    comparison_path = _latest(study_dir / "comparisons", "design_comparison.json")
    run_plan_path = _latest(study_dir / "run_plans", "run_plan.json")
    return {
        "study": (_load(study_dir / "study.json") or {}).get("study", {"study_id": study_id}),
        "workbench": {
            "candidate_design_sets": [_load(candidate_path)] if candidate_path else [],
            "active_comparison": _load(comparison_path) if comparison_path else None,
            "committed_run_plan": _load(run_plan_path) if run_plan_path else None,
            "study_stage": "run_plan_committed" if run_plan_path else "candidates_generated",
        },
        "sections": {},
        "warnings": [],
    }


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    workbench = payload.get("workbench", {})
    candidate_sets = workbench.get("candidate_design_sets") or []
    candidate_set = candidate_sets[0] if candidate_sets else {}
    candidates = [
        {
            "id": candidate.get("candidate_design_id"),
            "family": candidate.get("design_family"),
            "status": candidate.get("status"),
            "run_count": candidate.get("run_count"),
            "score": candidate.get("ranking_score"),
        }
        for candidate in candidate_set.get("candidates", [])
    ]
    unavailable_sections = {
        name: section.get("reason")
        for name, section in payload.get("sections", {}).items()
        if isinstance(section, dict) and str(section.get("status", "")).startswith("unavailable")
    }
    return {
        "study": payload.get("study", {}),
        "study_stage": workbench.get("study_stage"),
        "recommendation_mode": workbench.get("recommendation_mode") or candidate_set.get("recommendation_mode"),
        "preferred_candidate_design_id": candidate_set.get("ranking_summary", {}).get("preferred_candidate_design_id"),
        "run_plan": workbench.get("committed_run_plan"),
        "candidates": candidates,
        "warnings": payload.get("warnings", []),
        "unavailable_sections": unavailable_sections,
    }


def _print_text(summary: dict[str, Any]) -> None:
    study = summary.get("study", {})
    run_plan = summary.get("run_plan") or {}
    print(f"Study: {study.get('study_id')} - {study.get('title')}")
    print(f"Stage: {summary.get('study_stage')}")
    print(f"Recommendation mode: {summary.get('recommendation_mode')}")
    print(f"Preferred candidate: {summary.get('preferred_candidate_design_id')}")
    if run_plan:
        print(f"Run plan: {run_plan.get('run_plan_id')} ({run_plan.get('run_count')} runs)")
        print(f"Run matrix: {run_plan.get('run_matrix_path')}")
    print("Candidates:")
    for candidate in summary.get("candidates", []):
        print(
            "  "
            f"{candidate.get('id')} | {candidate.get('family')} | "
            f"{candidate.get('status')} | runs={candidate.get('run_count')} | score={candidate.get('score')}"
        )
    if summary.get("warnings"):
        print("Warnings:")
        for warning in summary["warnings"]:
            print(f"  {warning.get('code')}: {warning.get('message')}")
    if summary.get("unavailable_sections"):
        print("Unavailable sections:")
        for name, reason in summary["unavailable_sections"].items():
            print(f"  {name}: {reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a compact generated DOE study summary.")
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--json", action="store_true", help="Emit the compact summary as JSON.")
    args = parser.parse_args(argv)

    payload = _payload_or_artifacts(args.study_id)
    summary = _summary(payload)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
