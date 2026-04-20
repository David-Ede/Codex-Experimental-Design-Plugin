# IVT/QbD Workflow Spec: Paper-Class mRNA DOE Analysis

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Scientific Methods Spec.md
- Data & Schema Contract.md
- MCP Tool API Spec.md
- Canonical Build Contract.md
```

## 1. Purpose

This document defines the end-to-end IVT mRNA quality-by-design workflow that the Codex Scientific Toolchain must support. It translates the product requirements, scientific methods, data contracts, and MCP tool APIs into an operational workflow that a scientist can run inside Codex.

The workflow target is a paper-class IVT optimization study: iterative DOE, response-surface modeling, time-resolved assay data, theoretical and relative yield, dsRNA quality constraints, optional user-priced cost efficiency, next-experiment planning, verification runs, construct-transfer support, and counterion follow-up analysis.

This document is not a general DOE primer. It is the product workflow contract for the IVT/QbD template.

## 2. Workflow Goals

The IVT/QbD workflow must let a user:

```text
1. Define an IVT reaction knowledge space.
2. Generate an initial D-optimal or fallback optimal-screening DOE.
3. Import endpoint and time-resolved assay data.
4. Calculate theoretical and relative yield from sequence or nucleotide composition.
5. Fit MLR response-surface models for yield, dsRNA, relative yield, and optional cost efficiency.
6. Analyze factor effects, interactions, response curves, and contours.
7. Calculate cost efficiency only from direct user-provided component costs.
8. Identify quality-constrained operating regions.
9. Recommend next experiments and verification runs.
10. Preserve construct metadata for transfer analysis.
11. Support a counterion follow-up DOE.
12. Refresh a local dashboard after each material analytical step.
```

## 3. Non-Goals

The workflow must not:

```text
- clone proprietary MODDE projects;
- claim exact reproduction of a paper without the paper's raw data and supporting tables;
- infer reagent costs or fetch external price data;
- treat cost efficiency as required for DOE or modeling;
- claim a verified design space before verification data is imported and compared;
- perform regulatory or GMP release decisions;
- hide weak model diagnostics behind optimization recommendations;
- use the React dashboard for scientific computation.
```

## 4. Workflow Actors

**User**

Provides factor ranges, response goals, assay data, sequence/composition, optional cost table, and scientific judgment.

**Codex**

Interprets intent, selects the workflow stage, calls MCP tools, explains outputs, starts preview commands, and updates code or payloads when needed.

**MCP scientific server**

Validates inputs, generates DOE matrices, imports data, computes derived responses, fits models, calculates costs, plans experiments, writes artifacts, and logs audit entries.

**React dashboard**

Renders the current study state, warnings, charts, matrix views, diagnostics, cost-efficiency views, and unavailable states.

## 5. Workflow Stages

The full IVT/QbD workflow is divided into stages:

```text
0. Study setup
1. Knowledge-space definition
2. Initial DOE generation
3. Experimental execution handoff
4. Endpoint and time-resolved data import
5. Construct and theoretical-yield processing
6. Response-surface model fitting
7. Effects, contours, and diagnostic analysis
8. Optional cost-efficiency analysis
9. Quality design-space analysis
10. Next-experiment and verification planning
11. Verification result comparison
12. Construct-transfer analysis
13. Counterion follow-up DOE
14. Final study summary and export
```

Launch must support stages 0 through 8, stage 10 at launch level, and metadata foundations for stages 11 through 13. Full paper-class readiness requires all stages.

## 6. Required Inputs by Stage

### 6.1 Minimum Inputs for Initial DOE

```text
- study title
- four IVT factors or equivalent process factors
- factor ranges and units
- response names and goals
- dsRNA threshold if dsRNA is a CQA
- target run count or run-budget preference
- model terms or acceptance of IVT template defaults
```

### 6.2 Additional Inputs for Model Fitting

```text
- endpoint observation table
- run IDs or factor settings matching design rows
- response values and units
- model terms or selected template model
- validation method preference, if not default
```

### 6.3 Additional Inputs for Time-Resolved Analysis

```text
- long-format timecourse table
- run ID
- time
- analyte
- value
- units
- analyte-to-response mapping when endpoint summaries are needed
```

### 6.4 Additional Inputs for Theoretical and Relative Yield

```text
- mRNA construct ID
- full RNA sequence or nucleotide counts
- transcript length
- molecular weight or permission to calculate approximate molecular weight
- NTP concentration source
- measured yield response, if relative yield is requested
```

### 6.5 Additional Inputs for Cost Efficiency

```text
- direct component-cost table from the user
- currency
- cost basis units
- mapping from components to factors or fixed batch amounts
- product mass or concentration plus batch volume
- baseline condition if improvement claims are requested
```

### 6.6 Additional Inputs for Verification

```text
- fitted model
- response goals
- quality thresholds
- predicted optimum or recommendation set
- design-space probability artifact, if available
- desired number of verification runs
```

### 6.7 Additional Inputs for Construct Transfer

```text
- reference construct metadata
- target construct metadata
- model fit from reference construct
- molarity adjustment metadata
- time-scaling assumption, if requested
- validation observations, if comparing transfer predictions
```

### 6.8 Additional Inputs for Counterion DOE

```text
- Mg:NTP ratio range or levels
- counterion categorical levels
- response definitions
- target run count or candidate set
- model terms including counterion main effect and optional interaction
```

## 7. Canonical IVT Study Defaults

### 7.1 Default Factors

```text
mg_ntp_ratio:
  display: Mg:NTP ratio
  kind: continuous
  units: ratio
  default range: 0.8 to 1.6

ntp_concentration:
  display: NTP concentration, individual
  kind: continuous
  units: mM
  default range: 6 to 12

dna_template:
  display: DNA template
  kind: continuous
  units: ng/uL
  default range: 10 to 100

t7_rnap:
  display: T7 RNAP
  kind: continuous
  units: U/uL
  default range: 2 to 15
```

### 7.2 Default Responses

```text
mrna_yield:
  goal: maximize
  units: g/L
  role: productivity

dsrna_score:
  goal: upper_threshold
  threshold: < 3 score
  role: CQA
  assay type: semi_quantitative

theoretical_yield:
  goal: diagnostic_only
  units: g/L
  role: derived

relative_yield:
  goal: diagnostic_only
  units: percent
  role: derived

cost_efficiency:
  goal: maximize
  units: mass/currency
  role: economics
  availability: only when component costs are supplied
```

### 7.3 Default Initial Model Terms

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

### 7.4 Full Quadratic Candidate Terms

```text
4 main effects
6 two-factor interactions
4 square terms
```

The workflow may move from the default initial model terms toward the full quadratic candidate set as new DOE iterations add information.

## 8. Stage 0: Study Setup

### 8.1 User Intent

User creates or resumes an IVT/QbD study.

Example prompt:

```text
Create an IVT QbD study for eGFP mRNA. I want to optimize yield while keeping dsRNA below 3 and optionally evaluate cost efficiency if I provide component prices.
```

### 8.2 Tool Sequence

```text
1. create_or_update_study
2. generate_dashboard_payload
3. launch_dashboard_preview, if user asks to view
```

### 8.3 Required Outputs

```text
study.json
dashboard_payload.json
audit_log.jsonl
```

### 8.4 Decision Gates

```text
- If study_id already exists, update study metadata instead of creating a duplicate unless user requests a new study.
- If no domain template is given but IVT terms are present, use ivt_qbd and warn that template defaults were applied.
```

### 8.5 Completion Criteria

```text
- Study directory exists.
- Study has a stable study_id.
- Dashboard payload can render study overview and unavailable section states.
```

## 9. Stage 1: Knowledge-Space Definition

### 9.1 User Intent

User defines factors, ranges, units, responses, quality thresholds, and optional constraints.

Example prompt:

```text
Use Mg:NTP ratio 0.8-1.6, NTP 6-12 mM, DNA 10-100 ng/uL, and T7 RNAP 2-15 U/uL. Responses are mRNA yield, dsRNA score, relative yield, and cost efficiency if costs are supplied. Keep dsRNA below 3.
```

### 9.2 Tool Sequence

```text
1. validate_factor_space
2. generate_dashboard_payload
3. launch_dashboard_preview, if visual review is requested
```

### 9.3 Required Outputs

```text
factor_space.json
responses.json
dashboard_payload.json
audit_log.jsonl
```

### 9.4 Validation Rules

```text
- Continuous factors require low, high, and units.
- dsRNA score must be represented as semi-quantitative score if using dot-blot-style 0-10 scale.
- Cost efficiency can be listed as a response, but its section remains unavailable until costs are supplied.
- Constraints must be parseable and safe.
```

### 9.5 Decision Gates

```text
- If factor ranges are missing, Codex asks for ranges before DOE.
- If response goals are missing, Codex asks for goals before optimization.
- If cost efficiency is requested but costs are absent, Codex records economics as unavailable and proceeds.
- If dsRNA threshold is absent, design-space and verification boundary workflows are limited.
```

### 9.6 Completion Criteria

```text
- Factor space is valid.
- Response set is valid.
- Quality constraints are explicit.
- Dashboard shows factor ranges, response goals, and economics availability state.
```

## 10. Stage 2: Initial DOE Generation

### 10.1 User Intent

User requests an initial experimental design.

Example prompt:

```text
Generate the first DOE iteration using a 12-run D-optimal design with the IVT default model terms.
```

### 10.2 Tool Sequence

```text
1. design_optimal_doe
2. generate_dashboard_payload
3. launch_dashboard_preview
```

Fallback sequence:

```text
1. design_optimal_doe
2. if failed and fallback allowed: design_doe
3. generate_dashboard_payload
4. launch_dashboard_preview
```

### 10.3 Required Outputs

```text
designs/<design_id>/design_matrix.csv
designs/<design_id>/design_metadata.json
designs/<design_id>/candidate_set.metadata.json
dashboard_payload.json
audit_log.jsonl
```

### 10.4 D-Optimal Requirements

The initial IVT DOE should use:

```text
- candidate-set D-optimal design where feasible;
- 12 runs when the requested model is estimable or explicitly accepted as a screening iteration;
- IVT default model terms unless the user supplies terms;
- randomization order with seed;
- diagnostics for rank, condition number, log determinant, and estimable terms.
```

### 10.5 Decision Gates

```text
- If target_runs < model columns, fail or ask to increase runs/drop terms.
- If D-optimal design cannot estimate requested terms, show terms_not_estimable.
- If fallback design is used, explain scientific implications.
- If run count exceeds user budget, propose model-term reduction or augmentation plan.
```

### 10.6 Dashboard Requirements

Dashboard must show:

```text
- experiment matrix
- factor columns and units
- randomized execution order
- design diagnostics
- estimable and non-estimable terms
- warnings and fallback reasons
- empty model/effects/cost sections with clear unavailable states
```

### 10.7 Completion Criteria

```text
- User has a reviewable DOE matrix.
- Matrix can be exported or read as CSV.
- Diagnostics are sufficient to understand what the design supports.
- No model or cost claims are made before data exists.
```

## 11. Stage 3: Experimental Execution Handoff

### 11.1 Purpose

The product does not run lab experiments. It prepares an execution-ready matrix and preserves run IDs so later observations can be joined correctly.

### 11.2 Required Handoff Content

```text
- run_id
- randomization_order
- factor settings
- units
- block and replicate labels
- run_type
- notes for constraints or special handling
```

### 11.3 User-Facing Guidance

Codex may summarize:

```text
- number of runs;
- factors varied;
- center points or controls;
- randomization order;
- what responses must be measured;
- which assay columns should be included on import.
```

Codex must not provide wet-lab procedural instructions beyond reflecting user-provided experimental plans and the DOE matrix. The workflow is for study design and analysis, not lab protocol authoring.

### 11.4 Completion Criteria

```text
- DOE matrix includes stable run IDs.
- Observations can later join by run_id or factor settings.
- Dashboard and artifacts distinguish planned rows from observed rows.
```

## 12. Stage 4: Endpoint and Time-Resolved Data Import

### 12.1 User Intent

User provides experimental observations.

Example prompt:

```text
I added observed_data.csv and timecourse.csv for this DOE. Import them, derive endpoint mRNA yield from the final time point, and refresh the dashboard.
```

### 12.2 Tool Sequence

```text
1. import_endpoint_observations, if endpoint table exists
2. import_time_resolved_observations, if timecourse table exists
3. generate_dashboard_payload
4. launch_dashboard_preview
```

### 12.3 Required Outputs

```text
observations/endpoint_observations.csv
observations/endpoint_observations.metadata.json
observations/time_resolved_observations.csv, when supplied
observations/time_resolved_observations.metadata.json, when supplied
derived/endpoint_summary.json, when derived
dashboard_payload.json
audit_log.jsonl
```

### 12.4 Endpoint Import Requirements

Endpoint data must map to:

```text
- run_id or full factor settings;
- response columns;
- response units;
- replicate labels when present;
- observed_at timestamps when present.
```

### 12.5 Time-Resolved Import Requirements

Time-resolved data must use long format:

```text
run_id
time
time_unit
analyte
value
value_unit
```

The workflow supports HPLC-like analytes generically:

```text
- mRNA concentration
- ATP remaining
- GTP remaining
- UTP/CTP remaining
- other user-defined analytes
```

### 12.6 Endpoint Summary Methods

Allowed methods:

```text
final_observed
max_observed
time_selected
plateau_mean
```

Launch default:

```text
final_observed
```

### 12.7 Decision Gates

```text
- If imported factor values differ from design rows, warn and preserve data.
- If response units are missing, warn and block calculations that require unit conversion.
- If timecourse data has duplicate run/analyte/time rows without replicate IDs, fail validation.
- If endpoint summary cannot be derived, preserve raw timecourse and mark endpoint summary unavailable.
```

### 12.8 Dashboard Requirements

Dashboard must show:

```text
- imported endpoint table status;
- timecourse availability;
- time-course plots by run and analyte;
- endpoint summary method;
- missing-value warnings;
- observed vs planned run coverage.
```

### 12.9 Completion Criteria

```text
- Observation artifacts are normalized and validated.
- Raw imported data is preserved.
- Endpoint summaries are separate derived artifacts.
- Dashboard can display measured and missing responses.
```

## 13. Stage 5: Construct and Theoretical-Yield Processing

### 13.1 User Intent

User supplies sequence, nucleotide counts, or construct metadata so the product can calculate theoretical and relative yield.

Example prompt:

```text
Register this eGFP construct as 995 nt with a 45 nt poly(A) tail. Use the supplied nucleotide counts to calculate theoretical yield and relative yield for each run.
```

### 13.2 Tool Sequence

```text
1. register_construct
2. calculate_theoretical_yield
3. generate_dashboard_payload
4. launch_dashboard_preview, if requested
```

### 13.3 Required Outputs

```text
constructs.json
derived/theoretical_yield.json
dashboard_payload.json
audit_log.jsonl
```

### 13.4 Required Inputs

At least one of:

```text
- full sequence
- nucleotide counts plus transcript length
```

Additional required inputs for theoretical yield:

```text
- NTP concentration source
- molecular weight or accepted approximate molecular weight calculation
```

Additional required input for relative yield:

```text
- measured yield response or endpoint summary mapped to yield
```

### 13.5 Decision Gates

```text
- If sequence and counts conflict, block calculation.
- If modified nucleotides lack masses, require molecular weight override or residue masses.
- If NTP concentration is missing, theoretical yield is unavailable.
- If measured yield is missing, theoretical yield can be calculated but relative yield is unavailable.
- If relative yield exceeds 100%, warn rather than fail.
```

### 13.6 Dashboard Requirements

Dashboard must show:

```text
- construct ID and length;
- sequence/count source;
- limiting NTP by run;
- theoretical yield by run;
- relative yield by run when measured yield exists;
- warnings for missing sequence, missing NTP, or relative yield above 100%.
```

### 13.7 Completion Criteria

```text
- Construct metadata is stored.
- Theoretical yield is calculated or explicitly unavailable.
- Relative yield is calculated or explicitly unavailable.
- Derived responses are available for model fitting when valid.
```

## 14. Stage 6: Response-Surface Model Fitting

### 14.1 User Intent

User asks to fit models for yield, dsRNA, relative yield, and any other available responses.

Example prompt:

```text
Fit mRNA yield, dsRNA score, and relative yield using the IVT default model terms. Report R2, Q2, model warnings, and refresh the dashboard.
```

### 14.2 Tool Sequence

```text
1. fit_response_surface
2. generate_dashboard_payload
3. launch_dashboard_preview, if requested
```

If endpoint data came from time-resolved observations:

```text
1. import_time_resolved_observations
2. calculate_theoretical_yield, if relative yield depends on endpoint summary
3. fit_response_surface
4. generate_dashboard_payload
```

### 14.3 Required Outputs

```text
models/<fit_id>/model_fit.json
models/<fit_id>/residuals.csv
models/<fit_id>/predictions.csv
dashboard_payload.json
audit_log.jsonl
```

### 14.4 Launch Model Requirements

Launch fitting must support:

```text
- OLS response-surface models;
- main effects;
- two-factor interactions;
- continuous square terms;
- declared transforms;
- treatment-coded categorical factors when present;
- R2, adjusted R2, RMSE, Q2 or explicit Q2 unavailable state;
- residual diagnostics;
- rank and condition-number warnings.
```

### 14.5 Decision Gates

```text
- If rows are insufficient for requested terms, block or ask to reduce terms.
- If model matrix is rank deficient, block downstream optimization by default.
- If Q2 is weak, allow effects visualization but warn before optimization.
- If lack-of-fit is unavailable because replicates are absent, state that clearly.
- If a response is semi-quantitative, label model interpretation accordingly.
```

### 14.6 Dashboard Requirements

Dashboard must show:

```text
- model formula by response;
- coefficient table;
- R2 and Q2;
- residual warnings;
- rank and condition-number diagnostics;
- response availability;
- whether each model is suitable for optimization.
```

### 14.7 Completion Criteria

```text
- Fitted model artifacts exist for requested responses or explicit errors explain why not.
- Model warnings are visible before effects and optimization.
- Codex summary distinguishes measured, derived, and modeled responses.
```

## 15. Stage 7: Effects, Contours, and Diagnostics

### 15.1 User Intent

User asks to understand factor effects, interactions, and response surfaces.

Example prompt:

```text
Explain the main effects and interactions. Show Pareto charts and a contour for Mg:NTP ratio vs NTP concentration on yield and dsRNA.
```

### 15.2 Tool Sequence

```text
1. analyze_effects
2. generate_dashboard_payload
3. launch_dashboard_preview
```

### 15.3 Required Outputs

```text
derived/effects.json
derived/prediction_grids.json, when curves or contours are requested
dashboard_payload.json
audit_log.jsonl
```

### 15.4 Required Views

```text
- Pareto/effect ranking
- factor-response curves
- interaction slices when available
- contour grids
- diagnostics panel
- warnings panel
```

### 15.5 Decision Gates

```text
- If statistical thresholds are unavailable, label effects as magnitude-ranked.
- If prediction intervals are unavailable, do not draw confidence or prediction bands.
- If model is weak, include model warnings in every effect summary.
- If requested contour factors are invalid, fail validation.
- If predictions are masked by constraints, show infeasible regions.
```

### 15.6 Completion Criteria

```text
- Effects are generated from fitted model artifacts.
- Plots are traceable to prediction grid artifacts.
- User can identify which terms appear influential and which claims are unsupported.
```

## 16. Stage 8: Optional Cost-Efficiency Analysis

### 16.1 User Intent

User supplies direct component costs and asks to calculate cost efficiency across conditions.

Example prompt:

```text
Use these costs: T7 RNAP 4.20 EUR/U, DNA template 0.18 EUR/ng, NTP mix 0.06 EUR/umol, and fixed buffer/reagent cost 12 EUR per batch. Calculate ug/EUR for every condition and compare to the reference run.
```

### 16.2 Tool Sequence

```text
1. calculate_cogs_impact
2. generate_dashboard_payload
3. launch_dashboard_preview
```

### 16.3 Required Outputs

When costs are supplied and valid:

```text
derived/economics.json
dashboard_payload.json
audit_log.jsonl
```

When costs are absent:

```text
audit_log.jsonl
dashboard_payload.json with economics unavailable state
```

### 16.4 Economics Rules

```text
- Cost efficiency is optional.
- DOE generation does not require costs.
- Model fitting does not require costs.
- Missing costs never block non-economic workflow stages.
- Costs must be direct user inputs.
- The product must not fetch, infer, or default prices.
- Mixed currencies require explicit conversion rates.
- Improvement claims require baseline, comparison condition, product mass basis, and user-provided costs.
```

### 16.5 Decision Gates

```text
- If component costs are absent, skip economics and proceed.
- If unit_cost, currency, or cost_basis_unit is missing, fail cost calculation.
- If component does not map to a factor or fixed amount, warn or block depending on whether total cost can still be calculated.
- If product mass is unavailable, cost efficiency is unavailable.
- If predicted product mass is used, label cost efficiency as model-predicted.
```

### 16.6 Dashboard Requirements

Dashboard must show:

```text
- economics availability state;
- cost table provenance;
- currency and cost basis;
- cost breakdown by component;
- cost efficiency by condition;
- measured vs predicted product mass source;
- baseline comparison when available;
- warning that economics is model-based and user-cost-dependent.
```

### 16.7 Completion Criteria

```text
- Cost efficiency is calculated only from user-supplied costs.
- Cost inputs hash is stored.
- Dashboard can compare cost efficiency across conditions.
- Codex summary does not overstate COGS or validated savings.
```

## 17. Stage 9: Quality Design-Space Analysis

### 17.1 User Intent

User asks to identify the operating region that satisfies a quality threshold, such as dsRNA score below 3.

Example prompt:

```text
Estimate the dsRNA design space using the fitted dsRNA model. Use 5% factor noise and classify regions with less than 1% probability of exceeding dsRNA score 3.
```

### 17.2 Tool Sequence

Launch foundation:

```text
1. analyze_effects, to generate prediction grids
2. generate_dashboard_payload
```

Full paper-class sequence:

```text
1. estimate_design_space_probability
2. generate_dashboard_payload
3. launch_dashboard_preview
```

### 17.3 Required Outputs

Launch:

```text
prediction grids and unavailable state for design-space probability if Monte Carlo not run
```

Paper-class:

```text
derived/design_space_probability.json
dashboard_payload.json
audit_log.jsonl
```

### 17.4 Decision Gates

```text
- If no quality threshold exists, design-space probability is unavailable.
- If dsRNA model is rank deficient, design-space probability is unavailable.
- If prediction uncertainty is requested but unavailable, fail or downgrade based on user choice.
- If valid Monte Carlo simulations are too few near boundaries, warn.
```

### 17.5 Dashboard Requirements

Dashboard must show:

```text
- quality threshold definition;
- contour or probability map;
- in-design-space and outside-design-space regions;
- simulation settings when Monte Carlo is available;
- unavailable state when not yet calculated;
- warnings about weak models or extrapolation.
```

### 17.6 Completion Criteria

```text
- User can see whether quality design-space analysis is available.
- If available, classification is traceable to simulation settings and model artifact.
- If unavailable, dashboard explains which model/input is missing.
```

## 18. Stage 10: Next-Experiment and Verification Planning

### 18.1 User Intent

User asks what to run next or how to verify the predicted optimum/design space.

Example prompt:

```text
Propose the next five experiments balancing yield, dsRNA, relative yield, and cost efficiency if available. Then plan seven verification runs near the predicted optimum and dsRNA boundary.
```

### 18.2 Tool Sequence

```text
1. suggest_next_experiment
2. plan_verification_runs
3. generate_dashboard_payload
4. launch_dashboard_preview
```

### 18.3 Required Outputs

```text
derived/recommendations.json
derived/verification_plan.json
dashboard_payload.json
audit_log.jsonl
```

### 18.4 Recommendation Rules

```text
- Yield, dsRNA, and relative yield can be included when modeled.
- Cost efficiency can be included only when economics_status = calculated.
- Recommendations must distinguish exploitation, exploration, and constraint-probing.
- Duplicate existing runs are removed unless repeats are requested.
- Recommendations outside factor space are excluded by default.
```

### 18.5 Verification Rules

Verification plan may include:

```text
- predicted optimum confirmation;
- design-space corner probes;
- design-space edge probes;
- quality-boundary probes;
- center points;
- replicate controls;
- model disagreement probes.
```

Launch verification planning must work without Monte Carlo probability maps by using fitted models, response goals, and quality thresholds, but must warn that probability maps are unavailable.

### 18.6 Decision Gates

```text
- If model fit is missing, recommendations and verification are unavailable.
- If model is rank deficient, downstream recommendations are blocked by default.
- If cost is requested as required but economics is unavailable, fail the economics-inclusive recommendation request.
- If dsRNA threshold is missing, quality-boundary verification cannot be planned.
- If all candidates are infeasible, return a structured failure with reasons.
```

### 18.7 Dashboard Requirements

Dashboard must show:

```text
- ranked next-experiment queue;
- factor settings;
- predicted responses;
- desirability score;
- uncertainty score;
- rationale type;
- verification plan table;
- purpose of each verification run;
- warnings and model limitations.
```

### 18.8 Completion Criteria

```text
- User receives a ranked next-run plan or clear reason why not.
- Verification runs are labeled separately from model-building runs.
- Codex explains what each verification run tests.
- No verification claim is made before observed verification results are imported.
```

## 19. Stage 11: Verification Result Comparison

### 19.1 User Intent

User imports verification observations and asks whether the model predictions held.

Example prompt:

```text
Import the verification results and compare measured yield and dsRNA to the 95% prediction intervals.
```

### 19.2 Tool Sequence

```text
1. import_endpoint_observations
2. compare_verification_results
3. generate_dashboard_payload
4. launch_dashboard_preview
```

### 19.3 Availability

```text
Post-launch / paper-class expansion
```

Launch behavior:

```text
- verification observations can be imported as endpoint observations;
- dashboard can show planned verification runs;
- interval comparison is unavailable until compare_verification_results is implemented.
```

### 19.4 Required Outputs

Paper-class:

```text
derived/verification_results.json
dashboard_payload.json
audit_log.jsonl
```

### 19.5 Decision Gates

```text
- If prediction intervals are unavailable, comparison reports predicted vs observed but not interval pass/fail.
- If verification run IDs do not match plan, warn and attempt factor-setting match only when unambiguous.
- If observed result falls outside interval, mark as challenges_model but do not automatically reject the model.
```

### 19.6 Completion Criteria

```text
- Observed verification data is linked to planned verification runs.
- Within-interval status is calculated when possible.
- Dashboard shows predicted, observed, error, and interpretation.
- Codex states whether results support, challenge, or are inconclusive for the model.
```

## 20. Stage 12: Construct-Transfer Analysis

### 20.1 User Intent

User wants to test whether a model from one mRNA construct can inform another construct.

Example prompt:

```text
Register the mFIX construct and compare it to the eGFP construct. Use molarity normalization and length-time scaling only if the assumptions are recorded.
```

### 20.2 Tool Sequence

Launch foundation:

```text
1. register_construct for reference construct
2. register_construct for target construct
3. calculate_theoretical_yield for each construct where possible
4. generate_dashboard_payload
```

Paper-class:

```text
1. transfer_construct_model
2. import_time_resolved_observations for validation data, if supplied
3. generate_dashboard_payload
4. launch_dashboard_preview
```

### 20.3 Availability

```text
Launch: metadata, theoretical yield, molarity normalization foundation
Post-launch: transfer prediction model
```

### 20.4 Decision Gates

```text
- If construct length differs by more than 2x, warn.
- If nucleotide composition differs materially, warn.
- If chemistry, cap strategy, enzyme, buffer, temperature, or reaction format differs, warn.
- If transfer model is not fit or selected, do not claim predictive transfer.
```

### 20.5 Dashboard Requirements

Dashboard must show:

```text
- construct comparison table;
- transcript length;
- nucleotide composition;
- molecular weight source;
- theoretical yield by construct;
- transfer assumptions when present;
- validation status when present.
```

### 20.6 Completion Criteria

```text
- Launch product preserves enough metadata for future transfer modeling.
- Codex does not imply transfer predictions when only metadata exists.
- Paper-class product can compare transfer predictions against validation timecourse data.
```

## 21. Stage 13: Counterion Follow-Up DOE

### 21.1 User Intent

User asks to test magnesium counterion effects, typically chloride versus acetate, across Mg:NTP settings.

Example prompt:

```text
Design a counterion DOE varying Mg:NTP ratio and Mg2+ counterion chloride vs acetate. Include the interaction term and model yield and dsRNA.
```

### 21.2 Tool Sequence

Launch-compatible generic path:

```text
1. validate_factor_space, adding mg_counterion as categorical
2. design_optimal_doe
3. import_endpoint_observations when data exists
4. fit_response_surface
5. analyze_effects
6. generate_dashboard_payload
```

Specialized paper-class path:

```text
1. analyze_counterion_doe
2. generate_dashboard_payload
3. launch_dashboard_preview
```

### 21.3 Required Factor Setup

```text
mg_ntp_ratio:
  kind: continuous or ordinal levels

mg_counterion:
  kind: categorical
  levels: chloride, acetate
```

Optional model terms:

```text
mg_ntp_ratio
mg_counterion
mg_ntp_ratio:mg_counterion
```

### 21.4 Decision Gates

```text
- If each counterion level lacks sufficient replication, warn.
- If interaction is not estimable, drop or warn based on user choice.
- If counterion levels differ in other reaction conditions, warn about confounding.
```

### 21.5 Dashboard Requirements

Dashboard must show:

```text
- counterion levels;
- response by counterion;
- interaction plot when estimable;
- model warnings;
- statement that counterion conclusions are within tested conditions.
```

### 21.6 Completion Criteria

```text
- Counterion is represented as a categorical factor.
- Model can estimate or explicitly reject counterion and interaction terms.
- Codex summary does not generalize beyond the tested range.
```

## 22. Stage 14: Final Study Summary and Export

### 22.1 User Intent

User wants a final readout of what was done, what was learned, what is verified, and what remains uncertain.

Example prompt:

```text
Summarize this IVT DOE study for review. Include design, models, dsRNA constraints, relative yield, cost efficiency if available, verification status, and next steps.
```

### 22.2 Tool Sequence

```text
1. generate_dashboard_payload
2. launch_dashboard_preview, if visual review is requested
```

Codex then summarizes from artifacts. No new scientific calculations should be performed in prose.

### 22.3 Summary Requirements

The summary must include:

```text
- study ID and active run ID;
- design iterations and run counts;
- factors and ranges;
- responses and goals;
- model formulas and diagnostics;
- important effects and interactions;
- theoretical and relative yield availability;
- economics availability and cost-input provenance;
- dsRNA threshold/design-space status;
- recommendations and verification plan;
- verification result status, if available;
- limitations and unsupported conclusions.
```

### 22.4 Prohibited Summary Claims

Codex must not say:

```text
- design space is verified, unless verification results were compared;
- cost savings are validated, unless baseline, comparison, costs, and verification basis exist;
- model is transferable to another construct, unless transfer analysis has run and assumptions are stated;
- dsRNA is controlled outside tested/model-supported factor space;
- relative yield is valid when theoretical yield inputs are missing.
```

## 23. Dashboard Workflow Story

The dashboard must support progressive study maturity:

```text
Study setup:
  overview, unavailable sections

After knowledge-space definition:
  factor ranges, response goals, constraints, economics unavailable state

After DOE generation:
  experiment matrix, design diagnostics, estimable terms

After observation import:
  observed coverage, endpoint table, timecourse plots

After theoretical yield:
  construct summary, limiting NTP, theoretical yield, relative yield

After model fitting:
  formulas, metrics, diagnostics, residual warnings

After effects analysis:
  Pareto, factor-response curves, contours

After economics:
  cost table provenance, cost breakdown, cost efficiency

After recommendations:
  next-experiment queue

After verification planning:
  verification run table and rationale

After verification comparison:
  predicted vs observed, interval status, model support/challenge labels
```

Every dashboard view must show:

```text
- source artifact or unavailable reason;
- relevant units;
- warnings near affected charts;
- whether values are measured, derived, predicted, or recommended.
```

## 24. Codex Behavior Rules

Codex must:

```text
- call MCP tools for every numerical DOE/model/cost/optimization result;
- ask for missing factor bounds, response goals, sequence/composition, or cost table only when required for the requested stage;
- continue without economics when costs are absent;
- cite artifacts or tool outputs in summaries;
- place model warnings before recommendations;
- explain unsupported paper-class analyses as unavailable, not impossible;
- refresh dashboard payload after every material analytical update.
```

Codex must not:

```text
- invent DOE matrices;
- invent coefficients, p-values, Q2, cost efficiency, or recommendations;
- infer reagent costs;
- manually edit dashboard_payload.json when an MCP tool can generate it;
- hide failed validation behind a narrative answer;
- imply wet-lab protocol authority.
```

## 25. Unavailable-State Rules

Unavailable states must be explicit and actionable.

### 25.1 Economics Unavailable

Condition:

```text
component costs are missing or invalid
```

Required behavior:

```text
- calculate_cogs_impact returns skipped or failed_validation.
- dashboard economics section shows unavailable reason.
- Codex says cost efficiency was not calculated because direct component costs were not supplied or were invalid.
```

### 25.2 Relative Yield Unavailable

Condition:

```text
sequence/composition, NTP concentration, molecular weight, or measured yield is missing
```

Required behavior:

```text
- theoretical yield may be calculated if enough inputs exist.
- relative yield remains unavailable until measured yield and theoretical yield exist.
- dashboard shows missing input list.
```

### 25.3 Design-Space Probability Unavailable

Condition:

```text
quality threshold, fitted quality model, or Monte Carlo tool output is missing
```

Required behavior:

```text
- dashboard shows threshold/model/simulation missing state.
- verification planning may still run with warning if fitted model and threshold exist.
```

### 25.4 Construct Transfer Unavailable

Condition:

```text
target construct metadata or transfer model is missing
```

Required behavior:

```text
- dashboard can compare metadata only.
- Codex must not claim transfer prediction.
```

### 25.5 Verification Comparison Unavailable

Condition:

```text
verification observations or prediction intervals are missing
```

Required behavior:

```text
- dashboard can show verification plan.
- Codex must not claim model verification.
```

## 26. Workflow Acceptance Criteria

### 26.1 Launch Acceptance Criteria

The launch IVT/QbD workflow is complete when a user can:

```text
1. Create an IVT/QbD study.
2. Validate the four-factor IVT knowledge space.
3. Generate an initial D-optimal or fallback optimal-screening design.
4. Import endpoint observations.
5. Import time-resolved observations and derive endpoint summaries.
6. Register an mRNA construct.
7. Calculate theoretical and relative yield when inputs exist.
8. Fit response-surface models for yield and dsRNA.
9. Generate effects and contour payloads.
10. Calculate cost efficiency only when component costs are supplied.
11. Generate next-experiment recommendations.
12. Generate a launch-level verification plan.
13. Refresh and open a dashboard after each stage.
14. See explicit unavailable states for missing paper-class functions.
```

### 26.2 Paper-Class Readiness Criteria

The workflow is paper-class ready when it also supports:

```text
1. Three or more iterative D-optimal augmentation rounds.
2. Full response-surface model update between rounds.
3. Monte Carlo design-space probability maps.
4. Verification result comparison against prediction intervals.
5. Construct-transfer prediction and validation.
6. Counterion DOE analysis.
7. Final summary that distinguishes explored, modeled, optimized, and experimentally verified claims.
```

## 27. Required Workflow Fixtures

The IVT/QbD workflow requires fixtures for testing and demos:

```text
ivt_qbd_factor_space.json
ivt_qbd_responses.json
ivt_qbd_initial_design_request.json
ivt_qbd_initial_design_matrix.csv
ivt_qbd_endpoint_observations.csv
ivt_qbd_time_resolved_observations.csv
ivt_qbd_construct_egfp.json
ivt_qbd_component_costs.json
ivt_qbd_model_fit.json
ivt_qbd_effects.json
ivt_qbd_dashboard_payload.json
ivt_qbd_verification_plan.json
```

Fixture rules:

```text
- Costs must be artificial user-provided example prices.
- Data must be clearly marked synthetic unless it is user-provided.
- Numeric expected outputs must include tolerances in test docs.
- Fixtures must not imply reproduction of published results without raw data.
```

## 28. Example Prompts

### 28.1 Initial Study

```text
Create an IVT QbD study for eGFP mRNA. Use Mg:NTP ratio, NTP concentration, DNA template, and T7 RNAP as factors. Optimize mRNA yield while keeping dsRNA below 3. Cost efficiency should be included only if I provide component costs.
```

### 28.2 Initial DOE

```text
Generate a 12-run D-optimal DOE using the IVT default model terms. Randomize the run order and open a dashboard preview.
```

### 28.3 Data Import

```text
Import endpoint_observations.csv and timecourse.csv. Derive endpoint mRNA concentration from the final observed time point and refresh the dashboard.
```

### 28.4 Model Fit

```text
Fit mRNA yield, dsRNA score, and relative yield. Report R2, Q2, residual warnings, and show Pareto effects.
```

### 28.5 Cost Efficiency

```text
Use this component-cost table to calculate ug/EUR for every condition. Do not use any prices except the values in the table.
```

### 28.6 Design Space

```text
Estimate the dsRNA design-space probability with 5% factor noise and a 1% failure limit. If the Monte Carlo tool is unavailable, show the unavailable state and plan verification runs using the fitted model.
```

### 28.7 Verification

```text
Plan seven verification runs around the predicted optimum and design-space boundary. Explain what each run tests.
```

### 28.8 Construct Transfer

```text
Register the mFIX construct and compare its metadata to eGFP. Do not make transfer predictions unless the transfer model can run.
```

### 28.9 Counterion DOE

```text
Set up a follow-up DOE for Mg2+ counterion with chloride and acetate across Mg:NTP ratio. Include the counterion interaction if estimable.
```

## 29. Stage-to-Tool Matrix

| Stage | Required Launch Tools | Expansion Tools |
| --- | --- | --- |
| Study setup | `create_or_update_study`, `generate_dashboard_payload` | none |
| Knowledge space | `validate_factor_space` | none |
| Initial DOE | `design_optimal_doe`, `design_doe` | none |
| Execution handoff | `generate_dashboard_payload` | export helpers if added |
| Data import | `import_endpoint_observations`, `import_time_resolved_observations` | vendor parsers if added |
| Theoretical yield | `register_construct`, `calculate_theoretical_yield` | modified nucleotide libraries |
| Model fitting | `fit_response_surface` | `fit_time_resolved_response_model` |
| Effects/contours | `analyze_effects` | richer contour engines |
| Cost efficiency | `calculate_cogs_impact` | full scenario COGS |
| Design space | `analyze_effects` foundation | `estimate_design_space_probability` |
| Recommendations | `suggest_next_experiment` | advanced expected improvement |
| Verification planning | `plan_verification_runs` | none |
| Verification comparison | import tools foundation | `compare_verification_results` |
| Construct transfer | `register_construct` foundation | `transfer_construct_model` |
| Counterion DOE | generic DOE/model tools | `analyze_counterion_doe` |

## 30. Final Workflow Rule

The IVT/QbD workflow is successful only when the user can tell, at every stage:

```text
- what was measured;
- what was derived;
- what was modeled;
- what was predicted;
- what was recommended;
- what was verified;
- what was unavailable;
- what assumptions and warnings apply.
```
