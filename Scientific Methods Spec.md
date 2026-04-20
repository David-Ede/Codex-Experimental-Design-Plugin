# Scientific Methods Spec: DOE, IVT/QbD Modeling, Optional Economics, and Verification

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Canonical Build Contract.md
```

## 1. Purpose

This document defines the scientific and numerical methods required for the Codex Scientific Toolchain. It is the implementation-facing contract for DOE generation, IVT/QbD calculations, response modeling, optional cost efficiency, design-space analysis, optimization, verification planning, and scientific warnings.

The MCP server is the scientific source of truth. Codex may explain results, choose workflow steps, and coordinate previews, but all numerical DOE matrices, coefficients, predicted responses, cost-efficiency values, design-space classifications, and verification recommendations must come from deterministic tools that implement this spec.

## 2. Scope

### 2.1 In Scope

```text
- Factor and response normalization.
- Factor encoding, scaling, and transformations.
- DOE generation for full factorial, fractional factorial, Latin hypercube, candidate-set optimal, and D-optimal designs.
- D-optimal augmentation foundation at launch, with full locked-row augmentation in paper-class scope.
- Endpoint observation validation.
- Time-resolved observation validation and endpoint summary derivation.
- IVT construct metadata parsing.
- Theoretical-yield and relative-yield calculation.
- Multiple linear regression response-surface modeling.
- Cross-validation, predictive metrics, model warnings, and lack-of-fit checks.
- Effect analysis and prediction-grid generation.
- Optional direct-input cost and cost-efficiency calculation.
- Desirability scoring and next-experiment ranking.
- Quality-threshold design-space estimation.
- Verification-run planning.
- Construct-transfer foundation for IVT workflows.
```

### 2.2 Out of Scope for This Methods Spec

```text
- React component implementation details.
- Codex plugin packaging details.
- Regulatory validation protocols.
- GMP batch-release decisions.
- External price lookup.
- Instrument-vendor file parsing beyond structured CSV/JSON imports.
```

## 3. Method Ownership Boundaries

### 3.1 MCP Server Owns

```text
- Input validation.
- DOE matrix generation.
- Statistical model fitting.
- Derived scientific responses.
- Cost-efficiency calculations.
- Prediction grids.
- Design-space classifications.
- Verification-run proposals.
- Artifact writing and audit metadata.
```

### 3.2 Codex Owns

```text
- Interpreting user intent.
- Selecting tool sequence.
- Asking for missing inputs when required.
- Explaining results and limitations from artifacts.
- Launching local commands and dashboard preview.
```

### 3.3 Dashboard Owns

```text
- Display.
- Sorting.
- Filtering.
- Chart transforms that do not change scientific meaning.
- Runtime payload validation.
```

The dashboard must not fit models, calculate final costs, calculate theoretical yield, optimize recommendations, or classify design-space regions.

## 4. Core Notation

```text
n = number of experimental rows
p = number of fitted model columns, including intercept
X = encoded model matrix, shape n x p
y = response vector, shape n
b = fitted coefficient vector
y_hat = fitted or predicted response
e = residual vector, y - y_hat
SSE = sum of squared errors
SST = total sum of squares around response mean
MSE = mean squared error
R2 = coefficient of determination
Q2 = cross-validated predictive coefficient
```

All tools must preserve the distinction between:

```text
- raw factor settings
- encoded model variables
- transformed model variables
- measured responses
- derived responses
- predicted responses
- recommended future runs
```

## 5. Input Normalization and Validation

### 5.1 Factor Names

The system must normalize names for internal identifiers while preserving display labels.

Rules:

```text
- Internal names are lowercase snake_case.
- Display names preserve user terminology.
- Duplicate normalized names are errors.
- Factor names must not collide with response names, reserved columns, or generated metadata fields.
```

Reserved fields:

```text
study_id
run_id
iteration
block
replicate
randomization_order
time
response
value
unit
```

### 5.2 Factor Types

Supported factor types:

```text
continuous
ordinal
categorical
mixture
fixed
```

Launch behavior:

```text
- continuous: requires low, high, and units unless dimensionless.
- ordinal: requires ordered numeric or label levels.
- categorical: requires explicit levels.
- mixture: accepted in schema, but constrained mixture designs are post-launch unless implemented.
- fixed: retained in artifacts but excluded from model terms unless explicitly requested.
```

### 5.3 Factor Bounds and Levels

Validation rules:

```text
- Continuous low must be less than high.
- Bounds must be finite numeric values.
- Categorical levels must be unique after string normalization.
- Ordinal levels must have a deterministic order.
- A factor with one level is treated as fixed and warned.
- Units are required when values are dimensional.
```

### 5.4 Factor Transforms

Supported transforms:

```text
none
center_scale
log
log10
sqrt
reciprocal
user_defined_named_transform
```

Validation rules:

```text
- log, log10, sqrt, and reciprocal require strictly positive raw values.
- Transforms are applied before model matrix construction.
- The artifact must record both raw factor values and transformed model values.
- User-defined transforms require a named formula from a trusted method registry, not arbitrary code.
```

Default transform behavior:

```text
- DOE generation uses coded variables in [-1, 1] for continuous factors unless the design method requires raw units.
- Model fitting uses the user-specified transform, then center/scales continuous model variables unless disabled.
- Categorical factors use deterministic treatment coding by default.
```

### 5.5 Constraints

Constraints are structured as expressions over raw factor settings.

Supported launch constraint forms:

```text
- linear inequality: a*x + b*y <= c
- linear equality: a*x + b*y = c
- bounded expression: lower <= expression <= upper
- forbidden categorical combination
- user-supplied candidate-set filter
```

Validation rules:

```text
- Constraints must be evaluable without arbitrary code execution.
- Invalid constraints stop DOE generation.
- Constraints that make the candidate set empty stop DOE generation.
- Constraints that remove more than 80% of candidate rows produce warnings.
```

## 6. Factor Encoding and Model Matrix Construction

### 6.1 Continuous Factors

Continuous factors are encoded for model fitting as:

```text
x_coded = 2 * (x_raw - midpoint) / (high - low)
midpoint = (high + low) / 2
```

If a transform is specified, transform first and code second:

```text
x_transformed = transform(x_raw)
x_coded = 2 * (x_transformed - transformed_midpoint) / transformed_range
```

The tool must preserve:

```text
- raw value
- transformed value
- coded value
- transform name
- coding bounds
```

### 6.2 Categorical Factors

Default categorical encoding is treatment coding:

```text
k levels -> k - 1 model columns
reference level = first level in declared order unless user specifies otherwise
```

Requirements:

```text
- The reference level must be stored in model artifacts.
- Predictions must require known categorical levels.
- Unknown levels in new data must fail validation.
```

For D-optimal candidate sets, categorical levels are included as candidate rows before model matrix encoding.

### 6.3 Interaction Terms

Interaction term syntax:

```text
A:B
```

For continuous-continuous interactions:

```text
X_A_B = X_A * X_B
```

For continuous-categorical interactions, multiply the continuous coded column by each non-reference categorical indicator.

For categorical-categorical interactions, include interaction columns between non-reference indicators. The tool must warn when a categorical interaction produces sparse or unobserved combinations.

### 6.4 Square Terms

Square term syntax:

```text
I(A^2)
```

Square terms use the transformed and coded continuous variable:

```text
X_A2 = X_A_coded^2
```

Square terms for categorical factors are invalid.

### 6.5 Heredity Rules

Supported heredity modes:

```text
none
weak
strong
```

Definitions:

```text
strong heredity: all parent main effects must be included for an interaction.
weak heredity: at least one parent main effect must be included for an interaction.
none: no heredity check is enforced.
```

Default mode:

```text
weak heredity
```

Warnings:

```text
- Interaction without required parent main effects.
- Square term without matching main effect.
- User-requested heredity mode incompatible with supplied terms.
```

## 7. DOE Generation Methods

### 7.1 DOE Output Contract

Every DOE generation method must return:

```text
- study_id
- design_id
- design_type
- iteration
- factor_space_hash
- random_seed
- randomization_enabled
- design_matrix
- encoded_design_summary
- model_terms_requested
- model_terms_estimable
- model_terms_not_estimable
- diagnostics
- warnings
- artifact_paths
```

Required diagnostics:

```text
- n_runs
- n_factors
- n_model_columns
- model_matrix_rank
- condition_number
- determinant_or_logdet when applicable
- alias_or_confounding_notes
- constraint_retention_fraction
```

### 7.2 Full Factorial

Use full factorial when:

```text
- all factors have explicit levels, or continuous factors can be discretized by requested levels;
- total runs do not exceed configured maximum;
- user requests exhaustive coverage.
```

Run count:

```text
n_runs = product(level_count_i)
```

Default maximum:

```text
256 runs
```

If the run count exceeds the maximum, the tool returns an error with alternatives:

```text
- reduce levels
- use fractional factorial
- use Latin hypercube
- use candidate-set optimal design
```

### 7.3 Fractional Factorial

Launch support:

```text
- two-level continuous or categorical factors only
- main-effects screening
- optional center points for continuous factors
```

Requirements:

```text
- The tool must report design resolution when calculable.
- The tool must report aliasing structure when calculable.
- Unsupported mixed-level fractional factorial designs must fail with a clear recommendation.
```

### 7.4 Latin Hypercube Sampling

Use Latin hypercube sampling for space-filling continuous designs.

Method:

```text
1. Divide each continuous factor range into n equal-probability intervals.
2. Sample one value from each interval per factor using the configured seed.
3. Independently permute sampled values per factor.
4. Reject rows that violate constraints.
5. If constraint rejection removes rows, resample up to max_attempts.
```

Defaults:

```text
max_attempts = 100
criterion = maximin distance among candidate rows when multiple samples are generated
```

Diagnostics:

```text
- minimum pairwise distance
- constraint rejection count
- factor marginal coverage
```

### 7.5 Candidate-Set Generation

Candidate-set designs start by constructing a feasible candidate pool.

Continuous candidate generation options:

```text
- low/mid/high grid
- user-specified levels
- Latin hypercube candidate pool
- full grid over requested levels
```

Categorical candidate generation:

```text
- Cartesian product of declared levels with other candidate dimensions.
```

Candidate filters:

```text
- hard constraints
- forbidden combinations
- run feasibility filters
- duplicate row removal
```

The candidate set artifact must include all candidate rows or a hash plus reproducible generation parameters when the set is too large to store inline.

### 7.6 D-Optimal Design

D-optimal design selects rows from a candidate set to maximize information for a requested model.

Model matrix:

```text
X_candidate = model_matrix(candidate_rows, requested_terms)
X_design = selected rows from X_candidate
```

Objective:

```text
maximize log(det(X_design' * X_design))
```

Use log determinant for numerical stability. If the matrix is rank deficient, determinant is treated as invalid and the candidate selection must continue or fail.

Minimum run rule:

```text
n_runs >= p
```

where `p` is the number of model columns including intercept. If `n_runs < p`, the tool must fail unless the user explicitly requests a screening fallback that drops terms.

Default algorithm:

```text
1. Build candidate set.
2. Build encoded candidate model matrix.
3. Initialize selected rows using deterministic QR-pivoted row selection or seeded random starts.
4. Apply Fedorov-style row exchange:
   - for each selected row and each unselected candidate row,
   - evaluate logdet improvement,
   - perform the best improving exchange,
   - repeat until improvement < tolerance or max iterations reached.
5. Run multiple seeded starts when candidate set size permits.
6. Return the best valid design.
```

Defaults:

```text
max_iterations = 1000
n_starts = 20
logdet_improvement_tolerance = 1e-8
condition_number_warning_threshold = 1000
```

Required diagnostics:

```text
- logdet
- model_matrix_rank
- condition_number
- selected_candidate_indices
- number_of_exchange_iterations
- convergence_status
- terms_not_estimable
- high_leverage_candidate_notes
```

### 7.7 D-Optimal Augmentation

Augmentation adds new runs while preserving existing runs.

Inputs:

```text
- existing design rows
- observed rows, if different from design rows
- locked row identifiers
- candidate set
- requested model terms
- target additional runs
```

Method:

```text
1. Encode existing locked rows into X_locked.
2. Encode feasible candidate rows into X_candidate.
3. Remove duplicate candidates unless repeats are explicitly allowed.
4. Select new rows that maximize log(det([X_locked; X_new]' * [X_locked; X_new])).
5. Return only new rows plus diagnostics for the combined design.
```

Requirements:

```text
- Existing rows are never changed.
- Repeated control rows are allowed only when requested.
- The combined design rank and condition number must be reported.
- Augmentation must warn when requested new rows cannot make the full model estimable.
```

### 7.8 Fallback Behavior

If D-optimal design cannot be generated, the tool may offer a fallback only when the user or workflow permits it.

Allowed fallbacks:

```text
- reduce model terms using heredity and parsimony rules
- increase run count recommendation
- use Latin hypercube screening
- use low/mid/high grid subset
```

Fallback output must include:

```text
- original requested method
- fallback method
- failure reason
- scientific implications
- terms dropped or unsupported
```

## 8. IVT/QbD Study Template

### 8.1 Launch IVT Factor Set

The launch IVT template must support the four-factor knowledge space:

```text
mg_ntp_ratio:
  display: Mg:NTP ratio
  kind: continuous
  units: ratio
  default_low: 0.8
  default_high: 1.6

ntp_concentration:
  display: NTP concentration, individual
  kind: continuous
  units: mM
  default_low: 6
  default_high: 12

dna_template:
  display: DNA template
  kind: continuous
  units: ng/uL
  default_low: 10
  default_high: 100

t7_rnap:
  display: T7 RNAP
  kind: continuous
  units: U/uL
  default_low: 2
  default_high: 15
```

The template may be instantiated with different ranges, units, or display names, but the methods must preserve the intended semantics.

### 8.2 Launch IVT Response Set

The launch IVT template must support:

```text
mrna_yield:
  role: productivity
  goal: maximize
  default_units: g/L

dsrna_score:
  role: CQA
  goal: upper_threshold
  default_threshold: 3
  assay_scale: 0 to 10

theoretical_yield:
  role: derived
  goal: diagnostic
  default_units: g/L

relative_yield:
  role: derived
  goal: diagnostic
  default_units: percent

cost_efficiency:
  role: economics
  goal: maximize
  default_units: mass/currency
  availability: only when component costs are supplied
```

### 8.3 Candidate Model Terms for IVT

The default first-pass IVT model candidate terms are:

```text
main effects:
  mg_ntp_ratio
  ntp_concentration
  dna_template
  t7_rnap

interactions:
  mg_ntp_ratio:ntp_concentration
  dna_template:t7_rnap

square terms:
  I(mg_ntp_ratio^2)
  I(ntp_concentration^2)
```

The full quadratic candidate set for four factors is:

```text
4 main effects
6 two-factor interactions
4 square terms
```

Later iterations may include more terms when data volume supports them. DNA template and T7 RNAP may use log transforms in later iterations when the workflow is modeling saturation or leveling behavior rather than a simple quadratic optimum.

### 8.4 Counterion Follow-Up DOE

The IVT template must be able to add counterion as a categorical factor:

```text
mg_counterion:
  display: Mg2+ counterion
  kind: categorical
  levels: chloride, acetate
```

The recommended follow-up design for counterion analysis is a mixed categorical/continuous candidate-set design using:

```text
- Mg:NTP ratio as continuous or discretized continuous factor.
- Mg2+ counterion as categorical factor.
- Optional interaction term mg_ntp_ratio:mg_counterion.
```

The tool must warn when categorical level replication is insufficient for estimating counterion effects.

## 9. Observation Data Methods

### 9.1 Endpoint Observation Validation

Endpoint rows must include:

```text
- run_id
- factor settings or link to design row
- one or more response values
```

Validation steps:

```text
1. Confirm run IDs are unique unless replicate rows are explicitly allowed.
2. Confirm every factor column maps to the study factor space.
3. Confirm response columns map to response definitions.
4. Validate numeric response values are finite.
5. Validate categorical factor values are known levels.
6. Validate units or mark units as missing with warning.
7. Write normalized observation artifact.
```

Replicates:

```text
- Replicate rows are allowed.
- Replicate grouping uses run_id, replicate_id, or identical factor settings.
- Replicates must be retained, not silently averaged.
- Optional summary statistics may be derived as separate artifacts.
```

### 9.2 Time-Resolved Observation Validation

Time-resolved data must use long format:

```text
study_id
run_id
time
time_unit
analyte
value
value_unit
```

Validation rules:

```text
- Time must be numeric and non-negative.
- Time units must be convertible within the study.
- Values must be finite numeric values.
- Each run/analyte pair must have at least two time points for a curve.
- Duplicate run/analyte/time rows require replicate IDs or are errors.
```

### 9.3 Endpoint Summary Derivation from Time Series

Supported summary methods:

```text
final_observed:
  value at the latest time point for each run/analyte

max_observed:
  maximum value observed for each run/analyte

time_selected:
  value at a user-selected time, using interpolation if allowed

plateau_mean:
  mean of points after plateau detection
```

Launch default:

```text
final_observed
```

Linear interpolation may be used for `time_selected` only when:

```text
- the selected time lies within observed time bounds;
- at least one observation exists before and after selected time;
- interpolation is recorded in the artifact.
```

### 9.4 Plateau Detection

Plateau detection is optional at launch and deterministic when used.

Method:

```text
1. Sort points by time.
2. Calculate local slopes between adjacent points.
3. Convert slopes to absolute percent change per unit time relative to maximum observed value.
4. Identify the earliest window of at least three consecutive points where absolute percent change is <= threshold.
5. Return the mean response in that window.
```

Defaults:

```text
threshold = 2 percent of max response per hour
minimum_plateau_points = 3
```

Warnings:

```text
- insufficient time points
- non-monotonic trajectory
- plateau not detected
- endpoint chosen by final_observed fallback
```

## 10. IVT Theoretical Yield and Relative Yield

### 10.1 Construct Metadata

Accepted construct inputs:

```text
- full RNA sequence
- nucleotide counts: A, C, G, U
- transcript length
- poly(A) tail length
- molecular weight override
- construct ID
```

Validation:

```text
- Sequence characters must be A, C, G, U, T, or supported modified nucleotide aliases.
- DNA-style T is converted to U only when user confirms or template type is declared.
- Counts must sum to transcript length.
- If full sequence and counts are both supplied, they must agree.
- Molecular weight override must be positive and include units.
```

### 10.2 Default Molecular Weight Calculation

Default RNA residue masses:

```text
A residue: 329.21 g/mol
C residue: 305.18 g/mol
G residue: 345.21 g/mol
U residue: 306.17 g/mol
```

Default molecular weight approximation:

```text
MW = n_A * 329.21 + n_C * 305.18 + n_G * 345.21 + n_U * 306.17 + terminal_adjustment
```

Default terminal adjustment:

```text
terminal_adjustment = 159.0 g/mol
```

Rules:

```text
- If user supplies molecular weight, use it and record override.
- If exact chemistry matters, user-supplied molecular weight is preferred.
- Modified nucleotides require user-supplied residue masses or molecular weight override.
- The artifact must record the residue mass table used.
```

### 10.3 Limiting NTP and Theoretical Yield

For each NTP species with count greater than zero:

```text
transcript_molar_limit_i = c_i / n_i
```

where:

```text
c_i = initial molar concentration of NTP i, mol/L
n_i = number of residues of nucleotide i in the transcript
```

The limiting NTP is:

```text
limiting_ntp = argmin(transcript_molar_limit_i)
```

Maximum transcript molarity:

```text
c_mrna_max = min(transcript_molar_limit_i)
```

Theoretical mass yield:

```text
theoretical_yield_g_per_L = c_mrna_max * MW_g_per_mol
```

If NTP concentration is supplied as individual equimolar concentration, use that concentration for A, C, G, and U. If concentrations differ by NTP, use the supplied per-NTP values.

### 10.4 Relative Yield

Relative yield:

```text
relative_yield_percent = 100 * measured_yield_g_per_L / theoretical_yield_g_per_L
```

Validation:

```text
- theoretical_yield_g_per_L must be positive.
- measured_yield_g_per_L must be non-negative.
- relative yield > 100 percent is allowed but must warn that measured yield exceeds theoretical estimate.
- relative yield cannot be calculated when sequence/composition or NTP concentration is missing.
```

Artifact fields:

```text
- construct_id
- nucleotide_counts
- molecular_weight
- residue_mass_table
- ntp_concentrations
- limiting_ntp
- theoretical_yield
- measured_yield
- relative_yield_percent
- warnings
```

## 11. Response-Surface Modeling

### 11.1 Model Formula

Models are specified by:

```text
response ~ terms
```

Supported terms:

```text
- intercept
- main effects
- two-factor interactions
- square terms for continuous variables
- declared transforms
- block terms
- categorical treatment-coded terms
```

The model artifact must store:

```text
- human-readable formula
- parsed term list
- encoded column names
- transform and coding metadata
- rows included and excluded
- exclusion reasons
```

### 11.2 Ordinary Least Squares

Default fitting method:

```text
ordinary least squares
```

Fit:

```text
b = argmin sum((y - X*b)^2)
```

Implementation:

```text
- Use QR decomposition or SVD-based least squares.
- Do not invert X'X directly for fitting.
- Use pseudo-inverse only when rank deficiency is explicitly reported.
```

Rank handling:

```text
- If rank(X) < p, mark model as rank deficient.
- Coefficients for non-estimable terms must be omitted or marked non-estimable.
- Tool must warn and prevent downstream optimization unless user explicitly allows weak model use.
```

### 11.3 Weighted and Robust Options

Launch optional methods:

```text
- weighted least squares when row weights are supplied
- heteroscedasticity-robust standard errors when supported by implementation
```

Rules:

```text
- Row weights must be positive.
- Robust standard errors change uncertainty estimates, not fitted coefficients.
- The artifact must identify the covariance method used.
```

### 11.4 Residual Diagnostics

Required residual outputs:

```text
- residuals by row
- fitted values by row
- standardized residuals when possible
- leverage values when possible
- Cook's distance when possible
- RMSE
- residual mean
- residual standard deviation
```

Warnings:

```text
- high leverage
- large standardized residual
- sparse categorical levels
- missing replicate error estimate
- non-estimable terms
- model over-parameterized for row count
```

Default warning thresholds:

```text
high_leverage: leverage > 2p/n
large_standardized_residual: absolute standardized residual > 3
high_cooks_distance: Cook's distance > 4/n
```

### 11.5 R2 and Adjusted R2

Definitions:

```text
SSE = sum((y_i - y_hat_i)^2)
SST = sum((y_i - mean(y))^2)
R2 = 1 - SSE/SST
adjusted_R2 = 1 - ((SSE/(n-p)) / (SST/(n-1)))
```

Validation:

```text
- R2 is undefined if SST = 0.
- adjusted R2 is undefined if n <= p.
- Undefined metrics must be null with warnings, not zero.
```

### 11.6 Cross-Validated Predictive Score

Default launch predictive metric:

```text
leave-one-out Q2
```

PRESS:

```text
PRESS = sum((y_i - y_hat_minus_i)^2)
```

where `y_hat_minus_i` is the prediction for row i from a model fit without row i.

Q2:

```text
Q2 = 1 - PRESS/SST
```

Rules:

```text
- If n is too small to refit models, Q2 is undefined with warning.
- If any leave-one-out fit is rank deficient, Q2 is undefined unless fallback is explicitly allowed.
- K-fold cross-validation may be used when n is large enough and the seed is recorded.
```

Default K-fold rules:

```text
k = min(5, n)
shuffle = true
seed required
```

### 11.7 Lack-of-Fit and Pure Error

Lack-of-fit testing requires replicated factor settings.

Definitions:

```text
SSPE = sum within-replicate squared deviations
SSLOF = SSE - SSPE
df_pe = n - number_of_unique_factor_settings
df_lof = number_of_unique_factor_settings - p
MSPE = SSPE / df_pe
MSLOF = SSLOF / df_lof
F = MSLOF / MSPE
```

Rules:

```text
- If no replicated settings exist, lack-of-fit is unavailable.
- If df_pe <= 0 or df_lof <= 0, lack-of-fit is unavailable.
- The artifact must distinguish "not significant lack-of-fit" from "lack-of-fit unavailable."
```

### 11.8 Prediction Intervals

For OLS with valid covariance:

Mean prediction standard error:

```text
se_mean = sqrt(x0' * Cov(b) * x0)
```

Observation prediction standard error:

```text
se_pred = sqrt(MSE + x0' * Cov(b) * x0)
```

Prediction interval:

```text
y_hat +/- t_quantile * se_pred
```

Rules:

```text
- Prediction intervals require residual degrees of freedom > 0.
- Prediction intervals must not be reported outside supported model domain without extrapolation warning.
- Dashboard must label confidence bands versus prediction bands distinctly.
```

## 12. Effect Analysis and Prediction Grids

### 12.1 Coefficient Effects

For coded continuous factors, coefficient magnitude may be used as a standardized effect proxy when:

```text
- factors are centered and scaled;
- model has no unsupported rank issues;
- response has not been transformed in a way that changes interpretation without warning.
```

The artifact must store:

```text
- term
- coefficient
- standard error when available
- effect sign
- effect magnitude
- response
- warnings
```

### 12.2 Pareto Effects

Pareto chart payload:

```text
response
term
effect_value
absolute_effect_value
rank
sign
statistical_threshold when available
warnings
```

Rules:

```text
- Do not draw a statistical significance threshold unless the model supports it.
- If p-values are unavailable, use "effect magnitude ranking" language.
```

### 12.3 Factor-Response Curves

For each selected factor and response:

```text
1. Generate a grid over the selected factor.
2. Hold other factors by declared hold strategy.
3. Predict response at grid points.
4. Attach uncertainty bands when supported.
```

Hold strategies:

```text
center
best_observed
user_specified
reference_condition
```

Rules:

```text
- Hold values must be recorded.
- Predictions outside factor bounds are forbidden unless extrapolation is explicitly requested.
- Categorical factors use one curve per selected level or a selected reference level.
```

### 12.4 Contour Grids

Contour grids vary two factors and hold others fixed.

Defaults:

```text
points_per_axis = 50
hold_strategy = center
```

Output:

```text
- factor_x
- factor_y
- grid_x
- grid_y
- predicted_response
- uncertainty when available
- hold_values
- infeasible_mask
- extrapolation_mask
```

Rules:

```text
- Constraint violations must be masked.
- Predictions must preserve raw, transformed, and coded factor metadata.
```

## 13. Optional Cost and Cost-Efficiency Methods

### 13.1 Economics Availability Rule

Economics is available only when the user supplies direct component costs.

If costs are absent:

```text
economics_status = skipped_missing_component_costs
cogs_results = []
warnings include: "Cost efficiency was not calculated because component costs were not supplied."
```

The tool must continue returning non-economic study outputs.

### 13.2 Component Cost Input

Required fields:

```text
component_name
unit_cost
currency
cost_basis_unit
factor_mapping or fixed_amount_per_batch
```

Optional fields:

```text
amount_unit
price_low
price_high
conversion_factor
notes
```

Validation:

```text
- unit_cost must be positive.
- currency must be non-empty.
- cost_basis_unit must be parseable.
- Mixed currencies require explicit conversion rates.
- Component rows must map to a factor, fixed amount, or derived amount formula.
- Unknown factor mappings are errors.
```

### 13.3 Cost Per Condition

For each condition:

```text
component_cost = component_amount * unit_cost_after_conversion
total_condition_cost = sum(component_costs) + fixed_costs
```

Amount resolution order:

```text
1. fixed_amount_per_batch
2. factor_mapping value converted to cost basis
3. named derived amount formula
```

The artifact must store:

```text
- total_condition_cost
- cost_breakdown_by_component
- currency
- amount assumptions
- unit conversions
- missing mappings
- cost_inputs_hash
```

### 13.4 Cost Efficiency

Supported metrics:

```text
mass_per_currency
currency_per_mass
```

Mass per currency:

```text
cost_efficiency = product_mass / total_condition_cost
```

Currency per mass:

```text
cost_per_mass = total_condition_cost / product_mass
```

Product mass source order:

```text
1. measured endpoint product mass
2. measured concentration * batch volume
3. predicted concentration * batch volume
```

Rules:

```text
- Product mass must be positive.
- If measured and predicted values both exist, measured is used by default and predicted is retained for comparison.
- The source of product mass must be recorded.
- Cost efficiency must not be calculated from yield alone unless batch volume or equivalent basis is available.
```

### 13.5 Sensitivity

When price ranges are supplied:

```text
component_cost_low = component_amount * price_low
component_cost_high = component_amount * price_high
```

Sensitivity output:

```text
- low_total_cost
- high_total_cost
- low_cost_efficiency
- high_cost_efficiency
- dominant_cost_drivers
```

Dominant cost drivers are components whose mean contribution is at least 20% of total cost or in the top three contributions, whichever yields more components.

### 13.6 Prohibited Economics Behavior

The MCP server and Codex workflow must not:

```text
- fetch reagent prices from the web;
- infer prices from vendor names;
- apply default prices;
- convert currencies without explicit conversion rates;
- describe model-based estimates as validated COGS;
- claim cost improvement without a defined baseline and comparison condition.
```

## 14. Desirability and Optimization

### 14.1 Response Goal Functions

Each response receives an individual desirability score `d_i` in [0, 1].

Maximize:

```text
d_i = 0 if y <= low
d_i = ((y - low) / (target - low))^s if low < y < target
d_i = 1 if y >= target
```

Minimize:

```text
d_i = 1 if y <= target
d_i = ((high - y) / (high - target))^s if target < y < high
d_i = 0 if y >= high
```

Target:

```text
d_i = 0 outside [low, high]
d_i rises from low to target and falls from target to high
```

Range:

```text
d_i = 1 inside [low, high]
d_i = 0 outside hard bounds, unless soft shoulders are configured
```

Default shape exponent:

```text
s = 1
```

### 14.2 Composite Desirability

Composite desirability:

```text
D = product(d_i ^ w_i) ^ (1 / sum(w_i))
```

Rules:

```text
- Weights must be positive.
- A hard quality constraint violation sets D = 0.
- Missing response prediction excludes the candidate unless user allows incomplete scoring.
- Cost efficiency can be included only when economics_status = calculated.
```

### 14.3 Candidate Recommendation

Recommendation workflow:

```text
1. Generate feasible candidate set.
2. Remove duplicates of existing runs unless repeats are allowed.
3. Predict responses for each candidate.
4. Calculate desirability and constraint status.
5. Add exploration bonus when configured.
6. Rank candidates.
7. Return top n recommendations with rationale.
```

Exploration bonus:

```text
score = desirability + exploration_weight * normalized_uncertainty
```

Rules:

```text
- uncertainty must be normalized to [0, 1].
- exploration_weight default = 0.2.
- Recommendations must include whether the rationale is exploitation, exploration, or constraint-probing.
```

### 14.4 Extrapolation Control

Candidates outside the validated factor space are excluded by default.

Candidates inside bounds but far from observed data must be flagged when:

```text
distance_to_nearest_observed > 90th percentile of observed nearest-neighbor distances
```

The distance calculation uses coded continuous factors and one-hot categorical factors.

## 15. Quality Design-Space Probability

### 15.1 Quality Threshold

A quality threshold is defined as:

```text
response_name
operator
threshold
units
hard_constraint
```

Example:

```text
dsrna_score < 3
```

### 15.2 Monte Carlo Probability of Failure

For each grid point or candidate condition:

```text
1. Generate N perturbed factor settings around the nominal condition.
2. Reject perturbations outside allowed factor bounds unless boundary clipping is configured.
3. Predict quality response for each perturbation.
4. Count failures against threshold.
5. probability_of_failure = failures / valid_simulations
```

Default settings:

```text
N = 10000
factor_noise = 5 percent of factor range
noise_distribution = normal
random_seed required
failure_limit = 1 percent
```

Rules:

```text
- Perturbation settings must be recorded.
- Number of valid simulations must be recorded.
- If valid simulations < 90% of N, warn about boundary effects.
- If model prediction is unavailable or rank deficient, probability map is unavailable.
```

### 15.3 Prediction Uncertainty Mode

Two modes are supported:

```text
factor_perturbation_only
factor_and_prediction_uncertainty
```

In `factor_and_prediction_uncertainty` mode:

```text
predicted_y_sample = predicted_mean + random_normal(0, prediction_standard_error)
```

This mode requires valid prediction standard errors.

### 15.4 Design-Space Classification

Classification:

```text
in_design_space if probability_of_failure <= failure_limit
outside_design_space if probability_of_failure > failure_limit
unknown if probability cannot be calculated
```

Output payload:

```text
- grid factors
- nominal settings
- probability_of_failure
- classification
- threshold
- simulation_settings
- warnings
```

## 16. Verification-Run Planning

### 16.1 Verification Run Types

Supported verification run types:

```text
predicted_optimum
design_space_corner
design_space_edge
quality_boundary_probe
center_point
replicate_control
model_disagreement_probe
```

### 16.2 Planning Method

Workflow:

```text
1. Confirm fitted model exists.
2. Confirm factor space and constraints exist.
3. Confirm response goals and quality thresholds exist.
4. Generate candidate verification points.
5. Remove duplicate or infeasible points.
6. Score points by verification value.
7. Return requested number of runs with rationale.
```

Verification value considers:

```text
- proximity to predicted optimum
- proximity to design-space boundary
- predicted quality risk
- prediction uncertainty
- coverage of factor directions
- feasibility constraints
```

### 16.3 Design-Space Corners

For a continuous two-dimensional design-space view:

```text
- Identify feasible grid cells classified as in_design_space.
- Find boundary hull or approximate extreme cells.
- Select points near extremes while respecting all factor constraints.
```

For more than two factors:

```text
- Use candidate-set extremes in coded factor space.
- Prefer points that vary one or more factors around the optimum.
- Avoid points with high predicted failure unless boundary probing is explicitly requested.
```

### 16.4 Prediction Interval Verification

When verification observations are later supplied:

```text
within_interval = lower_prediction_bound <= observed <= upper_prediction_bound
prediction_error = observed - predicted
relative_error = prediction_error / observed_scale
```

The artifact must report:

```text
- prediction used
- interval type
- observed value
- error
- within interval
- whether result supports or challenges model
```

## 17. Construct-Transfer Methods

### 17.1 Launch Foundation

At launch, construct-transfer support means preserving metadata and preventing unsupported claims.

Required stored metadata:

```text
- construct_id
- transcript_length
- nucleotide_counts
- molecular_weight
- DNA template molarity when available
- original DNA template mass concentration
- sequence source
- yield units
```

Launch behavior:

```text
- The product may compare construct metadata.
- The product may calculate theoretical yield for each construct.
- The product may normalize DNA template mass concentration to molarity when molecular weight is available.
- The product must not claim predictive transfer across constructs unless a transfer model has been fit or explicitly selected.
```

### 17.2 Molarity Normalization

DNA or RNA mass concentration to molarity:

```text
molarity_mol_per_L = concentration_g_per_L / molecular_weight_g_per_mol
```

For ng/uL:

```text
concentration_g_per_L = concentration_ng_per_uL * 1e-3
```

because:

```text
1 ng/uL = 1 mg/L = 1e-3 g/L
```

### 17.3 Transfer Model Modes

Supported post-launch transfer modes:

```text
molarity_only
length_time_scaled
user_supplied_scaling
```

`molarity_only`:

```text
- Convert mass concentrations to molar concentrations.
- Compare model predictions on molar basis.
- Do not alter time axis.
```

`length_time_scaled`:

```text
- Convert mass concentrations to molar concentrations.
- Scale time by transcript length ratio.
- Record scaling direction and assumption.
```

Default length time scaling:

```text
equivalent_time_new = reference_time * (new_length / reference_length)
```

This assumes elongation-related duration scales with transcript length. If the workflow assumes initiation/termination dominance, use `molarity_only` instead.

`user_supplied_scaling`:

```text
- User provides explicit time or rate scaling factor.
- Artifact records source and rationale.
```

### 17.4 Transfer Warnings

Always warn when:

```text
- construct length differs by more than 2x;
- nucleotide composition differs materially;
- modified nucleotides differ;
- cap/poly(A) strategy differs;
- enzyme, buffer, temperature, counterion, or reaction format differs;
- transfer predictions are not experimentally validated.
```

Material nucleotide composition difference:

```text
sum(abs(fraction_i_new - fraction_i_ref)) > 0.10
```

## 18. Numerical Reproducibility

### 18.1 Seeds

All stochastic methods require explicit or generated seeds.

Seeded methods:

```text
- Latin hypercube sampling
- D-optimal random starts
- Monte Carlo design-space simulation
- cross-validation fold assignment
- recommendation exploration sampling
```

Rules:

```text
- Generated seeds must be stored.
- Re-running with same inputs, versions, and seed must reproduce outputs within tolerance.
- Artifact hashes must include seed and method settings.
```

### 18.2 Numeric Tolerances

Default tolerances:

```text
absolute_tolerance = 1e-9 for dimensionless algorithmic checks
relative_tolerance = 1e-6 for floating point scientific outputs
display_rounding = response-specific and never used for stored values
```

Model comparison tolerances:

```text
coefficient_relative_tolerance = 1e-5
prediction_relative_tolerance = 1e-5
metric_absolute_tolerance = 1e-6
```

DOE reproducibility:

```text
- Exact row order is reproducible when randomization is disabled.
- Randomized row order is reproducible with seed.
- D-optimal designs may have equivalent alternatives; tests should compare criterion and rank, not only row identity, unless seed and algorithm are pinned.
```

### 18.3 Version Capture

Every scientific artifact must record:

```text
- tool name
- tool version
- method version
- schema version
- Python version
- package versions for numerical libraries
- operating system
- random seed when used
```

## 19. Artifact Contracts

### 19.1 Required Artifact Metadata

Every artifact must include:

```text
study_id
run_id
artifact_type
schema_version
method_version
generated_at
input_hash
artifact_hash
warnings
```

### 19.2 Warning Severity

Warning severities:

```text
info
warning
blocking
```

Blocking warnings prevent downstream use unless the user explicitly overrides and the method allows override.

Blocking examples:

```text
- invalid factor bounds
- empty feasible candidate set
- rank-deficient model for optimization
- missing component costs for requested cost calculation
- unknown categorical level
```

Non-blocking examples:

```text
- high condition number
- relative yield above 100 percent
- weak Q2
- lack-of-fit unavailable
- economics unavailable because costs were not supplied
```

### 19.3 Audit Log Entries

Each tool call writes one audit entry:

```text
timestamp
study_id
run_id
tool_name
tool_version
method_version
input_hash
output_hash
status
warnings
errors
duration_ms
seed
artifact_paths
```

## 20. Scientific Validation Fixtures

### 20.1 DOE Fixtures

Required tests:

```text
- full factorial run count equals product of levels.
- fractional factorial reports aliasing or unsupported alias diagnostics.
- Latin hypercube covers every factor interval once.
- D-optimal design returns full-rank matrix when n_runs >= p and candidate set supports requested terms.
- D-optimal augmentation does not modify locked existing rows.
- D-optimal failure reports terms that are not estimable.
```

### 20.2 Modeling Fixtures

Required tests:

```text
- OLS recovers known coefficients from synthetic noiseless data.
- Rank-deficient design is detected.
- R2, adjusted R2, RMSE, and Q2 match hand-calculated fixtures.
- Lack-of-fit is unavailable without replicated settings.
- Lack-of-fit calculation matches hand fixture when replicates exist.
- Prediction intervals are unavailable when residual degrees of freedom are insufficient.
```

### 20.3 IVT Yield Fixtures

Required tests:

```text
- Sequence parser counts A, C, G, U correctly.
- T is converted to U only under declared DNA-style input mode.
- Molecular weight calculation matches residue-mass fixture.
- Limiting NTP is correctly identified.
- Theoretical yield matches hand calculation.
- Relative yield refuses missing theoretical yield.
- Relative yield above 100 percent produces warning, not failure.
```

### 20.4 Cost Fixtures

Required tests:

```text
- Missing component costs skips economics.
- Missing unit_cost fails cost calculation.
- Mixed currencies fail without conversion rates.
- Factor-mapped component cost changes by condition.
- Fixed batch cost is applied to every condition.
- Cost efficiency uses measured product mass before predicted product mass.
- Cost improvement claim requires baseline.
```

### 20.5 Design-Space Fixtures

Required tests:

```text
- Quality threshold parsing supports dsRNA < 3.
- Monte Carlo probability is reproducible with seed.
- Probability-of-failure classification follows configured failure limit.
- Boundary clipping warning appears when valid simulations fall below threshold.
```

### 20.6 Verification Fixtures

Required tests:

```text
- Predicted optimum verification run is generated when fitted model and objectives exist.
- Boundary verification runs require quality threshold or design-space map.
- Duplicate verification points are removed.
- Verification observation comparison correctly reports within prediction interval.
```

## 21. Launch Method Readiness Matrix

| Method | Launch Requirement | Launch Behavior | Post-Launch Expansion |
| --- | --- | --- | --- |
| Factor validation | Required | Full validation for continuous, categorical, ordinal, fixed | Mixture design validation |
| Full factorial | Required | Small feasible spaces | Larger sparse storage |
| Fractional factorial | Required | Two-level screening | Mixed-level fractions |
| Latin hypercube | Required | Continuous space filling | Advanced optimal space filling |
| D-optimal design | Required | Candidate-set selection and augmentation metadata | Full locked-row augmentation and more optimality criteria |
| Endpoint modeling | Required | OLS response surfaces | GLM and nonlinear models |
| Time-resolved data | Required | Import, plot, endpoint summaries | Rich kinetic models |
| Theoretical yield | Required for IVT when sequence/composition supplied | Residue-mass calculation and limiting NTP | Modified nucleotide libraries |
| Cost efficiency | Required when costs supplied | Direct component-cost calculation | Full scenario COGS |
| Desirability | Required | Multi-response scoring | Bayesian or expected-improvement strategies |
| Design-space probability | Foundation required | Threshold schema and unavailable state unless run | Full Monte Carlo maps |
| Verification planning | Required | Optimum and boundary/corner recommendations | Closed-loop verification analysis |
| Construct transfer | Foundation required | Metadata and molarity normalization | Transfer prediction model |

## 22. Scientific Interpretation Rules for Codex

Codex summaries must follow these rules:

```text
- State which tool produced each numerical result.
- State when a result is measured, derived, predicted, or recommended.
- State model warnings before optimization recommendations.
- Never call a model causal unless the study design and user context support causal language.
- Never claim a design space is verified until verification observations have been compared.
- Never claim cost savings unless component costs, baseline, comparison condition, and product mass basis exist.
- Use "model predicts" for fitted model outputs.
- Use "not calculated" rather than "not applicable" when required inputs are missing.
```

## 23. Method Change Control

Any change to a scientific method must update:

```text
1. Method version.
2. Schema contract if inputs or outputs change.
3. Golden fixtures.
4. Dashboard payload expectations.
5. Skill instructions if user-facing workflow changes.
6. Release notes describing scientific impact.
```

Backward compatibility:

```text
- Existing artifacts must remain readable.
- If method outputs change materially, dashboard must show method version.
- Recomputed results must not silently overwrite old artifacts.
```
