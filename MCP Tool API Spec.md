# MCP Tool API Spec: Codex Scientific Toolchain

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Scientific Methods Spec.md
- Data & Schema Contract.md
- Canonical Build Contract.md
```

## 1. Purpose

This document defines the MCP tool API for the Codex Scientific Toolchain. It specifies tool names, launch availability, input contracts, output contracts, side effects, validation behavior, error behavior, idempotency expectations, and example calls.

The API is designed for a local Python MCP server used by Codex. Codex calls these tools to produce deterministic scientific artifacts. The tools write study artifacts under `outputs/studies/<study_id>/` and return structured summaries for Codex to explain to the user.

## 2. API Design Principles

1. Tools are small enough to debug and audit.
2. Tools return structured outputs and write durable artifacts.
3. Tools never rely on Codex for numerical calculation.
4. Tools never invent component costs or reagent prices.
5. Tools preserve source data and write derived data separately.
6. Tools report unavailable states explicitly.
7. Tools are deterministic for identical inputs, method versions, package versions, and seeds.
8. Tools record audit log entries for success, warning, failure, and skipped states.
9. Tools use workspace-relative artifact paths in persisted outputs.
10. Tools validate inputs before scientific computation.

## 3. Launch Tool Inventory

Launch tools:

```text
create_or_update_study
validate_factor_space
design_doe
design_optimal_doe
import_endpoint_observations
import_time_resolved_observations
register_construct
calculate_theoretical_yield
fit_response_surface
analyze_effects
calculate_cogs_impact
suggest_next_experiment
plan_verification_runs
generate_dashboard_payload
launch_dashboard_preview
```

Post-launch or paper-class expansion tools:

```text
estimate_design_space_probability
compare_verification_results
transfer_construct_model
analyze_counterion_doe
fit_time_resolved_response_model
```

Tool naming rules:

```text
- Tool names are lowercase snake_case.
- Tool names describe one primary action.
- Tool names must remain stable once released.
- Breaking changes require a new version or new tool name.
```

## 4. Common MCP Tool Envelope

### 4.1 Common Input Envelope

Every study-scoped tool accepts:

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "request": {},
  "options": {
    "seed": 20260420,
    "overwrite_policy": "write_new_run",
    "strict_validation": true,
    "dry_run": false
  }
}
```

Rules:

```text
- study_id is required for all tools except create_or_update_study when creating a new study.
- run_id is optional; the server generates one if absent.
- request contains tool-specific inputs.
- options is optional.
- seed is required for stochastic methods unless a generated seed is acceptable.
- dry_run validates and plans side effects without writing final scientific artifacts.
```

Allowed overwrite policies:

```text
write_new_run
replace_latest_pointer
fail_if_exists
```

Launch default:

```text
overwrite_policy = write_new_run
strict_validation = true
dry_run = false
```

### 4.2 Common Output Envelope

Every tool returns:

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated a 12-run D-optimal design.",
  "artifact_paths": [],
  "artifact_hashes": {},
  "warnings": [],
  "errors": [],
  "structured_content": {}
}
```

Allowed statuses:

```text
success
success_with_warnings
failed_validation
failed_runtime
skipped
```

Rules:

```text
- `summary` is concise and human-readable.
- `structured_content` contains the key machine-readable result.
- Persisted artifacts are authoritative over summary text.
- Failed validation returns errors and writes an audit entry.
- Runtime failures return structured errors when possible.
```

### 4.3 Warning Object

```json
{
  "code": "weak_predictive_score",
  "severity": "warning",
  "message": "Cross-validated Q2 is below the configured threshold.",
  "field": "structured_content.metrics.q2",
  "details": {
    "q2": 0.41,
    "threshold": 0.5
  }
}
```

Allowed severities:

```text
info
warning
blocking
```

### 4.4 Error Object

```json
{
  "code": "invalid_factor_bounds",
  "message": "Factor low bound must be less than high bound.",
  "field": "request.factors[0].low",
  "recoverable": true,
  "details": {
    "low": 12,
    "high": 6
  }
}
```

### 4.5 Audit Behavior

Every tool call writes one audit log entry to:

```text
outputs/studies/<study_id>/audit_log.jsonl
```

Audit entries record:

```text
timestamp
study_id
run_id
tool_name
tool_version
method_version
schema_version
input_hash
output_hash
status
duration_ms
seed
artifact_paths
warnings
errors
```

For `dry_run = true`, the tool writes an audit entry with `status = skipped` and no final scientific artifacts.

## 5. Cross-Tool Status and Idempotency

### 5.1 Idempotency

Tools are functionally idempotent for the same:

```text
- input payload
- study artifacts referenced by input
- method version
- package versions
- random seed
```

Idempotency rules:

```text
- Same deterministic call produces same artifact content hash.
- New run_id may differ unless caller supplies run_id.
- If overwrite_policy = fail_if_exists and target artifact exists, tool returns failed_validation.
- If overwrite_policy = replace_latest_pointer, latest pointer can change but historical audit entries remain.
```

### 5.2 Tool Preconditions

Common precondition errors:

```text
study_not_found
factor_space_not_found
responses_not_found
design_not_found
observations_not_found
construct_not_found
model_fit_not_found
economics_unavailable
dashboard_payload_not_found
```

### 5.3 Data Source Rules

Tools may read:

```text
- current request payload
- existing study artifacts
- workspace-relative CSV/JSON files supplied by user
```

Tools must not:

```text
- fetch external reagent prices
- upload data externally by default
- read files outside the workspace unless explicitly provided as an input path
- mutate user source data files
```

## 6. Tool: `create_or_update_study`

### 6.1 Purpose

Create a new study or update study metadata, domain template, active construct, and active artifact pointers.

### 6.2 Availability

```text
Launch required
```

### 6.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "title": "IVT eGFP DOE",
    "domain_template": "ivt_qbd",
    "status": "active",
    "active_construct_id": "egfp_995nt",
    "metadata": {
      "owner": "process_development"
    }
  },
  "options": {
    "overwrite_policy": "replace_latest_pointer"
  }
}
```

Required request fields:

```text
title
```

Optional request fields:

```text
study_id
domain_template
status
active_construct_id
metadata
```

If `study_id` is omitted, the server generates one from the title plus a short suffix.

### 6.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Created study ivt_egfp_001.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/study.json"
  ],
  "artifact_hashes": {
    "study": "sha256:studyhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "study_id": "ivt_egfp_001",
    "study_path": "outputs/studies/ivt_egfp_001/study.json"
  }
}
```

### 6.5 Side Effects

Writes or updates:

```text
outputs/studies/<study_id>/study.json
outputs/studies/<study_id>/audit_log.jsonl
```

Creates study directory if missing.

### 6.6 Validation and Errors

Errors:

```text
invalid_study_id
study_exists
invalid_status
invalid_domain_template
```

Warnings:

```text
domain_template_not_set
active_construct_missing
```

## 7. Tool: `validate_factor_space`

### 7.1 Purpose

Validate and normalize factors, responses, constraints, transforms, units, and IVT/QbD template defaults before DOE generation or model fitting.

### 7.2 Availability

```text
Launch required
```

### 7.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "factors": [
      {
        "name": "mg_ntp_ratio",
        "display_name": "Mg:NTP ratio",
        "kind": "continuous",
        "units": "ratio",
        "low": 0.8,
        "high": 1.6,
        "transform": { "name": "none", "parameters": {} }
      }
    ],
    "responses": [
      {
        "name": "mrna_yield",
        "display_name": "mRNA yield",
        "role": "productivity",
        "goal": "maximize",
        "units": "g/L",
        "weight": 1.0
      },
      {
        "name": "dsrna_score",
        "display_name": "dsRNA score",
        "role": "CQA",
        "goal": "upper_threshold",
        "units": "score",
        "threshold": {
          "operator": "<",
          "value": 3,
          "unit": "score",
          "hard_constraint": true
        }
      }
    ],
    "constraints": [],
    "domain_template": "ivt_qbd"
  },
  "options": {
    "strict_validation": true
  }
}
```

Required request fields:

```text
factors
responses
```

Optional request fields:

```text
constraints
domain_template
fixed_conditions
normalization_options
```

### 7.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Validated 4 factors and 4 responses.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/factor_space.json",
    "outputs/studies/ivt_egfp_001/responses.json"
  ],
  "artifact_hashes": {
    "factor_space": "sha256:factorhash",
    "responses": "sha256:responsehash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "valid": true,
    "normalized_factor_count": 4,
    "normalized_response_count": 4,
    "constraint_count": 0
  }
}
```

### 7.5 Side Effects

Writes:

```text
factor_space.json
responses.json
study.json latest artifact pointers
audit_log.jsonl
```

### 7.6 Validation and Errors

Errors:

```text
missing_factors
missing_responses
duplicate_factor_name
duplicate_response_name
factor_response_name_collision
invalid_factor_kind
invalid_factor_bounds
invalid_categorical_levels
invalid_transform_for_bounds
invalid_units
invalid_constraint_expression
missing_response_goal
invalid_threshold
```

Warnings:

```text
factor_with_single_level_treated_as_fixed
response_weight_missing_defaulted
domain_template_defaults_applied
economics_response_unavailable_until_costs_supplied
```

### 7.7 Example Codex Use

Use this tool first for any new DOE, imported dataset, or optimization request. If validation fails, Codex should ask for corrected bounds, levels, units, response goals, or thresholds.

## 8. Tool: `design_doe`

### 8.1 Purpose

Generate a standard DOE matrix using full factorial, fractional factorial, Latin hypercube, or simple response-surface designs. For D-optimal candidate-set design, Codex should prefer `design_optimal_doe`.

### 8.2 Availability

```text
Launch required
```

### 8.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "design_type": "latin_hypercube",
    "factor_space": null,
    "target_runs": 24,
    "replicates": 0,
    "center_points": 3,
    "blocks": 1,
    "randomize": true,
    "model_intent": "screening_main_effects",
    "use_existing_factor_space": true
  },
  "options": {
    "seed": 20260420
  }
}
```

Required request fields:

```text
design_type
```

Allowed design types:

```text
full_factorial
fractional_factorial
latin_hypercube
central_composite
box_behnken
```

Launch implementation requirement:

```text
full_factorial
fractional_factorial
latin_hypercube
```

Central composite and Box-Behnken may return `failed_validation` with `unsupported_design_type` until implemented.

### 8.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated a 24-run Latin hypercube design with 3 center points.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/designs/design_iter01_lhs_4d2a/design_matrix.csv",
    "outputs/studies/ivt_egfp_001/designs/design_iter01_lhs_4d2a/design_metadata.json"
  ],
  "artifact_hashes": {
    "design_matrix": "sha256:matrixhash",
    "design_metadata": "sha256:metadatahash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "design_id": "design_iter01_lhs_4d2a",
    "design_type": "latin_hypercube",
    "n_runs": 27,
    "diagnostics": {
      "n_factors": 4,
      "constraint_retention_fraction": 1.0
    }
  }
}
```

### 8.5 Side Effects

Writes:

```text
designs/<design_id>/design_matrix.csv
designs/<design_id>/design_metadata.json
study.json active_design_id
audit_log.jsonl
```

### 8.6 Validation and Errors

Errors:

```text
factor_space_not_found
unsupported_design_type
invalid_target_runs
run_count_exceeds_limit
constraints_infeasible
unsupported_mixed_level_fractional_factorial
missing_seed_for_randomized_design
```

Warnings:

```text
center_points_ignored_for_categorical_only_design
design_randomized
fractional_aliasing_present
lhs_constraint_rejections
```

## 9. Tool: `design_optimal_doe`

### 9.1 Purpose

Generate a candidate-set optimal or D-optimal design. Launch support includes candidate-set selection plus augmentation metadata validation; full locked-row iterative augmentation is paper-class scope.

### 9.2 Availability

```text
Launch required
```

### 9.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "optimality": "d_optimal",
    "iteration": 1,
    "target_runs": 12,
    "candidate_generation": {
      "method": "low_mid_high_grid",
      "levels_per_continuous_factor": 3
    },
    "model_terms": [
      "mg_ntp_ratio",
      "ntp_concentration",
      "dna_template",
      "t7_rnap",
      "mg_ntp_ratio:ntp_concentration",
      "dna_template:t7_rnap",
      "I(mg_ntp_ratio^2)",
      "I(ntp_concentration^2)"
    ],
    "augmentation": {
      "enabled": false,
      "locked_design_ids": [],
      "allow_repeats": false
    },
    "randomize": true
  },
  "options": {
    "seed": 20260420
  }
}
```

Required request fields:

```text
optimality
target_runs
model_terms
```

Allowed optimality values:

```text
d_optimal
candidate_set_optimal
```

Candidate generation methods:

```text
low_mid_high_grid
user_supplied_candidate_set
latin_hypercube_candidate_pool
full_grid
```

### 9.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated a 12-run D-optimal design for 8 requested terms.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/design_matrix.csv",
    "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/design_metadata.json",
    "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/candidate_set.metadata.json"
  ],
  "artifact_hashes": {
    "design_matrix": "sha256:matrixhash",
    "design_metadata": "sha256:metadatahash",
    "candidate_set": "sha256:candidatehash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "design_id": "design_iter01_dopt_7c2d",
    "n_runs": 12,
    "diagnostics": {
      "n_model_columns": 9,
      "model_matrix_rank": 9,
      "condition_number": 18.4,
      "logdet": 12.73,
      "terms_not_estimable": []
    }
  }
}
```

### 9.5 Side Effects

Writes:

```text
designs/<design_id>/design_matrix.csv
designs/<design_id>/design_metadata.json
designs/<design_id>/candidate_set.csv when retained
designs/<design_id>/candidate_set.metadata.json
study.json active_design_id
audit_log.jsonl
```

### 9.6 Validation and Errors

Errors:

```text
factor_space_not_found
invalid_model_term
unsupported_term_for_factor_type
target_runs_less_than_model_columns
candidate_set_empty
candidate_set_rank_deficient
constraints_infeasible
d_optimal_convergence_failed
augmentation_locked_design_not_found
```

Warnings:

```text
high_condition_number
terms_not_estimable
fallback_design_used
candidate_set_large_stored_as_hash_only
augmentation_cannot_make_full_model_estimable
```

### 9.7 Idempotency Notes

With identical candidate generation settings and seed, selected row order must be reproducible. Equivalent D-optimal designs may exist; the artifact must record selected candidate indices and criterion value.

## 10. Tool: `import_endpoint_observations`

### 10.1 Purpose

Import, validate, normalize, and persist endpoint experimental observations from CSV, JSON rows, or inline table data.

### 10.2 Availability

```text
Launch required
```

### 10.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "data": "outputs/studies/ivt_egfp_001/imports/observed_data.csv",
    "data_format": "csv",
    "table_id": "endpoint_obs_iter01",
    "design_id": "design_iter01_dopt_7c2d",
    "column_mapping": {
      "Mg:NTP": "mg_ntp_ratio",
      "NTP (mM)": "ntp_concentration",
      "Yield g/L": "mrna_yield",
      "dsRNA score": "dsrna_score"
    },
    "units": {
      "mrna_yield": "g/L",
      "dsrna_score": "score"
    },
    "replicate_policy": "preserve"
  },
  "options": {
    "strict_validation": true
  }
}
```

Required request fields:

```text
data
data_format
```

Allowed data formats:

```text
csv
json_rows
inline_rows
```

Allowed replicate policies:

```text
preserve
summarize_separately
reject_duplicates
```

### 10.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Imported 23 endpoint observation rows.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/observations/endpoint_observations.csv",
    "outputs/studies/ivt_egfp_001/observations/endpoint_observations.metadata.json"
  ],
  "artifact_hashes": {
    "endpoint_observations": "sha256:endpointhash",
    "endpoint_metadata": "sha256:metadatahash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "table_id": "endpoint_obs_iter01",
    "n_rows": 23,
    "response_columns": ["mrna_yield", "dsrna_score"],
    "missing_value_count": 0
  }
}
```

### 10.5 Side Effects

Writes:

```text
observations/endpoint_observations.csv
observations/endpoint_observations.metadata.json
audit_log.jsonl
```

### 10.6 Validation and Errors

Errors:

```text
input_file_not_found
unsupported_data_format
missing_required_columns
ambiguous_column_mapping
unknown_factor_column
unknown_response_column
invalid_numeric_value
unknown_categorical_level
unit_mismatch
duplicate_run_id_rejected
```

Warnings:

```text
missing_optional_units
missing_response_values
replicates_preserved
factor_values_differ_from_design
extra_columns_preserved_in_metadata
```

## 11. Tool: `import_time_resolved_observations`

### 11.1 Purpose

Import, validate, normalize, and persist long-format time-resolved assay observations. Optionally derive endpoint summaries.

### 11.2 Availability

```text
Launch required
```

### 11.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "data": "outputs/studies/ivt_egfp_001/imports/timecourse.csv",
    "data_format": "csv",
    "table_id": "timecourse_iter01",
    "column_mapping": {
      "Run": "run_id",
      "Time": "time",
      "Analyte": "analyte",
      "Value": "value"
    },
    "time_unit": "min",
    "analyte_units": {
      "mrna_concentration": "g/L",
      "atp_remaining": "mM"
    },
    "derive_endpoint_summary": true,
    "endpoint_summary_method": "final_observed",
    "analyte_response_mapping": {
      "mrna_concentration": "mrna_yield"
    }
  }
}
```

Required request fields:

```text
data
data_format
time_unit
```

Allowed endpoint summary methods:

```text
final_observed
max_observed
time_selected
plateau_mean
```

### 11.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Imported 276 time-resolved observations and derived endpoint summaries.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/observations/time_resolved_observations.csv",
    "outputs/studies/ivt_egfp_001/observations/time_resolved_observations.metadata.json",
    "outputs/studies/ivt_egfp_001/derived/endpoint_summary.json"
  ],
  "artifact_hashes": {
    "time_resolved_observations": "sha256:timehash",
    "endpoint_summary": "sha256:summaryhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "table_id": "timecourse_iter01",
    "n_rows": 276,
    "n_runs": 23,
    "analytes": ["mrna_concentration", "atp_remaining"],
    "endpoint_summary_created": true
  }
}
```

### 11.5 Side Effects

Writes:

```text
observations/time_resolved_observations.csv
observations/time_resolved_observations.metadata.json
derived/endpoint_summary.json when requested
audit_log.jsonl
```

### 11.6 Validation and Errors

Errors:

```text
input_file_not_found
unsupported_data_format
missing_time_column
missing_analyte_column
missing_value_column
invalid_time_value
invalid_analyte_value
duplicate_timepoint_without_replicate
unknown_run_id
invalid_endpoint_summary_method
```

Warnings:

```text
non_monotonic_time_order
insufficient_timepoints_for_curve
endpoint_summary_used_final_observed
plateau_not_detected
unmapped_analyte_preserved
```

## 12. Tool: `register_construct`

### 12.1 Purpose

Register or update mRNA construct metadata, sequence, nucleotide counts, molecular weight, modifications, and IVT-specific construct properties.

### 12.2 Availability

```text
Launch required
```

### 12.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "construct": {
      "construct_id": "egfp_995nt",
      "display_name": "eGFP mRNA",
      "construct_type": "mRNA",
      "sequence": null,
      "sequence_alphabet": "RNA",
      "nucleotide_counts": {
        "A": 300,
        "C": 220,
        "G": 240,
        "U": 235
      },
      "transcript_length": 995,
      "poly_a_tail_length": 45,
      "molecular_weight": {
        "value": 320000,
        "unit": "g/mol",
        "source": "user_input"
      },
      "modifications": []
    },
    "set_active": true
  }
}
```

Required request fields:

```text
construct
```

Required construct fields:

```text
construct_id
display_name
construct_type
transcript_length
sequence or nucleotide_counts
```

### 12.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Registered construct egfp_995nt.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/constructs.json"
  ],
  "artifact_hashes": {
    "constructs": "sha256:constructhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "construct_id": "egfp_995nt",
    "transcript_length": 995,
    "active": true
  }
}
```

### 12.5 Side Effects

Writes:

```text
constructs.json
study.json active_construct_id when set_active = true
audit_log.jsonl
```

### 12.6 Validation and Errors

Errors:

```text
invalid_construct_id
missing_sequence_and_counts
invalid_sequence_character
nucleotide_counts_do_not_sum_to_length
modified_nucleotide_missing_mass
invalid_molecular_weight
```

Warnings:

```text
dna_sequence_t_converted_to_u
molecular_weight_override_used
poly_a_tail_not_specified
construct_replaces_existing_definition
```

## 13. Tool: `calculate_theoretical_yield`

### 13.1 Purpose

Calculate limiting NTP, theoretical maximum yield, and relative yield for IVT runs when construct metadata and NTP concentrations are available.

### 13.2 Availability

```text
Launch required
```

### 13.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "construct_id": "egfp_995nt",
    "source_design_id": "design_iter01_dopt_7c2d",
    "source_observation_table_id": "endpoint_obs_iter01",
    "ntp_concentration_source": {
      "mode": "factor",
      "factor_name": "ntp_concentration",
      "assumption": "individual_equimolar_ntps"
    },
    "measured_yield_response": "mrna_yield",
    "output_response_names": {
      "theoretical_yield": "theoretical_yield",
      "relative_yield": "relative_yield"
    }
  }
}
```

Required request fields:

```text
construct_id
ntp_concentration_source
```

Allowed NTP concentration modes:

```text
factor
per_ntp_columns
constant_individual_concentration
inline_by_run
```

### 13.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Calculated theoretical yield for 23 runs.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/theoretical_yield.json"
  ],
  "artifact_hashes": {
    "theoretical_yield": "sha256:yieldhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "construct_id": "egfp_995nt",
    "n_results": 23,
    "relative_yield_calculated": true
  }
}
```

### 13.5 Side Effects

Writes:

```text
derived/theoretical_yield.json
audit_log.jsonl
```

May update dashboard payload only through `generate_dashboard_payload`, not directly.

### 13.6 Validation and Errors

Errors:

```text
construct_not_found
missing_nucleotide_counts
missing_ntp_concentration
invalid_ntp_concentration
missing_molecular_weight
measured_yield_response_not_found
```

Warnings:

```text
relative_yield_not_calculated_missing_measured_yield
relative_yield_above_100_percent
molecular_weight_override_used
modified_nucleotides_require_user_mass
```

## 14. Tool: `fit_response_surface`

### 14.1 Purpose

Fit deterministic response-surface models for measured or derived responses using endpoint observations and requested model terms.

### 14.2 Availability

```text
Launch required
```

### 14.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "observation_table_id": "endpoint_obs_iter01",
    "design_id": "design_iter01_dopt_7c2d",
    "responses": ["mrna_yield", "dsrna_score", "relative_yield"],
    "model_terms": [
      "mg_ntp_ratio",
      "ntp_concentration",
      "dna_template",
      "t7_rnap",
      "mg_ntp_ratio:ntp_concentration",
      "I(ntp_concentration^2)"
    ],
    "transforms": {
      "dna_template": "none",
      "t7_rnap": "none"
    },
    "include_blocks": true,
    "robust_errors": true,
    "validation": {
      "method": "leave_one_out"
    },
    "heredity": "weak"
  }
}
```

Required request fields:

```text
observation_table_id or data
responses
model_terms
```

Allowed validation methods:

```text
none
leave_one_out
kfold
holdout
```

Allowed heredity modes:

```text
none
weak
strong
```

### 14.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success_with_warnings",
  "summary": "Fit 3 response-surface models. One model has weak predictive score.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/models/fit_yield_dsrna_iter01_31ad/model_fit.json",
    "outputs/studies/ivt_egfp_001/models/fit_yield_dsrna_iter01_31ad/residuals.csv",
    "outputs/studies/ivt_egfp_001/models/fit_yield_dsrna_iter01_31ad/predictions.csv"
  ],
  "artifact_hashes": {
    "model_fit": "sha256:fithash"
  },
  "warnings": [
    {
      "code": "weak_predictive_score",
      "severity": "warning",
      "message": "Model for dsrna_score has Q2 below threshold.",
      "field": "models[1].metrics.q2",
      "details": {
        "q2": 0.42
      }
    }
  ],
  "errors": [],
  "structured_content": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "models": [
      {
        "response": "mrna_yield",
        "r2": 0.97,
        "q2": 0.86,
        "rank": 7
      }
    ]
  }
}
```

### 14.5 Side Effects

Writes:

```text
models/<fit_id>/model_fit.json
models/<fit_id>/residuals.csv
models/<fit_id>/predictions.csv
study.json active_fit_id
audit_log.jsonl
```

### 14.6 Validation and Errors

Errors:

```text
observations_not_found
response_not_found
invalid_model_term
unsupported_term_for_factor_type
insufficient_rows_for_model
rank_deficient_model
invalid_validation_method
missing_response_values
```

Warnings:

```text
high_condition_number
weak_predictive_score
lack_of_fit_unavailable
large_residual_detected
high_leverage_row_detected
robust_errors_unavailable
terms_dropped_for_estimability
```

### 14.7 Downstream Blocking Rules

If model status is `rank_deficient`, downstream optimization tools must refuse to use the model unless the user explicitly requests an override and the downstream tool supports it.

## 15. Tool: `analyze_effects`

### 15.1 Purpose

Calculate effect summaries and plot-ready payloads from fitted response-surface models.

### 15.2 Availability

```text
Launch required
```

### 15.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "responses": ["mrna_yield", "dsrna_score"],
    "effect_type": "all",
    "confidence_level": 0.95,
    "prediction_grid": {
      "points_per_factor": 50,
      "hold_strategy": "center",
      "hold_values": {}
    },
    "contours": [
      {
        "response": "mrna_yield",
        "factor_x": "mg_ntp_ratio",
        "factor_y": "ntp_concentration",
        "hold_strategy": "center"
      }
    ]
  }
}
```

Required request fields:

```text
fit_id
```

Allowed effect types:

```text
main_effects
interactions
standardized
all
```

### 15.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated effects and plot payloads for 2 responses.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/effects.json",
    "outputs/studies/ivt_egfp_001/derived/prediction_grids.json"
  ],
  "artifact_hashes": {
    "effects": "sha256:effectshash",
    "prediction_grids": "sha256:gridhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "responses": ["mrna_yield", "dsrna_score"],
    "plot_payloads": ["pareto", "factor_response", "contours"]
  }
}
```

### 15.5 Side Effects

Writes:

```text
derived/effects.json
derived/prediction_grids.json when grids requested
audit_log.jsonl
```

### 15.6 Validation and Errors

Errors:

```text
model_fit_not_found
response_not_in_fit
invalid_effect_type
invalid_hold_strategy
hold_value_outside_factor_space
contour_factor_not_found
prediction_grid_too_large
```

Warnings:

```text
statistical_threshold_unavailable
prediction_intervals_unavailable
extrapolation_mask_applied
constraint_mask_applied
weak_model_effects_ranked_by_magnitude_only
```

## 16. Tool: `calculate_cogs_impact`

### 16.1 Purpose

Calculate optional direct-input component costs, condition costs, and cost efficiency. This tool must not invent, fetch, infer, or default reagent prices.

### 16.2 Availability

```text
Launch required
```

### 16.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "component_costs": [
      {
        "component_id": "comp_t7_rnap",
        "component_name": "T7 RNAP",
        "unit_cost": 4.2,
        "currency": "EUR",
        "cost_basis_unit": "EUR/U",
        "factor_mapping": "t7_rnap",
        "amount_unit": "U",
        "source": "user_input"
      }
    ],
    "basis": {
      "batch_volume": {
        "value": 0.05,
        "unit": "L"
      },
      "product_mass_source": "measured_then_predicted",
      "yield_response": "mrna_yield"
    },
    "conditions": {
      "mode": "design_or_observed_rows",
      "design_id": "design_iter01_dopt_7c2d",
      "fit_id": "fit_yield_dsrna_iter01_31ad"
    },
    "cost_efficiency_metric": "mass_per_currency",
    "baseline_run_id": "run_reference"
  }
}
```

Required request fields:

```text
component_costs
basis
conditions
```

Allowed condition modes:

```text
design_or_observed_rows
scenarios
recommendations
inline_conditions
```

Allowed cost efficiency metrics:

```text
mass_per_currency
currency_per_mass
```

### 16.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Calculated cost efficiency for 23 conditions using user-provided component costs.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/economics.json"
  ],
  "artifact_hashes": {
    "economics": "sha256:economicshash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "economics_status": "calculated",
    "n_conditions": 23,
    "currency": "EUR",
    "cost_inputs_hash": "sha256:costhash"
  }
}
```

If component costs are absent:

```json
{
  "status": "skipped",
  "summary": "Cost efficiency was not calculated because component costs were not supplied.",
  "structured_content": {
    "economics_status": "skipped_missing_component_costs"
  }
}
```

### 16.5 Side Effects

Writes when calculated:

```text
derived/economics.json
audit_log.jsonl
```

When skipped:

```text
audit_log.jsonl
```

### 16.6 Validation and Errors

Errors:

```text
missing_component_costs_for_requested_economics
component_cost_missing_unit_cost
component_cost_missing_currency
component_cost_missing_basis
mixed_currencies_without_conversion
unknown_factor_mapping
product_mass_unavailable
batch_volume_required
invalid_cost_efficiency_metric
```

Warnings:

```text
factor_has_no_cost_mapping
fixed_cost_applied_to_all_conditions
predicted_product_mass_used
baseline_missing_for_improvement_claim
sensitivity_partial_missing_price_range
```

### 16.7 Prohibited Behavior

This tool must return `failed_validation` if the request asks it to fetch, infer, or default reagent prices.

## 17. Tool: `suggest_next_experiment`

### 17.1 Purpose

Recommend next experiments using desirability, D-optimal augmentation, expected improvement, or hybrid scoring.

### 17.2 Availability

```text
Launch required
```

### 17.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "objectives": [
      {
        "response": "mrna_yield",
        "goal": "maximize",
        "weight": 1.0,
        "target": 11.0
      },
      {
        "response": "dsrna_score",
        "goal": "upper_threshold",
        "weight": 2.0,
        "upper": 3.0,
        "hard_constraint": true
      }
    ],
    "strategy": "hybrid",
    "n_recommendations": 5,
    "candidate_generation": {
      "method": "latin_hypercube_candidate_pool",
      "n_candidates": 2000
    },
    "exploration_weight": 0.2,
    "avoid_duplicates": true,
    "include_economics": "if_available"
  },
  "options": {
    "seed": 20260420
  }
}
```

Required request fields:

```text
fit_id
objectives
n_recommendations
```

Allowed strategies:

```text
desirability
d_optimal_augment
expected_improvement
hybrid
```

Allowed economics modes:

```text
never
if_available
require_calculated
```

### 17.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated 5 next-experiment recommendations.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/recommendations.json"
  ],
  "artifact_hashes": {
    "recommendations": "sha256:recommendationshash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "recommendation_set_id": "recs_iter02_001",
    "n_recommendations": 5,
    "strategy": "hybrid"
  }
}
```

### 17.5 Side Effects

Writes:

```text
derived/recommendations.json
audit_log.jsonl
```

### 17.6 Validation and Errors

Errors:

```text
model_fit_not_found
rank_deficient_model_blocks_recommendations
objective_response_not_found
invalid_objective_goal
candidate_set_empty
economics_required_but_unavailable
all_candidates_infeasible
```

Warnings:

```text
economics_not_included_missing_costs
recommendations_near_observed_boundary
high_uncertainty_recommendation
duplicate_candidates_removed
weak_model_used_for_ranking
```

## 18. Tool: `plan_verification_runs`

### 18.1 Purpose

Plan verification experiments around predicted optima, design-space boundaries, corners, center points, and model-risk regions.

### 18.2 Availability

```text
Launch required
```

### 18.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "recommendation_set_id": "recs_iter02_001",
    "design_space_artifact": null,
    "verification_types": [
      "predicted_optimum",
      "design_space_corner",
      "quality_boundary_probe"
    ],
    "n_runs": 7,
    "quality_thresholds": [
      {
        "response": "dsrna_score",
        "operator": "<",
        "value": 3,
        "unit": "score"
      }
    ],
    "include_center_point": true
  }
}
```

Required request fields:

```text
fit_id
verification_types
n_runs
```

Allowed verification types:

```text
predicted_optimum
design_space_corner
design_space_edge
quality_boundary_probe
center_point
replicate_control
model_disagreement_probe
```

### 18.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success_with_warnings",
  "summary": "Planned 7 verification runs. Design-space probability map was unavailable, so boundary probes used model predictions and thresholds.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/verification_plan.json"
  ],
  "artifact_hashes": {
    "verification_plan": "sha256:verifyhash"
  },
  "warnings": [
    {
      "code": "design_space_probability_unavailable",
      "severity": "warning",
      "message": "Verification boundary probes used model predictions because probability map was not available.",
      "field": "request.design_space_artifact",
      "details": {}
    }
  ],
  "errors": [],
  "structured_content": {
    "verification_plan_id": "verify_iter01_001",
    "n_runs": 7
  }
}
```

### 18.5 Side Effects

Writes:

```text
derived/verification_plan.json
audit_log.jsonl
```

### 18.6 Validation and Errors

Errors:

```text
model_fit_not_found
invalid_verification_type
n_runs_too_small
quality_threshold_required_for_boundary_probe
all_verification_candidates_infeasible
```

Warnings:

```text
design_space_probability_unavailable
prediction_intervals_unavailable
duplicate_verification_points_removed
weak_model_used_for_verification_planning
```

## 19. Tool: `generate_dashboard_payload`

### 19.1 Purpose

Collect current study artifacts into a single versioned `dashboard_payload.json` read model for the React dashboard.

### 19.2 Availability

```text
Launch required
```

### 19.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "include": [
      "factor_space",
      "responses",
      "design_matrix",
      "observations",
      "time_courses",
      "constructs",
      "theoretical_yield",
      "model_fit",
      "effects",
      "economics",
      "recommendations",
      "verification",
      "diagnostics",
      "audit"
    ],
    "payload_version": "1.0.0",
    "active_artifacts": {
      "design_id": "design_iter01_dopt_7c2d",
      "fit_id": "fit_yield_dsrna_iter01_31ad"
    }
  }
}
```

Required request fields:

```text
none
```

If `include` is omitted, the tool includes all known launch sections with availability states.

### 19.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Generated dashboard payload for study ivt_egfp_001.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/dashboard_payload.json"
  ],
  "artifact_hashes": {
    "dashboard_payload": "sha256:payloadhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "payload_path": "outputs/studies/ivt_egfp_001/dashboard_payload.json",
    "payload_hash": "sha256:payloadhash",
    "available_sections": ["experiment_matrix", "effects", "diagnostics"],
    "unavailable_sections": ["economics"]
  }
}
```

### 19.5 Side Effects

Writes:

```text
dashboard_payload.json
audit_log.jsonl
```

### 19.6 Validation and Errors

Errors:

```text
study_not_found
payload_schema_validation_failed
artifact_referenced_but_missing
artifact_hash_mismatch
```

Warnings:

```text
economics_unavailable_missing_costs
model_fit_unavailable
effects_unavailable
time_courses_unavailable
design_space_probability_unavailable
```

### 19.7 Dashboard Availability Rules

Missing optional artifacts must create section states:

```text
unavailable_missing_input
unavailable_not_run
unavailable_failed_validation
unavailable_unsupported
```

They must not cause payload generation failure unless a required core artifact is missing.

## 20. Tool: `launch_dashboard_preview`

### 20.1 Purpose

Return the local dashboard URL for the study and optionally start or check the local dashboard dev server.

### 20.2 Availability

```text
Launch required
```

### 20.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "host": "127.0.0.1",
    "port": 5173,
    "mode": "return_url_only",
    "reuse_existing": true,
    "route": "/studies/ivt_egfp_001"
  }
}
```

Allowed modes:

```text
return_url_only
check_existing_server
start_dev_server
static_file
```

Launch default:

```text
return_url_only
```

### 20.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Dashboard preview URL is http://127.0.0.1:5173/studies/ivt_egfp_001.",
  "artifact_paths": [],
  "artifact_hashes": {},
  "warnings": [],
  "errors": [],
  "structured_content": {
    "url": "http://127.0.0.1:5173/studies/ivt_egfp_001",
    "server_status": "not_started",
    "instructions": "Start the dashboard dev server, then open the URL in the Codex in-app browser."
  }
}
```

Allowed server statuses:

```text
already_running
started
not_started
failed
static_file_ready
```

### 20.5 Side Effects

Default mode:

```text
audit_log.jsonl only
```

`start_dev_server` mode may start a local process and must return PID when available.

### 20.6 Validation and Errors

Errors:

```text
dashboard_payload_not_found
invalid_host
invalid_port
dashboard_app_not_found
dev_server_start_failed
```

Warnings:

```text
dashboard_server_not_started
port_in_use
auth_not_supported_in_preview
static_preview_less_interactive
```

## 21. Tool: `estimate_design_space_probability`

### 21.1 Purpose

Estimate probability of quality failure over a candidate grid using Monte Carlo factor perturbation and model predictions.

### 21.2 Availability

```text
Post-launch / paper-class expansion
Schema foundation required at launch
```

### 21.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "quality_threshold": {
      "response": "dsrna_score",
      "operator": "<",
      "value": 3,
      "unit": "score"
    },
    "grid": {
      "factor_x": "mg_ntp_ratio",
      "factor_y": "ntp_concentration",
      "points_per_axis": 50,
      "hold_strategy": "center",
      "hold_values": {
        "dna_template": 55,
        "t7_rnap": 8.5
      }
    },
    "simulation": {
      "n_simulations": 10000,
      "factor_noise_percent": 5,
      "noise_distribution": "normal",
      "include_prediction_uncertainty": false,
      "failure_limit": 0.01
    }
  },
  "options": {
    "seed": 20260420
  }
}
```

### 21.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Estimated design-space probability for dsRNA score threshold.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/design_space_probability.json"
  ],
  "artifact_hashes": {
    "design_space_probability": "sha256:dsphash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "status": "calculated",
    "quality_response": "dsrna_score",
    "failure_limit": 0.01,
    "n_grid_points": 2500
  }
}
```

### 21.5 Validation and Errors

Errors:

```text
model_fit_not_found
quality_response_not_in_fit
invalid_quality_threshold
rank_deficient_model
invalid_simulation_settings
grid_too_large
prediction_uncertainty_unavailable
```

Warnings:

```text
valid_simulations_below_threshold
boundary_clipping_applied
weak_model_used_for_design_space
prediction_uncertainty_not_included
```

## 22. Tool: `compare_verification_results`

### 22.1 Purpose

Compare observed verification results against model predictions and prediction intervals.

### 22.2 Availability

```text
Post-launch / paper-class expansion
```

### 22.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "verification_plan_id": "verify_iter01_001",
    "observation_table_id": "endpoint_obs_verification",
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "responses": ["mrna_yield", "dsrna_score"],
    "interval_level": 0.95
  }
}
```

### 22.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Compared 7 verification runs against prediction intervals.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/verification_results.json"
  ],
  "artifact_hashes": {
    "verification_results": "sha256:verificationresultshash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "n_runs": 7,
    "n_within_interval": 6,
    "n_outside_interval": 1
  }
}
```

### 22.5 Validation and Errors

Errors:

```text
verification_plan_not_found
observations_not_found
model_fit_not_found
prediction_interval_unavailable
verification_run_id_mismatch
```

Warnings:

```text
response_missing_for_some_runs
observation_outside_prediction_interval
verification_result_challenges_model
```

## 23. Tool: `transfer_construct_model`

### 23.1 Purpose

Apply a declared construct-transfer method to compare or predict behavior across mRNA constructs using sequence length, molecular weight, nucleotide composition, and molarity adjustment assumptions.

### 23.2 Availability

```text
Post-launch / paper-class expansion
Launch foundation: construct metadata only
```

### 23.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "reference_construct_id": "egfp_995nt",
    "target_construct_id": "mfix_3969nt",
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "transfer_mode": "length_time_scaled",
    "molarity_adjustment": true,
    "time_scaling": {
      "mode": "length_ratio"
    },
    "validation_observation_table_id": "mfix_validation_timecourse"
  }
}
```

Allowed transfer modes:

```text
molarity_only
length_time_scaled
user_supplied_scaling
```

### 23.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success_with_warnings",
  "summary": "Generated construct-transfer predictions with length-time scaling assumptions.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/derived/construct_transfer.json"
  ],
  "artifact_hashes": {
    "construct_transfer": "sha256:transferhash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "reference_construct_id": "egfp_995nt",
    "target_construct_id": "mfix_3969nt",
    "transfer_mode": "length_time_scaled"
  }
}
```

### 23.5 Validation and Errors

Errors:

```text
reference_construct_not_found
target_construct_not_found
model_fit_not_found
missing_molecular_weight_for_molarity_adjustment
invalid_transfer_mode
user_scaling_required
```

Warnings:

```text
construct_length_differs_more_than_2x
nucleotide_composition_differs_materially
modified_nucleotides_differ
reaction_conditions_differ
transfer_predictions_unvalidated
```

## 24. Tool: `analyze_counterion_doe`

### 24.1 Purpose

Analyze a mixed categorical/continuous DOE for magnesium counterion effects and interactions with Mg:NTP ratio.

### 24.2 Availability

```text
Post-launch / paper-class expansion
Can be implemented through design_optimal_doe + fit_response_surface if no specialized behavior is needed
```

### 24.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "observation_table_id": "counterion_obs",
    "continuous_factor": "mg_ntp_ratio",
    "categorical_factor": "mg_counterion",
    "responses": ["mrna_yield", "dsrna_score"],
    "model_terms": [
      "mg_ntp_ratio",
      "mg_counterion",
      "mg_ntp_ratio:mg_counterion"
    ]
  }
}
```

### 24.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Analyzed counterion DOE for 2 responses.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/models/fit_counterion_001/model_fit.json",
    "outputs/studies/ivt_egfp_001/derived/effects.json"
  ],
  "artifact_hashes": {},
  "warnings": [],
  "errors": [],
  "structured_content": {
    "fit_id": "fit_counterion_001"
  }
}
```

### 24.5 Validation and Errors

Errors:

```text
categorical_factor_not_found
continuous_factor_not_found
insufficient_categorical_replication
response_not_found
model_fit_failed
```

Warnings:

```text
sparse_counterion_level
interaction_not_estimable
weak_model_used_for_counterion_comparison
```

## 25. Tool: `fit_time_resolved_response_model`

### 25.1 Purpose

Fit richer time-resolved response models beyond launch endpoint summaries.

### 25.2 Availability

```text
Post-launch / paper-class expansion
Launch behavior is import and plot time-resolved data plus endpoint summaries
```

### 25.3 Input

```json
{
  "study_id": "ivt_egfp_001",
  "request": {
    "time_resolved_table_id": "timecourse_iter01",
    "response_analytes": ["mrna_concentration"],
    "model_type": "time_as_factor_mlr",
    "time_transform": "log",
    "factor_terms": [
      "mg_ntp_ratio",
      "ntp_concentration",
      "dna_template",
      "t7_rnap"
    ],
    "include_time_interactions": true
  }
}
```

Allowed model types:

```text
time_as_factor_mlr
endpoint_summary_series
nonlinear_kinetic_model
```

### 25.4 Output

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "status": "success",
  "summary": "Fit time-resolved model for mRNA concentration.",
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/models/fit_timecourse_001/model_fit.json"
  ],
  "artifact_hashes": {
    "time_model_fit": "sha256:timefithash"
  },
  "warnings": [],
  "errors": [],
  "structured_content": {
    "fit_id": "fit_timecourse_001",
    "model_type": "time_as_factor_mlr"
  }
}
```

### 25.5 Validation and Errors

Errors:

```text
time_resolved_table_not_found
analyte_not_found
invalid_time_transform
insufficient_timepoints
unsupported_time_model_type
model_fit_failed
```

Warnings:

```text
non_monotonic_trajectory
time_model_extrapolation_risk
plateau_not_detected
```

## 26. Canonical Launch Workflows

### 26.1 New IVT/QbD DOE

Tool sequence:

```text
1. create_or_update_study
2. validate_factor_space
3. register_construct, if sequence/composition is supplied
4. design_optimal_doe
5. generate_dashboard_payload
6. launch_dashboard_preview
```

Required outcome:

```text
- factor_space.json
- responses.json
- design_matrix.csv
- design_metadata.json
- dashboard_payload.json
- audit_log.jsonl entries for every tool call
```

### 26.2 Fit Observed IVT Data

Tool sequence:

```text
1. import_endpoint_observations
2. import_time_resolved_observations, if kinetic data exists
3. calculate_theoretical_yield, if sequence/composition exists
4. fit_response_surface
5. analyze_effects
6. generate_dashboard_payload
7. launch_dashboard_preview
```

Required outcome:

```text
- normalized observations
- theoretical_yield.json when inputs exist
- model_fit.json
- residuals.csv
- effects.json
- dashboard_payload.json
```

### 26.3 Optional Cost-Efficiency Analysis

Tool sequence:

```text
1. calculate_cogs_impact
2. generate_dashboard_payload
3. launch_dashboard_preview
```

Rules:

```text
- If component_costs is absent, calculate_cogs_impact returns skipped.
- Dashboard payload must show economics unavailable state.
- Codex must not ask the tool to infer prices.
```

### 26.4 Next Experiments and Verification

Tool sequence:

```text
1. suggest_next_experiment
2. plan_verification_runs
3. generate_dashboard_payload
4. launch_dashboard_preview
```

Rules:

```text
- Recommendations require a usable model fit.
- Verification planning can proceed without a Monte Carlo design-space map, but must warn.
- Verification output is a plan, not evidence of model validation.
```

## 27. Tool Authorization and Safety

### 27.1 Filesystem Access

Tools may write only under:

```text
outputs/studies/<study_id>/
logs/
```

Tools may read:

```text
- study artifacts
- user-specified input paths inside the workspace
- shared schema files
- example fixtures
```

Tools must reject:

```text
- paths outside the workspace unless explicit local-only override is configured
- path traversal segments
- attempts to overwrite source planning documents
```

### 27.2 Network Access

Launch tools must not require network access.

Network-prohibited operations:

```text
- external price lookup
- uploading assay data
- pulling model definitions from remote services
- sending dashboard payloads to hosted services
```

### 27.3 Sensitive Data

Tools must redact or avoid logging:

```text
api_key
password
token
secret
credential
private_key
```

Cost tables are treated as sensitive business data and remain local.

## 28. API Versioning

### 28.1 Tool Version

Every tool exposes:

```text
tool_name
tool_version
method_version
input_schema_version
output_schema_version
```

### 28.2 Compatibility Rules

Patch version:

```text
- bug fixes that do not alter schema or scientific semantics
```

Minor version:

```text
- optional fields added
- new warning codes added
- new unsupported enum value introduced behind validation
```

Major version:

```text
- required fields changed
- output semantics changed
- scientific method changed materially
```

### 28.3 Deprecation Rules

Deprecated tools or fields must:

```text
- remain documented for at least one minor version
- emit deprecation warnings
- identify replacement tool or field
- preserve existing artifact readability
```

## 29. Required Tool Tests

### 29.1 Envelope Tests

```text
- Every tool accepts common envelope.
- Every tool returns common output envelope.
- Every failed_validation response includes structured errors.
- Every warning includes code, severity, message, and field when applicable.
- Every tool writes audit log entry.
```

### 29.2 Tool-Specific Launch Tests

```text
create_or_update_study:
  creates study.json and study directory.

validate_factor_space:
  rejects invalid continuous bounds.
  rejects duplicate normalized names.
  persists factor_space.json and responses.json.

design_doe:
  generates full factorial expected run count.
  reports unsupported mixed-level fractional design.

design_optimal_doe:
  produces full-rank D-optimal design for IVT four-factor fixture.
  fails when target_runs < model columns.
  validates augmentation metadata and never changes locked rows.

import_endpoint_observations:
  validates required columns and units.
  preserves replicates.

import_time_resolved_observations:
  validates long-format timecourse data.
  derives endpoint summary with final_observed.

register_construct:
  rejects nucleotide counts that do not sum to transcript length.

calculate_theoretical_yield:
  calculates limiting NTP and relative yield fixture.

fit_response_surface:
  detects rank-deficient model.
  writes model_fit.json, residuals.csv, and predictions.csv.

analyze_effects:
  writes Pareto and factor-response payloads.

calculate_cogs_impact:
  skips without component costs.
  rejects missing currency.
  calculates cost efficiency from user-provided costs.

suggest_next_experiment:
  generates ranked recommendations with rationale type.

plan_verification_runs:
  generates predicted optimum and boundary run plans.

generate_dashboard_payload:
  validates payload and includes unavailable economics state.

launch_dashboard_preview:
  returns stable localhost URL.
```

### 29.3 Paper-Class Expansion Tests

```text
estimate_design_space_probability:
  Monte Carlo output is reproducible with seed.

compare_verification_results:
  identifies observed results inside and outside prediction intervals.

transfer_construct_model:
  warns when construct length differs by more than 2x.

analyze_counterion_doe:
  detects insufficient categorical replication.

fit_time_resolved_response_model:
  rejects insufficient time points.
```

## 30. Required Error Code Registry

Launch error codes:

```text
ambiguous_column_mapping
all_candidates_infeasible
artifact_hash_mismatch
batch_volume_required
candidate_set_empty
candidate_set_rank_deficient
component_cost_missing_basis
component_cost_missing_currency
component_cost_missing_unit_cost
construct_not_found
constraints_infeasible
d_optimal_convergence_failed
dashboard_app_not_found
dashboard_payload_not_found
duplicate_factor_name
duplicate_response_name
duplicate_run_id_rejected
economics_required_but_unavailable
factor_response_name_collision
factor_space_not_found
input_file_not_found
insufficient_rows_for_model
invalid_categorical_levels
invalid_constraint_expression
invalid_cost_efficiency_metric
invalid_factor_bounds
invalid_factor_kind
invalid_model_term
invalid_numeric_value
invalid_study_id
invalid_target_runs
invalid_threshold
invalid_transform_for_bounds
invalid_units
missing_component_costs_for_requested_economics
missing_factors
missing_molecular_weight
missing_ntp_concentration
missing_required_columns
missing_response_goal
missing_responses
model_fit_not_found
mixed_currencies_without_conversion
nucleotide_counts_do_not_sum_to_length
observations_not_found
payload_schema_validation_failed
product_mass_unavailable
rank_deficient_model
rank_deficient_model_blocks_recommendations
response_not_found
run_count_exceeds_limit
study_exists
study_not_found
target_runs_less_than_model_columns
unknown_categorical_level
unknown_factor_column
unknown_factor_mapping
unknown_response_column
unsupported_data_format
unsupported_design_type
unsupported_term_for_factor_type
unit_mismatch
```

## 31. Required Warning Code Registry

Launch warning codes:

```text
active_construct_missing
baseline_missing_for_improvement_claim
candidate_set_large_stored_as_hash_only
center_points_ignored_for_categorical_only_design
dashboard_server_not_started
design_randomized
design_space_probability_unavailable
duplicate_candidates_removed
duplicate_verification_points_removed
economics_not_included_missing_costs
economics_response_unavailable_until_costs_supplied
economics_unavailable_missing_costs
endpoint_summary_used_final_observed
extrapolation_mask_applied
factor_has_no_cost_mapping
factor_values_differ_from_design
factor_with_single_level_treated_as_fixed
fallback_design_used
fixed_cost_applied_to_all_conditions
fractional_aliasing_present
high_condition_number
high_leverage_row_detected
high_uncertainty_recommendation
lack_of_fit_unavailable
large_residual_detected
lhs_constraint_rejections
missing_optional_units
missing_response_values
model_fit_unavailable
molecular_weight_override_used
non_monotonic_time_order
payload_section_unavailable
plateau_not_detected
predicted_product_mass_used
prediction_intervals_unavailable
relative_yield_above_100_percent
replicates_preserved
response_weight_missing_defaulted
robust_errors_unavailable
statistical_threshold_unavailable
terms_dropped_for_estimability
terms_not_estimable
time_courses_unavailable
weak_model_used_for_ranking
weak_model_used_for_verification_planning
weak_predictive_score
```

## 32. Open API Decisions Resolved

1. `design_optimal_doe` is a separate launch tool rather than an overloaded mode of `design_doe`.
2. Endpoint and time-resolved imports are separate tools.
3. Construct registration is separate from theoretical-yield calculation.
4. Cost efficiency uses `calculate_cogs_impact`, but the tool skips cleanly when costs are absent.
5. Dashboard generation is explicit and never implicit inside analytical tools.
6. Dashboard preview URL generation is separate from payload generation.
7. Monte Carlo design-space probability is post-launch but has a defined tool contract.
8. Verification planning is launch required; verification result comparison is post-launch.
9. Time-resolved import is launch required; richer time-resolved model fitting is post-launch.
10. All tools use one common envelope and audit behavior.
