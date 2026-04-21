"""DOE Scientific Toolchain Gate 0 backend package."""

from __future__ import annotations

__version__ = "0.1.0"

LAUNCH_TOOL_NAMES: tuple[str, ...] = (
    "create_or_update_study",
    "validate_factor_space",
    "design_doe",
    "design_optimal_doe",
    "import_endpoint_observations",
    "import_time_resolved_observations",
    "register_construct",
    "calculate_theoretical_yield",
    "fit_response_surface",
    "analyze_effects",
    "calculate_cogs_impact",
    "suggest_next_experiment",
    "plan_verification_runs",
    "generate_dashboard_payload",
    "launch_dashboard_preview",
)

WORKBENCH_TOOL_NAMES: tuple[str, ...] = (
    "generate_candidate_designs",
    "rank_candidate_designs",
    "compare_candidate_designs",
    "commit_run_plan",
    "create_study_snapshot",
    "diff_study_snapshots",
    "explain_study_object",
)

PAPER_CLASS_TOOL_NAMES: tuple[str, ...] = (
    "estimate_design_space_probability",
    "compare_verification_results",
    "transfer_construct_model",
    "analyze_counterion_doe",
    "fit_time_resolved_response_model",
)
