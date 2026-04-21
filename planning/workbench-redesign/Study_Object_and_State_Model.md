# Study Object and State Model

Date: 2026-04-21
Status: Draft redesign direction

## 1. Purpose

This document defines the study-object model required for the workbench redesign. The goal is to make the study the central product object, with candidate designs, comparisons, recommendations, snapshots, and run plans derived from explicit state.

## 2. Core Object Model

Top-level study object:

```text
Study
  metadata
  objective
  recommendation_mode
  factor_space
  responses
  constraints
  fixed_conditions
  execution_constraints
  expected_noise
  candidate_design_sets
  comparisons
  committed_run_plan
  observations
  models
  recommendations
  snapshots
  audit_log
```

The existing persisted artifact model can remain the storage foundation. The redesign adds stronger product semantics around candidate design generation and comparison.

## 3. Study Lifecycle

Recommended state flow:

```text
draft_setup
  -> validated_setup
  -> candidates_generated
  -> candidates_compared
  -> run_plan_committed
  -> observations_imported
  -> model_fit
  -> augmentation_recommended
  -> verification_planned
  -> verification_observed
```

State rules:

```text
- Candidate designs require validated setup.
- Comparison requires at least two available candidate designs.
- Run plan requires a selected candidate design.
- Model fitting requires observed data.
- Augmentation recommendations require at least one model or explicit sequential strategy.
- Verification observed requires a verification plan and matching observations.
```

## 4. Recommendation Mode

Recommendation mode converts user intent into design-ranking criteria.

Allowed initial modes:

```text
minimize_runs
screen_important_factors
estimate_interactions
fit_curvature
optimize_response
respect_material_time_constraints
prepare_scale_up_robustness
custom_weighted_objective
```

Each mode should map to:

```text
- target model terms
- preferred design families
- run-count tolerance
- replicate and center-point policy
- diagnostic thresholds
- ranking weights
- explanation template
```

Example:

```json
{
  "mode": "fit_curvature",
  "ranking_weights": {
    "curvature_support": 0.30,
    "model_rank": 0.25,
    "prediction_precision": 0.20,
    "run_count_efficiency": 0.15,
    "execution_burden": 0.10
  },
  "required_capabilities": [
    "quadratic_terms",
    "center_points"
  ]
}
```

## 5. Candidate Design Set

A candidate design set is the result of generating alternatives for one validated study setup.

```text
CandidateDesignSet
  candidate_set_id
  study_id
  source_snapshot_id
  recommendation_mode
  generated_at
  generator_tool
  input_hash
  candidates[]
  ranking_summary
  warnings[]
```

Candidate design:

```text
CandidateDesign
  candidate_design_id
  design_family
  status
  run_count
  matrix_artifact_path
  metadata_artifact_path
  diagnostics
  capabilities
  tradeoffs
  unavailable_reasons
  recommendation_label
  ranking_score
  explanation_refs
```

Candidate statuses:

```text
recommended
available
available_with_warnings
not_recommended
infeasible
unsupported
failed_validation
stale
```

## 6. Design Capabilities

Each candidate design should expose machine-readable capability flags.

```text
Capabilities
  main_effects
  two_factor_interactions
  selected_interactions
  quadratic_terms
  curvature_detection
  pure_error_estimate
  lack_of_fit_test
  blocking
  randomization
  hard_to_change_factor_support
  categorical_factor_support
  missing_run_robustness
  sequential_augmentation_path
```

Capability values:

```text
supported
partially_supported
unsupported
unknown
not_applicable
```

## 7. Learn / Cannot Learn Model

Every candidate design should generate a visible "can learn / cannot learn" summary.

```text
Can learn:
  - main effects for all selected factors
  - selected two-factor interactions
  - curvature for continuous factors with center/axial support

Cannot learn:
  - aliased interactions
  - full quadratic model when run count is insufficient
  - lack of fit without replicated points or pure error
  - behavior outside supplied ranges
```

This should be structured data, not just prose.

```json
{
  "learnable": [
    {
      "claim": "main_effects_estimable",
      "label": "Main effects are estimable",
      "support": "supported",
      "source": "design_metadata.json#diagnostics.model_matrix_rank"
    }
  ],
  "not_learnable": [
    {
      "claim": "full_quadratic_not_estimable",
      "label": "Full curvature model is not estimable",
      "reason_code": "target_runs_less_than_model_columns",
      "source": "design_metadata.json#warnings"
    }
  ]
}
```

## 8. Comparison Object

A comparison object records selected candidates and decision criteria.

```text
DesignComparison
  comparison_id
  candidate_set_id
  selected_candidate_design_ids[]
  active_metrics[]
  ranking_weights
  preferred_candidate_design_id
  user_selected_candidate_design_id
  decision_notes
  generated_at
```

Comparison metrics:

```text
- run_count
- model_rank
- condition_number
- estimable_term_fraction
- curvature_support
- interaction_support
- alias_risk
- pure_error_support
- missing_run_sensitivity
- execution_burden
- material_cost_proxy
- blocking_fit
- randomization_fit
```

## 9. Snapshot and Version Model

Snapshots preserve reasoning across changes.

```text
StudySnapshot
  snapshot_id
  label
  created_at
  study_state_hash
  setup_hash
  active_candidate_set_id
  active_comparison_id
  committed_design_id
  notes
```

Version examples:

```text
Version A: 5 factors, screening focus
Version B: 4 factors, curvature focus
Version C: constrained custom design
```

Diff fields:

```text
- factor additions/removals
- factor range changes
- response goal changes
- constraint changes
- max run changes
- recommendation mode changes
- selected design changes
- diagnostics changes
```

## 10. Staleness Model

Any state derived from setup becomes stale when upstream inputs change.

Upstream changes:

```text
- factor bounds
- factor levels
- response goals
- constraints
- fixed conditions
- execution constraints
- recommendation mode
- max run budget
- expected noise
```

Affected downstream objects:

```text
- candidate design sets
- comparisons
- committed run plan, if not locked
- recommendations
- dashboard payload
- AI explanations
```

The UI should show:

```text
stale_due_to:
  - factor_space_changed
  - response_goals_changed
  - constraints_changed
  - objective_changed
```

## 11. MCP Tool Implications

The current tool inventory should be expanded or refined to support workbench behavior.

New or revised tool concepts:

```text
validate_study_setup
generate_candidate_designs
rank_candidate_designs
compare_candidate_designs
commit_run_plan
create_study_snapshot
diff_study_snapshots
explain_study_object
```

These can be implemented as new tools or as structured modes of existing tools. The key requirement is that candidate comparison and commit-to-run-plan become explicit artifacts.

## 12. Dashboard Payload Implications

`dashboard_payload.json` should evolve toward a workbench payload:

```text
workbench
  study_state
  setup_sections
  candidate_design_sets
  active_comparison
  committed_run_plan
  contextual_ai_panels
  snapshots
  stale_state
  warnings
  diagnostics
```

Payload rule:

```text
The React workbench can sort, filter, select, and display. It must not compute final design rankings or scientific diagnostics client-side.
```

## 13. Acceptance Criteria

The state model is sufficient when:

```text
- The workbench can show multiple candidate designs from one setup.
- The user can compare candidates without regenerating all science client-side.
- The user can commit a candidate into a run plan.
- The user can preserve and diff study snapshots.
- AI explanations can bind to specific object IDs and source artifacts.
- Stale downstream state is visible after upstream edits.
```

