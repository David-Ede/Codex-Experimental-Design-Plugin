# Product Requirements Document: Codex Scientific Toolchain for DOE and IVT/QbD Analysis

Date: 2026-04-20
Status: Draft for implementation planning
Related documents: `Technical Architecture Brief.md`, `Canonical Build Contract.md`, `Production Execution Plan.md`

## 1. Product Summary

The product is a Codex plugin-backed scientific toolchain for planning, analyzing, optimizing, and visualizing design-of-experiments studies. It combines a thin Codex-native workflow layer, a deterministic Python MCP scientific backend, and a local React dashboard preview.

The initial domain target is process-development DOE, with a launch-quality path for IVT mRNA quality-by-design workflows modeled on the Sartorius/Boman et al. paper, "Quality by design approach to improve quality and decrease cost of in vitro transcription of mRNA using design of experiments."

The product must let a scientist or process-development engineer ask Codex to:

```text
1. Define an experimental factor space and responses.
2. Generate an appropriate DOE matrix.
3. Import endpoint and time-resolved experimental data.
4. Fit response-surface and related regression models.
5. Analyze effects, interactions, quality constraints, and uncertainty.
6. Calculate theoretical and relative yield when sequence information is supplied.
7. Calculate cost efficiency only when direct component costs are supplied.
8. Visualize the study state in a local dashboard.
9. Recommend follow-up or verification experiments with clear limitations.
```

The scientific engine, not Codex natural-language reasoning, is the source of truth for all numerical outputs. Codex orchestrates tool calls, edits code and payloads, runs tests, launches previews, and explains outputs with caveats.

## 2. Problem Statement

Scientific DOE workflows are difficult to run inside an AI coding environment because the work spans natural-language planning, structured experimental design, statistical modeling, process economics, scientific caveats, and visual review. A general agent can draft study plans, but it cannot safely invent DOE matrices, model coefficients, cost estimates, statistical diagnostics, or quality design spaces.

For IVT mRNA development specifically, the target workflow is not a simple "maximize yield" task. The reference paper shows a multifactor QbD process in which yield, relative yield, dsRNA, cost efficiency, time-resolved production trajectories, construct transfer, and verification experiments are all connected. The product must therefore support both a general DOE workflow and an IVT/QbD workflow with domain-specific calculations.

The core product problem:

```text
Give Codex a deterministic, auditable scientific toolchain so users can conduct DOE-driven process-development work with interactive visualization, without relying on hallucinated calculations or undocumented Codex UI surfaces.
```

## 3. Product Goals

### 3.1 Primary Goals

1. Provide a launch-ready Codex plugin workflow for DOE setup, DOE generation, model fitting, effect analysis, optional cost-efficiency calculation, and dashboard review.
2. Support the first practical slice of an IVT mRNA QbD workflow: four-factor knowledge space, D-optimal or candidate-set optimal design, endpoint/time-resolved data import, theoretical/relative yield, dsRNA response modeling, optional cost efficiency, and dashboard visualization.
3. Enforce deterministic computation through Python MCP tools with typed inputs, typed outputs, artifacts, warnings, and audit logs.
4. Keep economics optional at runtime. The plugin must operate without component costs. If component costs are supplied, it calculates cost efficiency by condition. If costs are missing, it states economics is unavailable and continues.
5. Make results reviewable in a local React dashboard opened through the Codex in-app browser.
6. Preserve reproducibility through study IDs, run IDs, input hashes, output hashes, schema versions, package versions, and append-only audit logs.

### 3.2 Secondary Goals

1. Provide clear, domain-aware explanations of DOE limitations, model validity, extrapolation risk, quality constraints, and cost assumptions.
2. Support iterative campaigns where new experiments are added, models are refit, and dashboards refresh.
3. Provide useful templates for IVT workflows without hardcoding the product to IVT only.
4. Provide enough structure that future hosted MCP servers, access controls, LIMS integrations, or ELN integrations can be added without changing the user-facing workflow.

## 4. Non-Goals

1. The launch product will not be a native embedded Codex UI panel. Visualization will be a normal local React web app previewed in the Codex in-app browser.
2. The launch product will not fetch reagent prices, infer reagent prices, use stale public prices, or default to assumed cost tables.
3. The launch product will not claim regulatory validation, GMP compliance, or validated process control.
4. The launch product will not reproduce proprietary MODDE project files or require MODDE compatibility.
5. The launch product will not make final experimental, clinical, safety, regulatory, or manufacturing decisions without human review.
6. The launch product will not upload sensitive biotech data to hosted services by default.
7. The launch product will not use natural-language reasoning as the source for numerical scientific results.
8. The launch product will not support arbitrary native app connectors, LIMS integrations, ELN integrations, or authentication flows.

## 5. Target Users

### 5.1 Primary Users

**Process-development scientist**

Runs DOE campaigns, defines factor ranges, interprets assay outputs, and needs to decide which experiments to run next.

Key jobs:

```text
- Turn prior knowledge into a constrained factor space.
- Generate a statistically defensible DOE matrix.
- Fit responses and inspect factors, interactions, and model warnings.
- Define a quality-constrained operating space.
- Compare candidate conditions with yield, quality, and cost tradeoffs.
```

**Bioprocess or IVT development engineer**

Optimizes biochemical reaction conditions and needs to combine productivity, reagent usage, quality attributes, and verification experiments.

Key jobs:

```text
- Model IVT output across Mg:NTP, NTP, DNA template, and RNAP settings.
- Use sequence information to calculate theoretical and relative yield.
- Use supplied reagent prices to calculate cost efficiency.
- Plan verification experiments near design-space boundaries.
- Test transferability to a different construct.
```

**Scientific data analyst**

Validates model fit, cross-validation metrics, response surfaces, prediction intervals, and dashboard payload correctness.

Key jobs:

```text
- Inspect regression diagnostics.
- Confirm input schemas and units.
- Reproduce model outputs from artifacts.
- Detect unsupported model terms or weak predictive performance.
```

### 5.2 Secondary Users

**Technical product owner**

Needs the workflow to be repeatable, explainable, and extensible across scientific teams.

**Software engineer**

Maintains the plugin, MCP server, dashboard, tests, schemas, and local setup.

## 6. User Needs and Jobs-to-Be-Done

1. When I provide factor ranges and responses, I need the toolchain to validate them before designing experiments, so invalid units, missing bounds, and impossible constraints do not contaminate the study.
2. When I ask for a DOE, I need a matrix that matches my modeling intent and constraints, so I know what terms can and cannot be estimated.
3. When I provide observed assay data, I need the toolchain to fit models using deterministic code, so coefficients and diagnostics are traceable.
4. When I provide time-resolved IVT data, I need the toolchain to model trajectories or derive endpoint responses consistently, so I can analyze more than final yield.
5. When I provide an mRNA sequence or nucleotide composition, I need theoretical and relative yield calculations, so absolute yield can be interpreted against the limiting NTP.
6. When I provide direct component costs, I need cost efficiency by condition, so I can compare yield and reagent usage without the tool inventing prices.
7. When dsRNA or another CQA has a threshold, I need a probability-based design-space view, so I can distinguish feasible regions from risky regions.
8. When a model suggests an optimum, I need verification experiments near relevant boundaries, so I can test whether the predicted operating space is real.
9. When I use the dashboard, I need warnings and diagnostics surfaced near the charts, so I do not over-trust weak models.
10. When I rerun or modify a study, I need reproducible artifacts and audit logs, so I can reconstruct how each result was produced.

## 7. Product Principles

1. Deterministic tools own calculations.
2. Codex owns orchestration and explanation.
3. The React dashboard owns visualization, filtering, and review.
4. Costs are optional and user-supplied.
5. Missing inputs produce explicit unavailable states, not fabricated defaults.
6. Every numerical claim must trace to a tool artifact.
7. Every model output must include warnings when assumptions are weak.
8. Scientific workflows should be template-driven but not hardcoded to one paper.
9. Launch scope should prove an end-to-end vertical slice before expanding breadth.

## 8. Launch Scope

### 8.1 Included at Launch

Launch includes the following product capabilities:

```text
- Codex plugin manifest and scientific-study-designer skill.
- Local Python MCP server with deterministic DOE/model/economics/dashboard tools.
- Local React dashboard app.
- Study artifact persistence under outputs/studies/<study_id>/.
- Factor and response validation.
- DOE generation for screening and candidate-set optimal design.
- D-optimal or fallback optimal-screening support for IVT/QbD studies.
- Basic response-surface model fitting for endpoint data.
- Effect analysis and plot-ready payload generation.
- Time-resolved data ingestion with explicit launch-level handling:
  - accept long-format kinetic observations,
  - derive endpoint summaries,
  - preserve raw time-series artifacts,
  - render time-course plots.
- IVT theoretical-yield and relative-yield calculation when sequence or nucleotide composition is supplied.
- Optional component-cost schema and cost-efficiency calculation when costs are supplied.
- Dashboard views for matrix, warnings, diagnostics, effects, time courses, relative yield, and cost efficiency.
- Launch-level verification-plan generation for predicted optimum and boundary/corner experiments.
- Audit logging and artifact hashing.
```

### 8.2 Included After Launch

The following are planned after the launch workflow is working:

```text
- Richer time-resolved kinetic modeling.
- Monte Carlo design-space probability maps with configurable noise models.
- Full scenario-level COGS engine.
- Construct-transfer analysis across mRNA lengths.
- Counterion DOE analysis templates.
- Advanced desirability optimization.
- Hosted dashboard mode.
- Hosted or internal HTTP MCP server.
- Access controls and team deployment.
- ELN, LIMS, or batch-record integration.
```

## 9. Product Requirements

### 9.1 Plugin and Codex Workflow Requirements

**PRD-FR-001: Plugin installation**

The product must provide a Codex plugin package with manifest metadata, a primary skill, skill metadata, install-surface assets, and MCP configuration guidance.

Acceptance criteria:

```text
- Plugin appears as "Scientific Toolchain" or equivalent display name.
- The scientific-study-designer skill is visible to Codex.
- The skill can be invoked by prompts about DOE, model fitting, IVT/QbD, optimization, or dashboard refresh.
- Local MCP fallback configuration is documented and usable before plugin-bundled MCP config is finalized.
```

**PRD-FR-002: Skill workflow discipline**

The skill must instruct Codex to call deterministic MCP tools for calculations and never invent DOE matrices, coefficients, p-values, cost estimates, reagent prices, design-space boundaries, or next-experiment recommendations.

Acceptance criteria:

```text
- Skill contains explicit "do not invent" rules.
- Skill describes canonical tool sequences for new DOE, model fitting, cost analysis, and dashboard refresh.
- Skill tells Codex to continue without economics when costs are missing.
- Skill tells Codex to surface scientific caveats in user-facing summaries.
```

**PRD-FR-003: Study lifecycle**

The product must manage studies using stable `study_id` values and persist artifacts under `outputs/studies/<study_id>/`.

Acceptance criteria:

```text
- New studies create a study directory.
- Every tool output references the same study ID.
- Repeated runs write new run IDs rather than overwriting provenance.
- Dashboard payload references the latest run and artifact hashes.
```

### 9.2 Factor, Response, and Constraint Requirements

**PRD-FR-004: Factor validation**

The product must validate factor names, factor kinds, units, bounds, categorical levels, fixed factors, transformations, and constraints before DOE generation.

Acceptance criteria:

```text
- Continuous factors require low and high bounds.
- Categorical factors require explicit levels.
- Transform definitions are validated against factor type.
- Constraints are preserved as structured expressions plus descriptions.
- Invalid definitions return errors and do not generate a DOE.
- Ambiguous but recoverable definitions return warnings and suggested corrections.
```

**PRD-FR-005: Response validation**

The product must validate response names, goals, units, thresholds, weights, and quality roles.

Acceptance criteria:

```text
- Responses can be maximize, minimize, target, or range.
- Responses can be marked as CQA, productivity, economics, diagnostic, or derived.
- Quality thresholds such as dsRNA < 3 are represented explicitly.
- Missing response goals produce validation errors before optimization.
```

**PRD-FR-006: Derived response definitions**

The product must support derived responses that are calculated from raw assay data or metadata.

Required derived responses at launch:

```text
- theoretical yield
- relative yield
- cost efficiency when component costs are supplied
- endpoint yield from a time-resolved series
```

Acceptance criteria:

```text
- Derived responses include source inputs, formula metadata, units, and warnings.
- Derived responses are persisted as artifacts.
- Dashboard identifies derived responses distinctly from measured responses.
```

### 9.3 DOE Generation Requirements

**PRD-FR-007: General DOE generation**

The product must generate DOE matrices for common screening and response-surface use cases.

Launch-supported design modes:

```text
- full factorial for small feasible spaces
- fractional factorial for two-level screening
- Latin hypercube for mixed continuous spaces
- candidate-set optimal design with D-optimal objective where available
- fallback optimal-screening design if D-optimal constraints cannot be satisfied
```

Acceptance criteria:

```text
- Tool output includes design matrix, run count, design ID, randomization state, seed, and diagnostics.
- Diagnostics list estimable terms and alias/confounding warnings.
- The tool refuses designs that exceed practical run-count limits unless the user explicitly confirms.
- The tool returns a reason when it falls back from D-optimal to another design method.
```

**PRD-FR-008: D-optimal design support**

The product must support D-optimal candidate-set design for paper-class IVT/QbD workflows.

Acceptance criteria:

```text
- User can provide candidate model terms.
- User can provide candidate factor grid or factor bounds.
- Tool can select a fixed number of experiments from candidate rows.
- Tool reports selected model terms, design criterion value, rank, condition number, and unsupported terms.
- Launch supports the metadata foundation for augmentation: iteration number, locked-row references, and clear warnings when full augmentation is unavailable.
- Paper-class support includes selecting new rows while preserving existing experimental rows.
- Tool warns when the requested model is not estimable from the selected run count.
```

**PRD-FR-009: Iterative DOE campaign support**

The product must represent multiple DOE iterations within one study. Launch must preserve the data model and dashboard states for iterations; full iterative D-optimal augmentation is paper-class scope.

Acceptance criteria:

```text
- Iteration number is stored with each design and observed dataset.
- Existing experimental rows can be represented as locked rows.
- Paper-class augmentation can select new rows against locked rows.
- New recommended rows can target weak regions, missing interactions, quality boundaries, or verification needs when the required recommendation method is available.
- Dashboard can distinguish original, augmented, repeated, and verification runs.
```

### 9.4 Data Import and Assay Requirements

**PRD-FR-010: Endpoint data import**

The product must accept endpoint experimental observations as CSV, JSON, or in-memory table data.

Required columns:

```text
- run identifier
- factor settings
- measured response values
```

Acceptance criteria:

```text
- Import validates required factor and response columns.
- Import checks units when units are supplied.
- Import reports missing values by row and response.
- Imported data is persisted under the study directory.
```

**PRD-FR-011: Time-resolved data import**

The product must accept long-format time-resolved observations.

Required fields:

```text
- study_id
- run_id
- time
- time_unit
- analyte or response name
- value
- value_unit
- sample metadata when supplied
```

Acceptance criteria:

```text
- Multiple analytes per time point are supported.
- Time-series data can be plotted by run and response.
- Endpoint summaries can be derived by final time point, maximum observed value, plateau value, or user-selected time.
- Raw time-series data remains available after endpoint summaries are derived.
```

**PRD-FR-012: IVT assay semantics**

The product must include an IVT/QbD study template that names common IVT factors and responses without requiring those names for non-IVT studies.

Launch IVT factors:

```text
- Mg:NTP ratio
- NTP concentration
- DNA template concentration
- T7 RNAP concentration
```

Launch IVT responses:

```text
- mRNA yield
- dsRNA score
- theoretical yield
- relative yield
- cost efficiency, when component costs are supplied
```

Acceptance criteria:

```text
- Template can instantiate the four-factor knowledge space from the paper.
- Template supports dsRNA threshold rules.
- Template supports HPLC-like time-course measurements as generic analyte time series.
- Template can be extended with counterion as a categorical factor.
```

### 9.5 Modeling and Statistical Requirements

**PRD-FR-013: Response-surface model fitting**

The product must fit response-surface models for measured and derived responses using deterministic statistical code.

Acceptance criteria:

```text
- User can specify main effects, interaction terms, square terms, and transforms.
- Tool outputs coefficients, standard errors where applicable, model formula, metrics, diagnostics, and warnings.
- Tool reports singular or ill-conditioned model matrices.
- Tool supports robust standard errors when requested and available.
- Tool never fabricates p-values or confidence intervals when the model does not support them.
```

**PRD-FR-014: Cross-validation and predictive metrics**

The product must report predictive metrics suitable for model screening.

Launch metrics:

```text
- R2
- adjusted R2 when applicable
- leave-one-out or k-fold cross-validated predictive score
- RMSE
- residual summary
```

Acceptance criteria:

```text
- Predictive metrics are persisted with model artifacts.
- Dashboard diagnostics show when predictive performance is weak.
- Tool warns when data volume is too small for the requested validation method.
```

**PRD-FR-015: Heredity and parsimony checks**

The product must check model terms against heredity and parsimony rules.

Acceptance criteria:

```text
- Interaction terms trigger warnings if corresponding main effects are absent.
- Square terms trigger warnings if corresponding main effects are absent.
- Over-parameterized models warn when rows are insufficient for requested terms.
- Tool output identifies dropped, aliased, or unsupported terms.
```

**PRD-FR-016: Effect analysis**

The product must calculate and visualize model effects.

Acceptance criteria:

```text
- Tool outputs main effects, interactions, standardized effects where valid, and plot-ready payloads.
- Pareto payloads include response name, effect term, effect size, sign, and warnings.
- Factor-response curves include hold-value strategy and uncertainty metadata when available.
```

### 9.6 IVT-Specific Requirements

**PRD-FR-017: Sequence metadata**

The product must accept mRNA construct metadata for IVT workflows.

Accepted inputs:

```text
- full sequence
- nucleotide composition counts
- transcript length
- poly(A) tail length when supplied
- molecular weight override when supplied
```

Acceptance criteria:

```text
- Full sequence is parsed into nucleotide counts.
- Composition counts can be used when full sequence is unavailable.
- Tool validates that counts and length are consistent.
- Tool records whether molecular weight was calculated or user-supplied.
```

**PRD-FR-018: Theoretical yield**

The product must calculate theoretical maximum yield from sequence composition and limiting NTP when enough input is supplied.

Acceptance criteria:

```text
- Tool identifies the limiting NTP for a given construct and NTP condition.
- Tool calculates theoretical yield in explicit units.
- Tool calculates relative yield as actual yield divided by theoretical maximum times 100.
- Tool refuses relative-yield calculation when actual yield or theoretical yield is unavailable.
- Dashboard shows theoretical and relative yield with formula provenance.
```

**PRD-FR-019: dsRNA quality threshold**

The product must support semi-quantitative dsRNA responses and threshold-based quality constraints.

Acceptance criteria:

```text
- dsRNA can be represented as a numeric score with a bounded assay scale.
- User can define acceptance criteria such as dsRNA < 3.
- Model and dashboard distinguish semi-quantitative assay scores from absolute concentrations.
- Optimization can treat dsRNA threshold as a constraint.
```

**PRD-FR-020: Construct-transfer foundation**

The launch product must store enough construct metadata to enable later construct-transfer modeling.

Acceptance criteria:

```text
- Study artifacts preserve construct ID, length, composition, and molarity adjustment metadata.
- Dashboard can compare constructs at the metadata level.
- Full transfer-model predictions are explicitly marked post-launch unless implemented.
```

### 9.7 Economics and COGS Requirements

**PRD-FR-021: Optional economics**

Economics must be optional. DOE generation, model fitting, dashboard rendering, and non-economic optimization must work without cost inputs.

Acceptance criteria:

```text
- Missing cost inputs do not fail the study.
- Dashboard displays "economics unavailable" state rather than blank charts.
- Codex explains that cost efficiency was not calculated because component costs were not supplied.
```

**PRD-FR-022: Direct component-cost input**

The product must calculate cost efficiency only from user-supplied direct component costs.

Required cost fields:

```text
- component_name
- unit_cost
- currency
- cost_basis_unit
- factor_mapping or fixed amount
```

Acceptance criteria:

```text
- Tool rejects cost rows without unit cost, currency, or cost basis.
- Tool rejects mixed currencies unless the user supplies explicit conversion rates.
- Tool records cost input hash.
- Tool output cites source cost table and units.
- Tool never fetches or infers reagent prices.
```

**PRD-FR-023: Cost by condition**

The product must calculate reagent/component cost per experimental condition when enough cost and amount information is available.

Acceptance criteria:

```text
- Cost calculation maps factor settings to component amounts.
- Cost breakdown is reported by component.
- Cost efficiency can be represented as mass per currency or currency per mass.
- Tool returns warnings when a factor has no cost mapping.
- Tool can calculate sensitivity when price_low and price_high are supplied.
```

**PRD-FR-024: Economic claims**

The product must prevent unsupported economic claims.

Acceptance criteria:

```text
- Cost results are labeled as model-based estimates.
- Dashboard shows cost basis and currency.
- Summaries do not state "COGS improved" unless a baseline and comparison condition are both defined.
- Summaries do not state validated financial savings without verification data.
```

### 9.8 Optimization and Design Space Requirements

**PRD-FR-025: Desirability optimization**

The product must support multi-response desirability scoring.

Acceptance criteria:

```text
- User can define response goals and weights.
- Quality constraints can be hard constraints.
- Tool reports objective contributions for each recommendation.
- Tool distinguishes exploitation, exploration, and constraint-probing recommendations.
```

**PRD-FR-026: Design-space probability foundation**

The product must support design-space estimation for quality constraints as a planned capability, with launch artifacts structured to support it.

Launch acceptance criteria:

```text
- Quality thresholds are represented in schemas.
- Response surfaces can generate prediction grids.
- Dashboard can render a clear unavailable state for probability maps when Monte Carlo is not yet run.
```

Post-launch acceptance criteria:

```text
- Tool perturbs factor settings according to configured noise.
- Tool estimates probability of quality failure over a candidate grid.
- Tool marks regions that satisfy probability-of-failure limits.
- Dashboard renders probability maps and exposes simulation settings.
```

**PRD-FR-027: Verification planning**

The product must generate verification experiment plans for predicted optima and design-space boundaries.

Launch acceptance criteria:

```text
- Tool can propose predicted optimum confirmation.
- Tool can propose corner or edge verification points near quality boundaries.
- Tool labels verification runs distinctly from model-building runs.
- Tool explains what each verification run is intended to test.
```

### 9.9 Dashboard Requirements

**PRD-FR-028: Dashboard preview**

The product must provide a local React dashboard that renders a study from `dashboard_payload.json`.

Acceptance criteria:

```text
- Dashboard can run locally through Vite or equivalent dev server.
- Dashboard route supports `/studies/:studyId`.
- Dashboard validates payload schema at runtime.
- Dashboard shows study ID, run ID, generated timestamp, and payload version.
```

**PRD-FR-029: Launch dashboard views**

The launch dashboard must include the following views:

```text
- Study overview
- Experiment matrix
- Warnings and assumptions
- Time-course plots when time-resolved data exists
- Factor-response plots when model data exists
- Pareto/effects chart when effect analysis exists
- Relative-yield view when theoretical yield exists
- Cost-efficiency view when component costs exist
- Diagnostics view
- Payload/audit footer
```

Acceptance criteria:

```text
- Each unavailable view explains which input or tool output is missing.
- Charts do not silently omit warnings.
- User can identify measured, derived, predicted, and recommended values.
- Cost-efficiency charts are absent or marked unavailable when costs are missing.
```

**PRD-FR-030: Dashboard scientific boundaries**

The dashboard must not perform final scientific calculations beyond display transforms.

Acceptance criteria:

```text
- Model fitting happens in MCP tools, not React.
- Cost calculations happen in MCP tools, not React.
- Theoretical yield calculations happen in MCP tools, not React.
- Dashboard performs only sorting, filtering, formatting, and chart transformations.
```

### 9.10 Artifact, Audit, and Reproducibility Requirements

**PRD-FR-031: Artifact persistence**

The product must persist artifacts for every material analytical step.

Required artifacts:

```text
- factor_space.json
- design_matrix.csv
- design_metadata.json
- observed_data artifact when supplied
- time_resolved_observations artifact when supplied
- model_fit.json
- effects.json
- theoretical_yield.json when applicable
- economics.json when applicable
- dashboard_payload.json
- audit_log.jsonl
```

Acceptance criteria:

```text
- Artifacts include schema version and generated timestamp.
- Artifacts include input references and hashes.
- Dashboard payload references artifact hashes.
- Re-running a step writes a new audit entry.
```

**PRD-FR-032: Audit log**

The product must maintain an append-only audit log per study.

Acceptance criteria:

```text
- Each tool call records tool name, tool version, run ID, input hash, output hash, warnings, and errors.
- Random seeds are recorded.
- Package versions are recorded for scientific engines.
- Failed tool calls are logged with structured errors.
```

## 10. Launch User Workflows

### 10.1 New IVT DOE Design

User prompt:

```text
Use Scientific Toolchain to design an IVT DOE with Mg:NTP 0.8-1.6,
NTP 6-12 mM, DNA template 10-100 ng/uL, and T7 RNAP 2-15 U/uL.
Responses are mRNA yield, dsRNA score, relative yield, and cost efficiency
if I provide costs. Use a D-optimal design for the initial iteration.
```

Expected behavior:

```text
1. Codex invokes the scientific-study-designer skill.
2. Codex normalizes factors and responses.
3. MCP validates the factor space.
4. MCP generates D-optimal or fallback optimal-screening design.
5. MCP writes design matrix and metadata.
6. MCP generates dashboard payload.
7. Codex starts or identifies dashboard preview URL.
8. Codex explains run count, estimable terms, unsupported terms, randomization, and missing economics.
```

### 10.2 Fit Observed IVT Data

User prompt:

```text
Fit the observed IVT data for the last DOE. Model mRNA yield and dsRNA,
calculate relative yield from this sequence, and refresh the dashboard.
```

Expected behavior:

```text
1. Codex locates observed data and sequence metadata.
2. MCP validates data columns and units.
3. MCP calculates theoretical and relative yield.
4. MCP fits response models.
5. MCP analyzes effects.
6. MCP generates updated dashboard payload.
7. Codex summarizes model terms, metrics, warnings, and unsupported conclusions.
```

### 10.3 Optional Cost-Efficiency Analysis

User prompt:

```text
Use these component costs to calculate cost efficiency:
T7 RNAP is 4.20 EUR per U, DNA template is 0.18 EUR per ng,
NTP mix is 0.06 EUR per umol, and fixed buffer/reagent cost is 12 EUR per batch.
Compare each DOE condition using ug/EUR.
```

Expected behavior:

```text
1. MCP validates cost table, units, currency, and mappings.
2. MCP calculates component cost per condition.
3. MCP calculates cost efficiency using modeled or measured yield.
4. MCP writes economics artifact.
5. Dashboard shows cost breakdown and cost-efficiency chart.
6. Codex states that economics reflects only the user-provided costs.
```

### 10.4 Verification Plan

User prompt:

```text
Plan verification runs around the predicted optimum and the dsRNA design-space boundary.
```

Expected behavior:

```text
1. Codex checks that fitted model and quality threshold exist.
2. MCP identifies optimum and candidate boundary/corner points.
3. MCP proposes verification runs with rationale.
4. MCP updates dashboard payload.
5. Codex explains what each run tests and which uncertainty remains.
```

## 11. Success Metrics

### 11.1 Product Success Metrics

1. A user can complete a new DOE design and dashboard preview in one Codex thread.
2. A user can import observed data, fit models, and refresh the dashboard without manual artifact editing.
3. A user can run an IVT/QbD launch workflow with the four paper-inspired factors and responses.
4. A user can calculate cost efficiency only after supplying direct component costs.
5. A user can identify missing inputs, model warnings, and unavailable analyses from the dashboard and Codex summary.

### 11.2 Quality Metrics

1. 100% of numerical outputs in Codex summaries trace to MCP artifacts.
2. 100% of dashboard payloads pass schema validation.
3. 100% of scientific tool calls write audit entries.
4. Golden fixture tests pass for DOE generation, model fitting, theoretical yield, optional economics, and payload generation.
5. Unsupported analyses produce explicit warnings instead of silent omissions.

### 11.3 Scientific Reliability Metrics

1. D-optimal design tests recover expected run counts and estimability for known candidate models.
2. Theoretical yield tests match hand-calculated fixtures within stated tolerance.
3. Relative yield tests refuse impossible outputs when theoretical yield is missing or zero.
4. Cost-efficiency tests refuse missing units and mixed currencies without conversion.
5. Model-fitting tests detect singular matrices and over-parameterized formulas.

## 12. Release Criteria

### 12.1 Phase 0 Release Criteria

Phase 0 is complete when:

```text
- Plugin and skill are installable locally.
- MCP server exposes validate_factor_space, design_doe, and generate_dashboard_payload.
- Optional component-cost schema exists in shared schemas.
- Dashboard renders experiment matrix, warnings, economics availability state, and payload footer.
- One end-to-end DOE prompt works from factor input to local dashboard preview.
```

### 12.2 Launch Release Criteria

Launch is complete when:

```text
- D-optimal or candidate-set optimal DOE support works for the IVT four-factor example.
- Endpoint data import and model fitting work.
- Time-resolved data import and plotting work.
- IVT theoretical and relative yield calculation works from sequence or composition.
- Optional component-cost calculation works from direct user-provided costs.
- Dashboard shows matrix, effects, diagnostics, time courses, relative yield, and cost efficiency when available.
- Verification-plan generation works at launch level.
- All launch workflow tests pass.
- Every unavailable paper-class capability is explicitly labeled in output rather than implied.
```

### 12.3 Paper-Class Workflow Readiness Criteria

The product is ready for full paper-class IVT/QbD use when:

```text
- Iterative D-optimal augmentation works across at least three campaign iterations.
- Model metrics include predictive scores and prediction intervals.
- Monte Carlo design-space probability maps are implemented and visualized.
- Desirability optimization can combine yield, relative yield, dsRNA threshold, and cost efficiency.
- Construct-transfer modeling can compare two constructs with sequence-length and molarity adjustments.
- Counterion DOE supports Mg:NTP ratio plus categorical counterion.
- Verification results can be compared against prediction intervals.
```

## 13. Risks and Mitigations

**Risk: Codex invents scientific outputs**

Mitigation:

```text
- Skill forbids invented numerical outputs.
- Summaries must cite artifact names or tool outputs.
- Tests include prompts that tempt unsupported claims.
```

**Risk: COGS is overpromised**

Mitigation:

```text
- Economics is optional.
- Prices must be user-provided.
- Missing cost inputs produce unavailable states.
- Outputs label cost efficiency as model-based and input-dependent.
```

**Risk: D-optimal design implementation is incomplete**

Mitigation:

```text
- Provide fallback optimal-screening design.
- Report fallback reason.
- Add benchmark tests for candidate-set selection and estimability.
```

**Risk: IVT-specific features make the tool too narrow**

Mitigation:

```text
- Keep IVT as a template, not the only workflow.
- Keep factor/response schemas generic.
- Put sequence/yield logic in IVT-specific modules.
```

**Risk: Weak models look authoritative**

Mitigation:

```text
- Dashboard surfaces predictive metrics and warnings.
- Codex summaries include limitations.
- Optimization refuses unsupported extrapolation when model validity is poor.
```

**Risk: Sensitive data exposure**

Mitigation:

```text
- Local-only default MCP server.
- Local dashboard bound to localhost.
- No external price lookup or data upload by default.
- Audit logs redact secrets and avoid raw credentials.
```

## 14. Dependencies

### 14.1 Internal Dependencies

```text
- Technical Architecture Brief
- Scientific Methods Spec
- Data & Schema Contract
- MCP Tool API Spec
- IVT/QbD Workflow Spec
- Dashboard UX Spec
- Validation & Test Plan
```

### 14.2 Technical Dependencies

```text
- Codex plugin system
- Codex skills
- Codex MCP support
- Python MCP SDK / FastMCP or equivalent
- Python scientific stack for DOE, regression, validation, and optimization
- React dashboard stack
- Local dev server preview in Codex in-app browser
```

### 14.3 Data Dependencies

```text
- User-provided factor definitions
- User-provided response definitions
- User-provided observed endpoint data
- User-provided time-resolved assay data when kinetic analysis is requested
- User-provided sequence or nucleotide composition when theoretical yield is requested
- User-provided component costs when cost efficiency is requested
```

## 15. Product Decisions Captured

1. COGS and cost efficiency are included in product scaffolding at launch.
2. COGS and cost efficiency are optional at runtime.
3. The product never invents, fetches, or defaults reagent prices.
4. The IVT/QbD paper is a reference workflow target, not an exact MODDE clone.
5. D-optimal or candidate-set optimal DOE is required for the launch IVT/QbD workflow.
6. Time-resolved data must be accepted at launch, even if richer kinetic modeling matures after launch.
7. Theoretical and relative yield are required when sequence or composition is supplied.
8. The React dashboard renders scientific state but does not perform core scientific calculations.
9. The MCP server is the scientific source of truth.
10. The launch product must make missing or unsupported analyses explicit.

## 16. Glossary

**COGS**
Cost of goods sold. In this product, launch economics are limited to user-supplied component costs and model-derived cost efficiency. Full manufacturing COGS can be expanded later.

**Cost efficiency**
Product mass per unit currency or currency per product mass, calculated from user-supplied cost inputs and measured or predicted yield.

**CQA**
Critical quality attribute. For the IVT reference workflow, dsRNA score is treated as a CQA.

**D-optimal design**
An optimal experimental design selected from candidate points to maximize information for a specified model.

**Design space**
A region of factor settings predicted to satisfy defined response requirements, such as dsRNA below a threshold.

**IVT**
In vitro transcription.

**MLR**
Multiple linear regression.

**QbD**
Quality by design.

**Relative yield**
Actual yield divided by theoretical maximum yield, expressed as a percentage.

**Theoretical yield**
Maximum possible product yield based on sequence composition and limiting substrate.
