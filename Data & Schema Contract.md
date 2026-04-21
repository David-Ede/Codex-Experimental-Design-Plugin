# Data & Schema Contract: Codex Scientific Toolchain

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Scientific Methods Spec.md
- Canonical Build Contract.md
```

## 1. Purpose

This document defines the canonical data contracts for the Codex Scientific Toolchain. It is the shared agreement between:

```text
- Codex skill workflows
- Python MCP tools
- scientific engine modules
- persisted study artifacts
- React dashboard payloads
- validation tests
```

The goal is to prevent drift between tool inputs, tool outputs, stored artifacts, and dashboard rendering. Every scientific object must be structured, versioned, validated, traceable, and reproducible.

## 2. Contract Principles

1. JSON is the canonical artifact format unless tabular CSV is explicitly required.
2. CSV is allowed for human-editable matrices and observation tables, but every CSV must have a matching metadata JSON artifact.
3. Every persisted artifact includes schema version, method version, generated timestamp, input hash, artifact hash, warnings, and units.
4. Dashboard data flows through one versioned `dashboard_payload.json`.
5. MCP tools may return summaries, but persisted artifacts are the durable source of truth.
6. Missing optional inputs create explicit unavailable states, not absent fields with ambiguous meaning.
7. Cost fields are accepted only from direct user input; no schema may imply fetched or default reagent prices.
8. Units must be explicit for dimensional values.
9. Internal identifiers use stable snake_case. Display labels preserve user terminology.
10. Schema changes require a version bump and migration note.

## 3. File and Directory Contract

### 3.1 Study Directory Layout

Every study persists under:

```text
outputs/studies/<study_id>/
```

Required launch layout:

```text
outputs/studies/<study_id>/
  study.json
  factor_space.json
  responses.json
  constructs.json
  imports/
    <source_file_name>
  designs/
    <design_id>/
      design_matrix.csv
      design_metadata.json
  observations/
    endpoint_observations.csv
    endpoint_observations.metadata.json
    time_resolved_observations.csv
    time_resolved_observations.metadata.json
  models/
    <fit_id>/
      model_fit.json
      residuals.csv
      predictions.csv
  derived/
    endpoint_summary.json
    theoretical_yield.json
    effects.json
    prediction_grids.json
    economics.json
    design_space_probability.json
    recommendations.json
    verification_plan.json
  dashboard_payload.json
  audit_log.jsonl
```

Files are created only when relevant. For example, `economics.json` is absent until component costs are supplied, while dashboard payload must still include an economics availability state.

### 3.2 Artifact Naming Rules

```text
- JSON artifacts use snake_case filenames.
- CSV artifacts use snake_case filenames.
- Design-specific folders use design_id.
- Model-specific folders use fit_id.
- A new analytical run creates a new run_id and audit log entry.
- Recomputed artifacts may replace latest canonical files only if prior versions are still referenced in audit history or archival run folders.
```

### 3.3 Path References

All artifact references inside JSON use workspace-relative paths:

```json
"artifact_path": "outputs/studies/ivt_egfp_001/factor_space.json"
```

Absolute paths are allowed in transient MCP responses but must not be stored in portable artifacts unless explicitly marked as local-only.

## 4. IDs, Versions, and Timestamps

### 4.1 Identifier Formats

Identifiers are lowercase snake_case plus short stable suffixes when needed.

```text
study_id:         ivt_egfp_001
run_id:           run_20260420_120501_a8f3
design_id:        design_iter01_dopt_7c2d
fit_id:           fit_yield_dsrna_iter01_31ad
artifact_id:      artifact_factor_space_1b91
construct_id:     egfp_995nt
component_id:     comp_t7_rnap
```

Validation:

```text
- IDs must match ^[a-z][a-z0-9_]*[a-z0-9]$.
- IDs must be unique within their scope.
- User-facing display names are separate from IDs.
```

### 4.2 Version Fields

Every artifact includes:

```json
{
  "schema_version": "1.0.0",
  "method_version": "1.0.0",
  "tool_version": "0.1.0"
}
```

Versioning rules:

```text
- schema_version changes when fields, requiredness, or semantics change.
- method_version changes when scientific calculation behavior changes.
- tool_version changes when implementation changes without schema or method changes.
```

### 4.3 Timestamps

Timestamps use ISO 8601 UTC:

```json
"generated_at": "2026-04-20T19:05:01Z"
```

Rules:

```text
- Store UTC only.
- Dashboard may display local time, but payload remains UTC.
- Date-only values are not accepted for generated_at.
```

### 4.4 Hashes

Hashes use SHA-256 hex strings.

```json
"input_hash": "sha256:4b2f...",
"artifact_hash": "sha256:93aa..."
```

Hash rules:

```text
- Hash canonical JSON with sorted keys and normalized numeric representation.
- Hash CSV after normalizing line endings to LF.
- Include method settings and random seeds in input hashes.
- Do not include artifact_hash inside the content being hashed.
```

## 5. Common Schema Fragments

### 5.1 Artifact Metadata

Every JSON artifact must include `artifact_metadata`.

```json
{
  "artifact_metadata": {
    "artifact_id": "artifact_factor_space_1b91",
    "artifact_type": "factor_space",
    "study_id": "ivt_egfp_001",
    "run_id": "run_20260420_120501_a8f3",
    "schema_version": "1.0.0",
    "method_version": "1.0.0",
    "tool_name": "validate_factor_space",
    "tool_version": "0.1.0",
    "generated_at": "2026-04-20T19:05:01Z",
    "input_hash": "sha256:inputhash",
    "artifact_hash": "sha256:artifacthash",
    "warnings": []
  }
}
```

Required fields:

```text
artifact_id
artifact_type
study_id
run_id
schema_version
method_version
tool_name
tool_version
generated_at
input_hash
artifact_hash
warnings
```

### 5.2 Warning Object

```json
{
  "code": "weak_predictive_score",
  "severity": "warning",
  "message": "Cross-validated Q2 is below the configured threshold.",
  "field": "model_fit.metrics.q2",
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

Rules:

```text
- Blocking warnings prevent downstream use unless the tool explicitly supports override.
- Warning codes are lowercase snake_case.
- Human-readable messages must not contain stack traces.
```

### 5.3 Error Object

```json
{
  "code": "invalid_factor_bounds",
  "message": "Factor low bound must be less than high bound.",
  "field": "factors[0].low",
  "recoverable": true,
  "details": {
    "low": 12,
    "high": 6
  }
}
```

Rules:

```text
- Tool errors return structured errors.
- Persisted failed audit log entries include errors.
- Invalid inputs should not create scientific output artifacts, except validation reports when useful.
```

### 5.4 Quantity Object

Use `Quantity` for dimensional scalar values when a value needs provenance.

```json
{
  "value": 8.0,
  "unit": "mM",
  "basis": "individual_ntp",
  "source": "user_input"
}
```

Required fields:

```text
value
unit
```

Optional fields:

```text
basis
source
notes
```

### 5.5 Value Source

Allowed source labels:

```text
user_input
imported_observation
derived
model_predicted
tool_generated
dashboard_state
```

## 6. Unit Contract

### 6.1 Unit Storage

Store units as strings exactly from the accepted unit registry.

Launch unit registry:

```text
dimensionless: ratio, percent, score
concentration: mM, uM, nM, g/L, mg/L, ug/mL, ng/uL, U/uL
volume: L, mL, uL
time: h, min, s
mass: kg, g, mg, ug, ng
amount: mol, mmol, umol, nmol
currency: USD, EUR, GBP
cost_basis: USD/U, EUR/U, USD/ng, EUR/ng, USD/umol, EUR/umol, USD/batch, EUR/batch
```

### 6.2 Unit Conversion Rules

Allowed automatic conversions:

```text
time: h, min, s
mass: kg, g, mg, ug, ng
volume: L, mL, uL
amount: mol, mmol, umol, nmol
concentration mass/volume within compatible dimensions
```

Requires explicit user-provided conversion:

```text
- enzyme activity units to mass
- vendor-specific units
- currency conversion
- modified nucleotide equivalents
- assay score to absolute concentration
```

### 6.3 Unit Validation

Rules:

```text
- Dimensional values must include unit.
- Unitless values must use unit = "ratio", "percent", or "score" as applicable.
- Mixed units in one column are normalized or rejected.
- Dashboard labels always display units.
```

## 7. Study Schema

### 7.1 `study.json`

Purpose: identifies the study, domain template, constructs, active artifacts, and status.

```json
{
  "artifact_metadata": {
    "artifact_id": "artifact_study_001",
    "artifact_type": "study",
    "study_id": "ivt_egfp_001",
    "run_id": "run_20260420_120501_a8f3",
    "schema_version": "1.0.0",
    "method_version": "1.0.0",
    "tool_name": "create_or_update_study",
    "tool_version": "0.1.0",
    "generated_at": "2026-04-20T19:05:01Z",
    "input_hash": "sha256:inputhash",
    "artifact_hash": "sha256:artifacthash",
    "warnings": []
  },
  "study": {
    "study_id": "ivt_egfp_001",
    "title": "IVT eGFP DOE",
    "domain_template": "ivt_qbd",
    "status": "active",
    "created_at": "2026-04-20T19:00:00Z",
    "updated_at": "2026-04-20T19:05:01Z",
    "active_design_id": "design_iter01_dopt_7c2d",
    "active_fit_id": null,
    "active_construct_id": "egfp_995nt",
    "artifact_index": []
  }
}
```

Allowed statuses:

```text
active
archived
superseded
failed_validation
```

## 8. Factor Space Schema

### 8.1 Factor Space Artifact

File:

```text
factor_space.json
```

Shape:

```json
{
  "artifact_metadata": {},
  "factor_space": {
    "factors": [],
    "constraints": [],
    "fixed_conditions": [],
    "normalization": {
      "internal_name_policy": "lower_snake_case",
      "default_continuous_coding": "center_scale_to_minus_one_plus_one"
    }
  }
}
```

### 8.2 FactorSpec

```json
{
  "factor_id": "factor_mg_ntp_ratio",
  "name": "mg_ntp_ratio",
  "display_name": "Mg:NTP ratio",
  "kind": "continuous",
  "units": "ratio",
  "low": 0.8,
  "high": 1.6,
  "levels": null,
  "default_value": 1.2,
  "fixed": false,
  "transform": {
    "name": "none",
    "parameters": {}
  },
  "coding": {
    "method": "center_scale",
    "low_coded": -1,
    "high_coded": 1
  },
  "role": "process_factor",
  "description": "Total Mg:NTP molar ratio.",
  "source": "user_input"
}
```

Required fields:

```text
factor_id
name
display_name
kind
units
fixed
transform
coding
role
source
```

Kind-specific requirements:

```text
continuous:
  requires low and high
  levels optional

categorical:
  requires levels
  low and high null

ordinal:
  requires ordered levels

fixed:
  requires default_value
```

Allowed roles:

```text
process_factor
block
batch
construct_metadata
environmental
derived_factor
```

### 8.3 TransformSpec

```json
{
  "name": "log",
  "parameters": {
    "base": "e"
  }
}
```

Allowed names:

```text
none
center_scale
log
log10
sqrt
reciprocal
user_defined_named_transform
```

### 8.4 ConstraintSpec

```json
{
  "constraint_id": "constraint_low_ph",
  "expression": "ph >= 6.8",
  "description": "Avoid pH below 6.8.",
  "constraint_type": "inequality",
  "severity": "blocking",
  "applies_to": ["ph"],
  "source": "user_input"
}
```

Allowed constraint types:

```text
inequality
equality
bounded_expression
forbidden_combination
candidate_filter
```

Rules:

```text
- Expressions operate on raw factor names.
- Expressions must be parseable by the safe constraint evaluator.
- Constraint IDs must be stable across reruns if semantics do not change.
```

## 9. Response Schema

### 9.1 `responses.json`

```json
{
  "artifact_metadata": {},
  "responses": [
    {
      "response_id": "response_mrna_yield",
      "name": "mrna_yield",
      "display_name": "mRNA yield",
      "role": "productivity",
      "value_type": "measured",
      "goal": "maximize",
      "units": "g/L",
      "weight": 1.0,
      "threshold": null,
      "assay": {
        "name": "HPLC",
        "scale": null,
        "semi_quantitative": false
      },
      "source": "user_input"
    }
  ]
}
```

### 9.2 ResponseSpec

Required fields:

```text
response_id
name
display_name
role
value_type
goal
units
weight
source
```

Allowed roles:

```text
productivity
CQA
economics
diagnostic
derived
kinetic
purity
process
```

Allowed value types:

```text
measured
derived
predicted
semi_quantitative
```

Allowed goals:

```text
maximize
minimize
target
range
upper_threshold
lower_threshold
diagnostic_only
```

### 9.3 ThresholdSpec

```json
{
  "operator": "<",
  "value": 3,
  "unit": "score",
  "hard_constraint": true,
  "description": "dsRNA score must remain below 3."
}
```

Allowed operators:

```text
<
<=
>
>=
=
between
```

### 9.4 DerivedResponseSpec

```json
{
  "response_id": "response_relative_yield",
  "name": "relative_yield",
  "display_name": "Relative yield",
  "role": "derived",
  "value_type": "derived",
  "goal": "diagnostic_only",
  "units": "percent",
  "formula": {
    "name": "relative_yield_percent",
    "inputs": ["mrna_yield", "theoretical_yield"],
    "expression": "100 * mrna_yield / theoretical_yield",
    "method_version": "1.0.0"
  },
  "source": "tool_generated"
}
```

Rules:

```text
- Derived responses must include formula metadata.
- Derived responses must identify source input fields.
- Derived responses must never overwrite measured responses.
```

## 10. DOE Design Schemas

### 10.1 Design Metadata

File:

```text
designs/<design_id>/design_metadata.json
```

```json
{
  "artifact_metadata": {},
  "design": {
    "design_id": "design_iter01_dopt_7c2d",
    "study_id": "ivt_egfp_001",
    "iteration": 1,
    "design_type": "d_optimal",
    "status": "generated",
    "factor_space_hash": "sha256:factorhash",
    "response_set_hash": "sha256:responsehash",
    "random_seed": 20260420,
    "randomized": true,
    "n_runs": 12,
    "model_intent": "response_surface",
    "requested_terms": [
      "mg_ntp_ratio",
      "ntp_concentration",
      "dna_template",
      "t7_rnap",
      "mg_ntp_ratio:ntp_concentration",
      "dna_template:t7_rnap",
      "I(mg_ntp_ratio^2)",
      "I(ntp_concentration^2)"
    ],
    "estimable_terms": [],
    "not_estimable_terms": [],
    "diagnostics": {
      "model_matrix_rank": 9,
      "n_model_columns": 9,
      "condition_number": 18.4,
      "logdet": 12.73,
      "constraint_retention_fraction": 1.0
    },
    "matrix_path": "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/design_matrix.csv"
  }
}
```

Allowed design types:

```text
full_factorial
fractional_factorial
latin_hypercube
candidate_set_optimal
d_optimal
d_optimal_augmentation
verification_plan
custom_imported
```

Allowed statuses:

```text
generated
accepted
superseded
failed
imported
```

### 10.2 Design Matrix CSV

File:

```text
designs/<design_id>/design_matrix.csv
```

Required columns:

```text
study_id
design_id
run_id
iteration
run_type
randomization_order
block
replicate
<factor columns>
```

Allowed run types:

```text
model_building
augmentation
center_point
replicate
control
verification
candidate_recommendation
```

Example:

```csv
study_id,design_id,run_id,iteration,run_type,randomization_order,block,replicate,mg_ntp_ratio,ntp_concentration,dna_template,t7_rnap
ivt_egfp_001,design_iter01_dopt_7c2d,run_001,1,model_building,7,1,1,0.8,8.0,100,15
ivt_egfp_001,design_iter01_dopt_7c2d,run_002,1,model_building,3,1,1,1.6,12.0,10,2
```

Rules:

```text
- CSV factor column names use internal factor names.
- Units are not embedded in column names; units live in factor_space.json.
- Row order is storage order; randomization_order gives execution order.
- run_id must be stable once issued.
```

### 10.3 Candidate Set Artifact

Large candidate sets may be stored separately:

```text
designs/<design_id>/candidate_set.csv
designs/<design_id>/candidate_set.metadata.json
```

Metadata:

```json
{
  "artifact_metadata": {},
  "candidate_set": {
    "candidate_set_id": "candidate_iter01_grid_1a2b",
    "generation_method": "low_mid_high_grid",
    "n_candidates": 81,
    "constraints_applied": ["constraint_low_ph"],
    "candidate_set_hash": "sha256:candidatehash",
    "path": "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/candidate_set.csv"
  }
}
```

## 11. Observation Schemas

### 11.1 Endpoint Observations CSV

File:

```text
observations/endpoint_observations.csv
```

Required columns:

```text
study_id
run_id
observation_id
observation_type
<factor columns or design row link>
<response columns>
```

Recommended metadata columns:

```text
replicate
batch_id
operator_id
instrument_id
observed_at
notes
```

Example:

```csv
study_id,run_id,observation_id,observation_type,mg_ntp_ratio,ntp_concentration,dna_template,t7_rnap,mrna_yield,dsrna_score,observed_at
ivt_egfp_001,run_001,obs_001,endpoint,0.8,8.0,100,15,12.1,2.2,2026-04-20T19:30:00Z
```

Rules:

```text
- Response column units are defined in observations metadata or responses.json.
- Missing response values are blank in CSV and represented as null in normalized JSON.
- The import tool must not average replicates unless requested.
```

### 11.2 Endpoint Observations Metadata

File:

```text
observations/endpoint_observations.metadata.json
```

```json
{
  "artifact_metadata": {},
  "observation_table": {
    "table_id": "endpoint_obs_iter01",
    "table_type": "endpoint",
    "path": "outputs/studies/ivt_egfp_001/observations/endpoint_observations.csv",
    "n_rows": 12,
    "factor_columns": ["mg_ntp_ratio", "ntp_concentration", "dna_template", "t7_rnap"],
    "response_columns": [
      {
        "name": "mrna_yield",
        "unit": "g/L",
        "response_id": "response_mrna_yield"
      },
      {
        "name": "dsrna_score",
        "unit": "score",
        "response_id": "response_dsrna_score"
      }
    ],
    "missing_values": [],
    "import_warnings": []
  }
}
```

### 11.3 Time-Resolved Observations CSV

File:

```text
observations/time_resolved_observations.csv
```

Required columns:

```text
study_id
run_id
observation_id
time
time_unit
analyte
value
value_unit
```

Recommended columns:

```text
sample_id
replicate
quench_method
dilution_factor
instrument_id
observed_at
```

Example:

```csv
study_id,run_id,observation_id,time,time_unit,analyte,value,value_unit,sample_id
ivt_egfp_001,run_001,obs_t001,15,min,mrna_concentration,1.8,g/L,sample_001
ivt_egfp_001,run_001,obs_t002,30,min,mrna_concentration,3.7,g/L,sample_002
ivt_egfp_001,run_001,obs_t003,30,min,atp_remaining,5.9,mM,sample_002
```

Rules:

```text
- One row represents one analyte value at one time point.
- Multiple analytes at the same time point use multiple rows.
- Duplicate run/analyte/time rows require replicate or sample_id.
- Time values are normalized in metadata but original values are preserved.
```

### 11.4 Time-Resolved Metadata

```json
{
  "artifact_metadata": {},
  "time_resolved_table": {
    "table_id": "timecourse_iter01",
    "path": "outputs/studies/ivt_egfp_001/observations/time_resolved_observations.csv",
    "time_unit_normalized": "min",
    "analytes": [
      {
        "name": "mrna_concentration",
        "unit": "g/L",
        "maps_to_response": "mrna_yield"
      },
      {
        "name": "atp_remaining",
        "unit": "mM",
        "maps_to_response": null
      }
    ],
    "endpoint_summary_method": "final_observed",
    "endpoint_summary_path": "outputs/studies/ivt_egfp_001/derived/endpoint_summary.json"
  }
}
```

## 12. Construct and Sequence Schemas

### 12.1 Construct Metadata Artifact

File:

```text
constructs.json
```

```json
{
  "artifact_metadata": {},
  "constructs": [
    {
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
      "modifications": [],
      "source": "user_input"
    }
  ]
}
```

Required fields:

```text
construct_id
display_name
construct_type
nucleotide_counts or sequence
transcript_length
source
```

### 12.2 Nucleotide Counts

```json
{
  "A": 300,
  "C": 220,
  "G": 240,
  "U": 235
}
```

Rules:

```text
- Counts are non-negative integers.
- Counts must sum to transcript_length.
- Modified nucleotides require explicit aliases and residue masses.
```

### 12.3 Modification Object

```json
{
  "symbol": "m1Psi",
  "canonical_replaces": "U",
  "count": 235,
  "residue_mass": {
    "value": 320.2,
    "unit": "g/mol"
  }
}
```

Rules:

```text
- Modified nucleotide residue mass is required unless molecular weight override is supplied.
- Theoretical-yield tools must record how modifications were handled.
```

## 13. Derived Scientific Artifact Schemas

### 13.1 Theoretical Yield Artifact

File:

```text
derived/theoretical_yield.json
```

```json
{
  "artifact_metadata": {},
  "theoretical_yield_results": [
    {
      "run_id": "run_001",
      "construct_id": "egfp_995nt",
      "ntp_concentrations": {
        "ATP": { "value": 8, "unit": "mM" },
        "CTP": { "value": 8, "unit": "mM" },
        "GTP": { "value": 8, "unit": "mM" },
        "UTP": { "value": 8, "unit": "mM" }
      },
      "limiting_ntp": "ATP",
      "molecular_weight": {
        "value": 320000,
        "unit": "g/mol"
      },
      "theoretical_yield": {
        "value": 8.53,
        "unit": "g/L"
      },
      "measured_yield": {
        "value": 6.9,
        "unit": "g/L",
        "source": "imported_observation"
      },
      "relative_yield_percent": 80.9,
      "warnings": []
    }
  ]
}
```

Rules:

```text
- theoretical_yield is nullable only when calculation status is unavailable.
- relative_yield_percent is nullable when measured_yield is unavailable.
- limiting_ntp is required when theoretical_yield is calculated.
```

### 13.2 Endpoint Summary Artifact

File:

```text
derived/endpoint_summary.json
```

```json
{
  "artifact_metadata": {},
  "endpoint_summaries": [
    {
      "run_id": "run_001",
      "source_table_id": "timecourse_iter01",
      "analyte": "mrna_concentration",
      "summary_method": "final_observed",
      "time": {
        "value": 210,
        "unit": "min"
      },
      "value": {
        "value": 11.8,
        "unit": "g/L"
      },
      "maps_to_response": "mrna_yield",
      "warnings": []
    }
  ]
}
```

Allowed summary methods:

```text
final_observed
max_observed
time_selected
plateau_mean
```

## 14. Model Fit Schemas

### 14.1 Model Fit Artifact

File:

```text
models/<fit_id>/model_fit.json
```

```json
{
  "artifact_metadata": {},
  "fit": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "study_id": "ivt_egfp_001",
    "design_id": "design_iter01_dopt_7c2d",
    "observation_table_id": "endpoint_obs_iter01",
    "model_family": "ols_response_surface",
    "status": "fit",
    "models": [
      {
        "model_id": "model_mrna_yield",
        "response": "mrna_yield",
        "formula": "mrna_yield ~ mg_ntp_ratio + ntp_concentration + dna_template + t7_rnap + mg_ntp_ratio:ntp_concentration + I(ntp_concentration^2)",
        "terms": [],
        "coefficients": [],
        "metrics": {},
        "diagnostics": {},
        "warnings": []
      }
    ]
  }
}
```

Allowed statuses:

```text
fit
fit_with_warnings
rank_deficient
failed
```

### 14.2 Term Object

```json
{
  "term": "mg_ntp_ratio:ntp_concentration",
  "term_type": "interaction",
  "source_factors": ["mg_ntp_ratio", "ntp_concentration"],
  "estimable": true,
  "included": true,
  "coding": "coded_continuous_product"
}
```

Allowed term types:

```text
intercept
main_effect
interaction
square
block
categorical_level
derived
```

### 14.3 Coefficient Object

```json
{
  "term": "ntp_concentration",
  "estimate": 1.42,
  "standard_error": 0.31,
  "t_value": 4.58,
  "p_value": 0.004,
  "confidence_interval": {
    "level": 0.95,
    "lower": 0.74,
    "upper": 2.1
  },
  "estimable": true,
  "warnings": []
}
```

Rules:

```text
- p_value is null when unavailable.
- confidence_interval is null when unavailable.
- non-estimable coefficients must set estimable = false and include a warning.
```

### 14.4 Metrics Object

```json
{
  "n_observations": 23,
  "n_model_columns": 9,
  "rank": 9,
  "residual_degrees_of_freedom": 14,
  "r2": 0.97,
  "adjusted_r2": 0.95,
  "q2": 0.86,
  "rmse": 0.42,
  "sse": 2.47,
  "sst": 82.3,
  "validation_method": "leave_one_out",
  "lack_of_fit": {
    "status": "unavailable",
    "reason": "No replicated factor settings."
  }
}
```

### 14.5 Diagnostics Object

```json
{
  "condition_number": 82.4,
  "high_leverage_rows": ["run_006"],
  "large_residual_rows": [],
  "cooks_distance_flags": [],
  "rank_warnings": [],
  "extrapolation_policy": "forbid_outside_factor_space"
}
```

### 14.6 Residuals CSV

File:

```text
models/<fit_id>/residuals.csv
```

Required columns:

```text
study_id
fit_id
model_id
run_id
response
observed
fitted
residual
standardized_residual
leverage
cooks_distance
```

### 14.7 Predictions CSV

File:

```text
models/<fit_id>/predictions.csv
```

Required columns:

```text
study_id
fit_id
model_id
prediction_id
prediction_context
run_id
response
predicted
standard_error_mean
standard_error_prediction
prediction_interval_lower
prediction_interval_upper
confidence_level
```

Allowed prediction contexts:

```text
fitted_row
candidate
grid
recommendation
verification
```

## 15. Effects and Plot Payload Schemas

### 15.1 Effects Artifact

File:

```text
derived/effects.json
```

```json
{
  "artifact_metadata": {},
  "effects": {
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "effect_sets": [
      {
        "response": "mrna_yield",
        "effect_type": "standardized",
        "effects": [
          {
            "term": "ntp_concentration",
            "effect_value": 1.42,
            "absolute_effect_value": 1.42,
            "rank": 1,
            "sign": "positive",
            "warnings": []
          }
        ]
      }
    ],
    "plot_payloads": {
      "pareto": [],
      "factor_response": [],
      "contours": []
    }
  }
}
```

### 15.2 Pareto Payload

```json
{
  "response": "mrna_yield",
  "term": "ntp_concentration",
  "effect_value": 1.42,
  "absolute_effect_value": 1.42,
  "rank": 1,
  "sign": "positive",
  "threshold": null,
  "threshold_label": null,
  "warnings": []
}
```

### 15.3 Factor Response Payload

```json
{
  "response": "mrna_yield",
  "factor": "ntp_concentration",
  "hold_strategy": "center",
  "hold_values": {
    "mg_ntp_ratio": 1.2,
    "dna_template": 55,
    "t7_rnap": 8.5
  },
  "points": [
    {
      "factor_value": 6,
      "predicted": 7.4,
      "lower": 6.9,
      "upper": 7.9,
      "in_factor_space": true
    }
  ],
  "units": {
    "factor": "mM",
    "response": "g/L"
  }
}
```

### 15.4 Contour Payload

```json
{
  "response": "mrna_yield",
  "factor_x": "mg_ntp_ratio",
  "factor_y": "ntp_concentration",
  "hold_strategy": "center",
  "hold_values": {
    "dna_template": 55,
    "t7_rnap": 8.5
  },
  "grid": [
    {
      "x": 0.8,
      "y": 6,
      "predicted": 6.2,
      "lower": 5.7,
      "upper": 6.7,
      "feasible": true,
      "extrapolated": false
    }
  ],
  "units": {
    "x": "ratio",
    "y": "mM",
    "response": "g/L"
  }
}
```

## 16. Economics Schemas

### 16.1 Economics Artifact

File:

```text
derived/economics.json
```

```json
{
  "artifact_metadata": {},
  "economics": {
    "economics_status": "calculated",
    "cost_inputs_hash": "sha256:costhash",
    "currency": "EUR",
    "cost_efficiency_metric": "mass_per_currency",
    "component_costs": [],
    "condition_results": [],
    "sensitivity_results": null,
    "warnings": []
  }
}
```

Allowed economics statuses:

```text
calculated
skipped_missing_component_costs
failed_validation
partially_calculated
```

### 16.2 ComponentCostSpec

```json
{
  "component_id": "comp_t7_rnap",
  "component_name": "T7 RNAP",
  "unit_cost": 4.2,
  "currency": "EUR",
  "cost_basis_unit": "EUR/U",
  "factor_mapping": "t7_rnap",
  "fixed_amount_per_batch": null,
  "amount_unit": "U",
  "price_low": null,
  "price_high": null,
  "source": "user_input",
  "notes": "User-provided example cost."
}
```

Required fields:

```text
component_id
component_name
unit_cost
currency
cost_basis_unit
source
```

Rules:

```text
- factor_mapping or fixed_amount_per_batch is required.
- mixed currency rows require explicit conversion artifact.
- source must be user_input for launch economics.
```

### 16.3 Cost Condition Result

```json
{
  "run_id": "run_001",
  "scenario_id": null,
  "factor_settings": {
    "mg_ntp_ratio": 0.8,
    "ntp_concentration": 8,
    "dna_template": 100,
    "t7_rnap": 15
  },
  "product_mass": {
    "value": 590,
    "unit": "ug",
    "source": "model_predicted"
  },
  "total_condition_cost": {
    "value": 31.2,
    "unit": "EUR"
  },
  "cost_efficiency": {
    "value": 18.91,
    "unit": "ug/EUR",
    "metric": "mass_per_currency"
  },
  "cost_breakdown": [
    {
      "component_id": "comp_t7_rnap",
      "component_name": "T7 RNAP",
      "amount": {
        "value": 15,
        "unit": "U"
      },
      "cost": {
        "value": 63,
        "unit": "EUR"
      },
      "mapping": "t7_rnap"
    }
  ],
  "warnings": []
}
```

Rules:

```text
- Product mass source must be measured, derived, or predicted.
- Unit conversions must be listed in warnings or details when non-trivial.
- Cost efficiency is null if product mass or total cost is unavailable.
```

## 17. Design-Space Probability Schema

### 17.1 Design-Space Artifact

File:

```text
derived/design_space_probability.json
```

```json
{
  "artifact_metadata": {},
  "design_space_probability": {
    "status": "calculated",
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "quality_threshold": {
      "response": "dsrna_score",
      "operator": "<",
      "value": 3,
      "unit": "score"
    },
    "simulation_settings": {
      "n_simulations": 10000,
      "factor_noise_percent": 5,
      "noise_distribution": "normal",
      "seed": 20260420,
      "failure_limit": 0.01
    },
    "grid": [],
    "warnings": []
  }
}
```

Allowed statuses:

```text
calculated
unavailable_missing_model
unavailable_missing_threshold
unavailable_rank_deficient_model
failed
```

### 17.2 Design-Space Grid Point

```json
{
  "point_id": "dsp_000001",
  "factor_settings": {
    "mg_ntp_ratio": 0.9,
    "ntp_concentration": 10
  },
  "hold_values": {
    "dna_template": 55,
    "t7_rnap": 8.5
  },
  "probability_of_failure": 0.004,
  "classification": "in_design_space",
  "valid_simulations": 9972,
  "failed_simulations": 40,
  "warnings": []
}
```

Allowed classifications:

```text
in_design_space
outside_design_space
unknown
```

## 18. Recommendation Schema

### 18.1 Recommendations Artifact

File:

```text
derived/recommendations.json
```

```json
{
  "artifact_metadata": {},
  "recommendations": {
    "recommendation_set_id": "recs_iter02_001",
    "strategy": "hybrid",
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "objectives": [],
    "recommendations": []
  }
}
```

Allowed strategies:

```text
desirability
d_optimal_augment
expected_improvement
hybrid
verification
```

### 18.2 Recommendation Object

```json
{
  "recommendation_id": "rec_001",
  "rank": 1,
  "run_type": "candidate_recommendation",
  "factor_settings": {
    "mg_ntp_ratio": 0.95,
    "ntp_concentration": 10.5,
    "dna_template": 80,
    "t7_rnap": 5
  },
  "predicted_responses": {
    "mrna_yield": {
      "value": 11.2,
      "unit": "g/L"
    },
    "dsrna_score": {
      "value": 2.1,
      "unit": "score"
    }
  },
  "desirability": 0.87,
  "uncertainty_score": 0.31,
  "constraint_status": "feasible",
  "rationale_type": "exploitation",
  "rationale": "High predicted yield with dsRNA below threshold and lower T7 RNAP usage.",
  "warnings": []
}
```

Allowed constraint statuses:

```text
feasible
infeasible
unknown
quality_risk
```

Allowed rationale types:

```text
exploitation
exploration
constraint_probing
verification
control
```

## 19. Verification Schema

### 19.1 Verification Plan Artifact

File:

```text
derived/verification_plan.json
```

```json
{
  "artifact_metadata": {},
  "verification_plan": {
    "verification_plan_id": "verify_iter01_001",
    "fit_id": "fit_yield_dsrna_iter01_31ad",
    "design_space_artifact": "outputs/studies/ivt_egfp_001/derived/design_space_probability.json",
    "runs": [],
    "warnings": []
  }
}
```

### 19.2 Verification Run Object

```json
{
  "verification_run_id": "verify_run_001",
  "run_type": "predicted_optimum",
  "factor_settings": {
    "mg_ntp_ratio": 0.95,
    "ntp_concentration": 10.5,
    "dna_template": 80,
    "t7_rnap": 5
  },
  "predicted_responses": {
    "mrna_yield": {
      "value": 11.2,
      "unit": "g/L",
      "prediction_interval": {
        "level": 0.95,
        "lower": 10.1,
        "upper": 12.3
      }
    }
  },
  "purpose": "Confirm predicted optimum.",
  "selection_rationale": "Highest desirability inside quality design space.",
  "warnings": []
}
```

Allowed verification run types:

```text
predicted_optimum
design_space_corner
design_space_edge
quality_boundary_probe
center_point
replicate_control
model_disagreement_probe
```

### 19.3 Verification Result Object

When observed verification data is imported:

```json
{
  "verification_run_id": "verify_run_001",
  "response": "mrna_yield",
  "predicted": 11.2,
  "observed": 11.6,
  "unit": "g/L",
  "prediction_interval": {
    "level": 0.95,
    "lower": 10.1,
    "upper": 12.3
  },
  "within_interval": true,
  "prediction_error": 0.4,
  "relative_error_percent": 3.45,
  "interpretation": "supports_model"
}
```

Allowed interpretations:

```text
supports_model
challenges_model
inconclusive
outside_scope
```

## 20. Audit Log Schema

File:

```text
audit_log.jsonl
```

Each line is one JSON object.

```json
{
  "timestamp": "2026-04-20T19:05:01Z",
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "tool_name": "design_doe",
  "tool_version": "0.1.0",
  "method_version": "1.0.0",
  "schema_version": "1.0.0",
  "input_hash": "sha256:inputhash",
  "output_hash": "sha256:outputhash",
  "status": "success",
  "duration_ms": 148,
  "seed": 20260420,
  "artifact_paths": [
    "outputs/studies/ivt_egfp_001/designs/design_iter01_dopt_7c2d/design_matrix.csv"
  ],
  "warnings": [],
  "errors": []
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

## 21. Dashboard Payload Schema

### 21.1 Payload Artifact

File:

```text
dashboard_payload.json
```

Purpose: the single versioned read model for the React dashboard.

Top-level shape:

```json
{
  "version": "1.0.0",
  "payload_metadata": {},
  "study": {},
  "factor_space": {},
  "responses": [],
  "constructs": [],
  "designs": [],
  "observations": {},
  "models": [],
  "derived": {},
  "dashboard_state": {},
  "warnings": [],
  "audit": {}
}
```

Rules:

```text
- Dashboard payload is generated by MCP tools, not hand-edited.
- Payload may denormalize artifacts for faster rendering.
- Payload must reference source artifact hashes.
- Payload must be valid even when optional sections are unavailable.
```

### 21.2 Payload Metadata

```json
{
  "payload_id": "payload_ivt_egfp_001_latest",
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "generated_at": "2026-04-20T19:05:01Z",
  "schema_version": "1.0.0",
  "payload_hash": "sha256:payloadhash",
  "source_artifacts": [
    {
      "artifact_type": "factor_space",
      "path": "outputs/studies/ivt_egfp_001/factor_space.json",
      "artifact_hash": "sha256:factorhash"
    }
  ]
}
```

### 21.3 Dashboard Availability States

Every dashboard section has an availability state:

```json
{
  "status": "available",
  "reason": null,
  "required_inputs": [],
  "source_artifacts": []
}
```

Allowed statuses:

```text
available
unavailable_missing_input
unavailable_not_run
unavailable_failed_validation
unavailable_unsupported
```

Required launch sections:

```text
experiment_matrix
warnings
time_courses
effects
relative_yield
economics
diagnostics
recommendations
verification
audit
```

### 21.4 Dashboard State

Dashboard state is non-scientific UI state.

```json
{
  "selected_response": "mrna_yield",
  "selected_factor_x": "mg_ntp_ratio",
  "selected_factor_y": "ntp_concentration",
  "selected_scenario_ids": [],
  "matrix_filters": {},
  "show_confidence_bands": true,
  "show_cogs_overlay": false
}
```

Rules:

```text
- Dashboard state must not affect scientific artifact hashes.
- Persisted dashboard defaults may be regenerated.
- User UI interactions need not be written back to scientific artifacts.
```

### 21.5 Dashboard Audit Summary

```json
{
  "artifact_hashes": {
    "factor_space": "sha256:factorhash",
    "design_matrix": "sha256:designhash",
    "model_fit": "sha256:fithash"
  },
  "generated_by": "generate_dashboard_payload",
  "generated_at": "2026-04-20T19:05:01Z",
  "method_versions": {
    "design_doe": "1.0.0",
    "fit_response_surface": "1.0.0"
  }
}
```

## 22. MCP Tool Input and Output Envelope

### 22.1 Tool Input Envelope

Every MCP tool accepts a JSON object. Tools that modify or read a study must include:

```json
{
  "study_id": "ivt_egfp_001",
  "run_id": "run_20260420_120501_a8f3",
  "request": {},
  "options": {
    "seed": 20260420,
    "overwrite_policy": "write_new_run",
    "strict_validation": true
  }
}
```

`run_id` may be omitted by callers; the MCP server generates it.

Allowed overwrite policies:

```text
write_new_run
replace_latest_pointer
fail_if_exists
```

### 22.2 Tool Output Envelope

Every MCP tool returns:

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
- artifact_paths are workspace-relative.
- structured_content may duplicate key artifact data for immediate Codex use.
- persisted artifact is authoritative when it differs from summary text.
```

## 23. CSV Import Contracts

### 23.1 CSV General Rules

```text
- UTF-8 encoding.
- Comma delimiter.
- Header row required.
- LF or CRLF accepted; stored normalized to LF.
- Empty strings are parsed as null for optional fields.
- Numeric columns must not contain unit suffixes.
- Units live in metadata or schema, not in cell values.
```

### 23.2 Column Name Mapping

Import tools must support a mapping object:

```json
{
  "column_mapping": {
    "Mg:NTP": "mg_ntp_ratio",
    "NTP (mM)": "ntp_concentration",
    "Yield g/L": "mrna_yield"
  }
}
```

Rules:

```text
- Original column names are preserved in metadata.
- Normalized names are used in artifacts.
- Ambiguous column mappings are validation errors.
```

### 23.3 Missing Values

Missing values are tracked explicitly:

```json
{
  "row_index": 12,
  "column": "dsrna_score",
  "reason": "blank_cell"
}
```

Missing measured responses do not invalidate the entire table unless the requested model requires those rows.

## 24. Schema Validation Rules

### 24.1 Validation Levels

```text
structural:
  required fields, types, enum values

semantic:
  unit compatibility, factor bounds, response goals

scientific:
  estimability, rank, model validity, calculation prerequisites
```

### 24.2 Validation Result

```json
{
  "valid": false,
  "validation_level": "semantic",
  "errors": [],
  "warnings": []
}
```

### 24.3 Strict vs Permissive Mode

Strict mode:

```text
- Unknown fields fail validation.
- Missing optional-but-recommended fields warn.
- Unit mismatches fail validation.
```

Permissive mode:

```text
- Unknown fields are preserved under extension fields.
- Missing recommended fields warn.
- Recoverable unit issues warn when not used in calculations.
```

Launch default:

```text
strict_validation = true for MCP tools
permissive rendering for dashboard payload with visible diagnostics
```

## 25. Schema Evolution and Compatibility

### 25.1 Version Compatibility

```text
Patch version:
  additive docs or validation message changes only

Minor version:
  optional fields added, enum values added with backward compatibility

Major version:
  required fields changed, field semantics changed, incompatible structure
```

### 25.2 Migration Contract

Schema migrations must include:

```text
- source schema version
- target schema version
- migration script or deterministic transform description
- validation fixture before and after migration
- known semantic changes
```

### 25.3 Extension Fields

Extension fields use:

```json
"extensions": {
  "vendor_or_module_key": {}
}
```

Rules:

```text
- Core tools ignore unknown extension keys unless strict mode forbids them.
- Extension fields must not override core field semantics.
```

## 26. Required Schema Files

The implementation should maintain JSON Schema files under:

```text
schemas/
```

Required launch schemas:

```text
artifact_metadata.schema.json
warning.schema.json
error.schema.json
study.schema.json
factor_space.schema.json
responses.schema.json
doe_design.schema.json
endpoint_observations.schema.json
time_resolved_observations.schema.json
construct.schema.json
theoretical_yield.schema.json
model_fit.schema.json
effects.schema.json
economics.schema.json
design_space_probability.schema.json
recommendations.schema.json
verification_plan.schema.json
dashboard_payload.schema.json
audit_log_entry.schema.json
tool_envelope.schema.json
```

## 27. Required Fixtures

Fixtures live under:

```text
fixtures/studies/
fixtures/dashboard/
```

Required launch fixtures:

```text
ivt_four_factor_factor_space.json
ivt_response_set.json
ivt_initial_dopt_design_matrix.csv
ivt_endpoint_observations.csv
ivt_time_resolved_observations.csv
ivt_construct_egfp.json
ivt_component_costs.json
ivt_theoretical_yield.json
ivt_model_fit.json
ivt_effects.json
ivt_economics.json
ivt_dashboard_payload.json
```

Fixture rules:

```text
- Fixtures must validate against schemas.
- Fixtures must be small enough for tests and documentation.
- Numeric fixtures must document expected tolerance.
- Cost fixtures must use clearly artificial user-provided prices.
```

## 28. Contract Tests

Required tests:

```text
- Every JSON fixture validates against its schema.
- Every CSV fixture validates against its metadata.
- dashboard_payload.json validates after each tool sequence.
- Unknown required fields fail strict validation.
- Economics unavailable state appears when component costs are absent.
- Cost calculation fails on missing currency or cost basis.
- Theoretical yield fails on missing sequence/composition.
- Model fit artifact rejects rank-deficient model marked as successful.
- Audit log entry validates for success and failure cases.
```

## 29. Security and Privacy Rules

Schemas must avoid storing secrets.

Forbidden fields in artifacts:

```text
api_key
password
token
secret
credential
private_key
```

Rules:

```text
- Instrument IDs are allowed; credentials are not.
- Operator IDs should be pseudonymous where possible.
- Local absolute paths are not portable and should be avoided in durable artifacts.
- User-provided cost tables are sensitive business data and must remain local by default.
```

## 30. Open Implementation Decisions Resolved by This Contract

1. `dashboard_payload.json` is the only dashboard read model.
2. CSV matrix files never encode units in headers.
3. Units live in factor, response, observation metadata, and quantity objects.
4. Optional economics uses explicit availability status.
5. Cost input source must be `user_input` at launch.
6. Time-resolved observations use long format.
7. Replicates are preserved, not silently averaged.
8. Relative yield and theoretical yield are derived artifacts, not raw observations.
9. Design-space probability is a derived artifact with explicit unavailable states.
10. Audit log is JSONL and append-only.

## 31. Workbench Schema Addendum

The workbench redesign extends the dashboard read model with an optional `workbench` section. Existing dashboard payloads remain valid. Workbench-enabled payloads must validate both the root dashboard payload contract and the nested workbench contracts.

### 31.1 New Workbench Schema Files

Required workbench foundation schemas:

```text
learnability_summary.schema.json
candidate_design.schema.json
candidate_design_set.schema.json
design_comparison.schema.json
run_plan_commit.schema.json
study_snapshot.schema.json
stale_state.schema.json
contextual_ai_panel.schema.json
workbench_payload.schema.json
```

### 31.2 Workbench Payload Section

The optional `workbench` section contains:

```text
mode
study_stage
recommendation_mode
candidate_design_sets
active_comparison
committed_run_plan
snapshots
stale_state
contextual_ai_panels
```

Rules:

```text
- candidate designs must include source_artifacts;
- contextual AI panels must include source_refs;
- stale states must include reason codes and affected objects;
- committed run plans must reference source candidate and comparison IDs;
- React may render and filter this state but must not compute scientific diagnostics.
```

### 31.3 Required Workbench Fixtures

Initial foundation fixture:

```text
fixtures/dashboard/workbench_candidate_designs_payload.json
```

Invalid traceability fixture:

```text
fixtures/dashboard/invalid_contextual_ai_panel_missing_source_refs.json
```

The schema validator must accept the workbench candidate fixture and reject the invalid contextual AI panel fixture.
