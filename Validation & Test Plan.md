# Validation & Test Plan: Codex Scientific Toolchain

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Scientific Methods Spec.md
- Data & Schema Contract.md
- MCP Tool API Spec.md
- IVT QbD Workflow Spec.md
- Dashboard UX Spec.md
- Canonical Build Contract.md
- Production Execution Plan.md
```

## 1. Purpose

This document defines the validation and test strategy for the Codex Scientific Toolchain. It covers scientific correctness, API behavior, data contracts, dashboard rendering, reproducibility, security boundaries, and release gates.

The product is a local Codex plugin-backed workflow for DOE planning, response-surface modeling, IVT/QbD analysis, optional direct-input cost analysis, and dashboard review. The validation plan ensures that:

```text
- Numerical results come from deterministic scientific code, not Codex language reasoning.
- Study artifacts are traceable, reproducible, and schema-valid.
- The product works without economics inputs.
- Cost efficiency is calculated only when the user supplies direct component costs.
- The launch product supports the practical IVT/QbD workflow described in the planning docs.
- The product can grow into paper-class Sartorius/Boman-style analysis without redesigning the core architecture.
```

## 2. Validation Philosophy

The product must be validated as a scientific software toolchain, not as a conversational demo. Every release must prove four things:

```text
1. Correctness: calculations match known fixtures, independent reference calculations, or mathematically defined expectations.
2. Reproducibility: identical inputs, seeds, method versions, and package versions produce identical artifacts.
3. Traceability: every displayed result maps to source data, method versions, warnings, and artifact hashes.
4. Fail-safe behavior: missing, invalid, or insufficient inputs produce explicit unavailable states instead of fabricated outputs.
```

The validation approach is layered:

```text
- Unit tests validate individual scientific functions and validators.
- Schema tests validate all persisted and returned data.
- MCP tool tests validate API contracts, side effects, errors, and audit logs.
- Integration tests validate complete launch workflows.
- Dashboard tests validate user-visible interpretation surfaces.
- Regression tests lock known outputs for canonical IVT/QbD scenarios.
- Performance tests protect interactive use.
- Security tests protect local data boundaries and unsafe file behavior.
```

## 3. Scope

### 3.1 In Scope for Launch Validation

```text
- Study creation and metadata updates.
- Factor-space validation.
- Full factorial, fractional factorial, Latin hypercube, and D-optimal DOE generation where implemented at launch.
- Candidate-set D-optimal design, with augmentation metadata and locked-row validation at launch.
- Endpoint observation import.
- Time-resolved observation import.
- Construct registration.
- Theoretical maximum yield calculation from sequence composition.
- Relative yield calculation from actual yield and theoretical maximum.
- Ordinary least squares response-surface fitting.
- Model diagnostics: R2, adjusted R2, Q2 or cross-validated R2, RMSE, residuals, leverage, warnings, and rank status.
- Effect analysis for main effects, interactions, square terms, and response contours.
- Optional direct-input cost and cost-efficiency calculation.
- Next-experiment recommendation under declared constraints.
- Verification-run planning.
- Dashboard payload generation.
- Local dashboard preview behavior.
- Study audit logs and artifact hashes.
```

### 3.2 In Scope for Paper-Class Expansion Validation

```text
- Design-space probability estimation with Monte Carlo sampling.
- Verification result comparison against prediction intervals or acceptance limits.
- Time-resolved response modeling.
- Construct-transfer analysis using length-scaled time or declared transfer transforms.
- Counterion DOE analysis.
- Multi-response desirability across yield, relative yield, quality response, and optional cost efficiency.
```

### 3.3 Out of Scope

```text
- GMP validation.
- Regulatory validation.
- Clinical decision validation.
- Automated experiment execution on laboratory hardware.
- LIMS or ELN integration.
- Public reagent price lookup.
- Inferred reagent costs.
- Hosted multi-user access control.
```

## 4. Release Gates

### 4.1 Gate 0: Repository and Contract Gate

The implementation cannot be considered ready for feature work until:

```text
- Schema files exist for launch artifacts defined in Data & Schema Contract.md.
- Test fixtures exist for valid and invalid launch inputs.
- CI or local quality commands exist for backend, dashboard, and schema validation.
- The MCP tool registry matches MCP Tool API Spec.md.
- The dashboard accepts only generated dashboard payloads for scientific state.
- A fixed-seed test mode exists for stochastic or randomized methods.
- A plugin/MCP smoke test proves Codex can discover the local plugin, load the skill, start MCP, and call create_or_update_study.
- Backend and dashboard dependency lockfiles exist and install from a clean checkout.
- Package-version capture exists for Python, MCP server framework, pydantic, numpy, scipy, pandas, statsmodels, scikit-learn, jsonschema, pytest, Node, pnpm, React, Vite, and Playwright.
```

Minimum Gate 0 schema coverage:

```text
- artifact_metadata.schema.json
- warning.schema.json
- error.schema.json
- tool_envelope.schema.json
- audit_log_entry.schema.json
- study.schema.json
- factor_space.schema.json
- responses.schema.json
- dashboard_payload.schema.json
```

Minimum Gate 0 fixture coverage:

```text
- valid minimal study, factor space, response set, and dashboard payload
- invalid study ID
- invalid factor bounds
- duplicate normalized factor/response names
- invalid or missing units
- missing required artifact metadata
- empty dashboard payload state
- phase-0 design-only dashboard payload
- dashboard payload validation error state
```

### 4.2 Gate 1: Launch Readiness Gate

The product is launch-ready only when:

```text
- All launch MCP tools pass contract tests.
- Scientific fixtures pass within defined numerical tolerances.
- Golden IVT/QbD launch workflow passes end to end.
- Economics-unavailable behavior passes end to end.
- Direct-input economics behavior passes end to end.
- Dashboard rendering passes desktop, tablet, and mobile smoke tests.
- Audit logs are written for every successful, skipped, warning, and failed tool call.
- No launch workflow depends on external network access.
- No numerical result in the dashboard is calculated client-side.
```

### 4.3 Gate 2: Paper-Class Workflow Gate

The product can claim paper-class Sartorius/Boman-style workflow support only when:

```text
- Iterative D-optimal DOE design and augmentation pass regression tests.
- Time-resolved IVT data import and trajectory visualization pass integration tests.
- Theoretical and relative yield calculations pass sequence-composition fixtures.
- dsRNA or quality-response design-space constraints can be modeled and visualized.
- Optional direct-input cost efficiency can be combined with quality and yield responses.
- Verification-run planning and verification-result comparison pass integration tests.
- Construct-transfer workflow passes synthetic eGFP-to-longer-construct fixtures.
- Counterion DOE workflow passes fixtures with categorical counterion factors.
- The dashboard clearly distinguishes observed, predicted, recommended, verification, and unavailable results.
```

## 5. Test Environments

### 5.1 Local Development

Local development must support:

```text
- Python scientific backend tests.
- MCP server contract tests.
- Schema validation.
- Dashboard unit and component tests.
- Dashboard build verification.
- Browser-based dashboard smoke tests.
- End-to-end workflow tests using local file artifacts.
```

Required command surface:

```text
python -m pytest mcp-server/tests
python -m pytest mcp-server/tests --run-regression
python scripts/validate_schemas.py
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard build
pnpm --dir apps/dashboard test:e2e
```

### 5.2 Continuous Integration

CI must run the same validation suite as local development with fixed seeds and clean workspaces. CI must publish:

```text
- test result summary
- schema validation summary
- golden fixture diff summary
- dashboard build output
- end-to-end artifact bundle for failed workflow tests
```

### 5.3 Browser Verification

Browser verification must cover:

```text
- Chromium desktop viewport: 1440 x 900
- Tablet viewport: 1024 x 768
- Mobile viewport: 390 x 844
```

The dashboard must load with no blocking console errors, no blank primary panels, and no overlapping critical UI.

## 6. Test Data Strategy

### 6.1 Data Principles

Test data must be synthetic or explicitly cleared for local development. Fixtures must be small enough for CI, but rich enough to exercise real scientific behavior.

Test data rules:

```text
- Do not include confidential experimental data.
- Do not include proprietary reagent prices.
- Use explicit fixture costs only for cost tests.
- Keep fixture units realistic.
- Include both clean and intentionally flawed datasets.
- Include source CSV files and expected normalized JSON artifacts.
- Include expected warnings for borderline scientific cases.
```

### 6.2 Fixture Families

Required fixture families:

```text
fixtures/studies/minimal_doe/
fixtures/studies/invalid_bad_study_id/
fixtures/studies/invalid_bad_factor_bounds/
fixtures/studies/invalid_duplicate_normalized_names/
fixtures/studies/invalid_missing_required_metadata/
fixtures/studies/invalid_units/
fixtures/dashboard/empty_payload_state.json
fixtures/dashboard/phase0_design_only_payload.json
fixtures/dashboard/payload_validation_error.json
fixtures/studies/ivt_launch_no_costs/
fixtures/studies/ivt_launch_with_costs/
fixtures/studies/ivt_timecourse/
fixtures/studies/ivt_rank_deficient_model/
fixtures/studies/ivt_missing_response_values/
fixtures/studies/ivt_invalid_units/
fixtures/studies/ivt_construct_yield/
fixtures/studies/ivt_design_space/
fixtures/studies/ivt_verification/
fixtures/studies/ivt_construct_transfer/
fixtures/studies/ivt_counterion/
```

### 6.3 Golden Outputs

Golden outputs must be stored for:

```text
- DOE matrices.
- Normalized observation tables.
- Theoretical-yield calculations.
- Relative-yield calculations.
- Model coefficients.
- Diagnostics.
- Effect summaries.
- Cost-efficiency tables.
- Recommendation outputs.
- Dashboard payloads.
```

Numerical golden outputs must include:

```text
- expected value
- absolute tolerance
- relative tolerance
- seed
- method version
- package version
- source fixture hash
```

### 6.4 Synthetic IVT Reference Scenario

The canonical synthetic IVT scenario must use:

```text
- factors: Mg:NTP ratio, NTP concentration, DNA template, T7 RNAP
- responses: mRNA yield, dsRNA score, relative yield, cost efficiency when costs are supplied
- construct: 995 nt eGFP-like sequence with declared poly(A) tail length
- timepoints: 0, 15, 30, 45, 60, 90, 120, 150, 180, 210 minutes
- optional categorical expansion: magnesium counterion
```

This fixture does not need to reproduce the paper's proprietary measurements. It must reproduce the shape of the workflow and assert correct software behavior.

## 7. Traceability Matrix

| Product Capability | Source Document | Required Validation |
|---|---|---|
| DOE study creation | Product Requirements Document.md, MCP Tool API Spec.md | Study schema test, MCP contract test, audit-log test |
| Factor-space validation | Scientific Methods Spec.md, Data & Schema Contract.md | Unit validation tests, invalid-unit tests, impossible-range tests |
| DOE matrix generation | Scientific Methods Spec.md | Golden matrix tests, reproducibility tests, constraint tests |
| D-optimal design and augmentation foundation | Scientific Methods Spec.md, IVT QbD Workflow Spec.md | Candidate-set tests, determinant tests, fixed-seed regression tests, locked-row schema tests |
| Endpoint observation import | Data & Schema Contract.md | CSV parser tests, unit normalization tests, missing-value tests |
| Time-resolved observation import | IVT QbD Workflow Spec.md | Timepoint validation tests, replicate tests, trajectory payload tests |
| Construct registration | Scientific Methods Spec.md | Sequence validation tests, base-count tests, poly(A) metadata tests |
| Theoretical yield | Scientific Methods Spec.md | Hand-calculated sequence fixtures, limiting-nucleotide tests |
| Relative yield | Scientific Methods Spec.md | Actual/theoretical yield tests, unavailable-state tests |
| Response-surface modeling | Scientific Methods Spec.md | Coefficient tests, diagnostic tests, rank-deficiency tests |
| Effect analysis | Scientific Methods Spec.md | Main-effect tests, interaction tests, contour grid tests |
| Optional COGS analysis | Product Requirements Document.md | No-cost skipped tests, direct-cost positive tests, invalid-cost failure tests |
| Recommendations | MCP Tool API Spec.md | Constraint-respecting tests, reason-code tests, reproducibility tests |
| Verification planning | IVT QbD Workflow Spec.md | Corner/center selection tests, duplicate-run avoidance tests |
| Dashboard rendering | Dashboard UX Spec.md | Component tests, Playwright smoke tests, accessibility tests |
| Auditability | Data & Schema Contract.md | Hash tests, append-only log tests, artifact-link tests |

Detailed implementation tickets must use this traceability shape:

```text
requirement_id:
  source_document:
  build_ticket:
  owner_workstream:
  mcp_tool_or_dashboard_component:
  schemas:
  artifacts:
  fixtures:
  automated_tests:
  dashboard_states:
  release_gate:
  status:
```

Traceability rules:

```text
- Every PRD-FR requirement must map to at least one fixture or an explicit unavailable-state fixture.
- Every MCP tool must map to request schema, response schema, artifact schema, success fixture, and failure fixture.
- Every dashboard tab must map to at least one valid payload fixture and one unavailable/error-state fixture.
- Release gates cannot pass with unmapped launch requirements.
```

## 8. Scientific Engine Unit Tests

### 8.1 Quantity and Unit Validation

Tests must verify:

```text
- Required value, unit, and semantic role are present.
- Numeric values reject NaN, infinity, and non-numeric strings.
- Concentration, mass, volume, enzyme activity, time, and cost units parse correctly.
- Unsupported units fail in strict mode.
- Compatible units normalize consistently.
- Factor ranges reject min greater than max.
- Zero-width ranges are allowed only when explicitly marked as fixed factors.
- Missing units produce errors for numeric scientific values.
```

### 8.2 Factor Encoding

Tests must verify:

```text
- Continuous factors encode to coded units correctly.
- Categorical factors encode to stable contrast columns.
- Log-transformed factors reject non-positive values.
- Square terms are generated from encoded continuous factors.
- Interaction terms use encoded factors.
- Term labels are stable across runs.
```

### 8.3 DOE Generation

Tests must verify:

```text
- Full factorial design produces the expected run count and factor combinations.
- Fractional factorial design preserves requested resolution where supported.
- Latin hypercube design respects ranges and fixed seed reproducibility.
- D-optimal design produces the requested number of unique runs when the candidate set permits it.
- D-optimal design respects hard constraints.
- D-optimal design returns explicit warnings when candidate points are insufficient.
- Launch validates augmentation metadata and locked-row references; paper-class additionally proves augmentation preserves existing runs and selects only new candidate points unless duplicates are explicitly allowed.
- Replicate and center-point policies are applied exactly.
- Output run labels are stable and unique.
```

D-optimal acceptance checks:

```text
- identical inputs and seed produce identical selected runs
- determinant or information-quality metric is positive for estimable models
- rank-deficient model terms produce warnings before experiment selection
- selected runs remain inside declared factor bounds
```

### 8.4 Observation Import

Endpoint observation tests must verify:

```text
- Required run identifiers match known DOE rows.
- Unknown run identifiers fail in strict mode.
- Missing response values are preserved as missing values with warnings.
- Replicate rows are retained and summarized only in derived artifacts.
- Response units are validated and normalized.
- Source row numbers are retained for diagnostics.
```

Time-resolved observation tests must verify:

```text
- Timepoints are numeric and unit-normalized.
- Negative timepoints fail.
- Duplicate run/time/response rows are handled by declared replicate policy.
- Non-monotonic source order is accepted and sorted in derived artifacts.
- Endpoint and time-resolved data can coexist without overwriting source data.
```

### 8.5 Construct and Sequence Calculations

Tests must verify:

```text
- RNA and DNA sequence alphabets are validated.
- Sequence length is calculated correctly.
- Poly(A) tail metadata is retained separately when supplied.
- Base composition is counted correctly.
- Invalid bases fail in strict mode.
- Empty sequences fail.
- Theoretical maximum yield is calculated from limiting nucleotide availability.
- Relative yield equals actual yield divided by theoretical maximum times 100.
- Relative yield is unavailable when construct or nucleotide availability is missing.
- Relative yield warnings are emitted when units are incompatible or assumptions are incomplete.
```

Theoretical-yield fixture requirements:

```text
- one balanced construct where all NTPs are equally limiting
- one A-rich construct where ATP is limiting
- one G-rich construct where GTP is limiting
- one construct with poly(A) tail included
- one construct with user-declared NTP concentrations that differ by nucleotide
```

### 8.6 Model Fitting

Tests must verify:

```text
- OLS coefficients match independent reference calculations.
- Intercept handling is stable.
- Main-effect-only models fit correctly.
- Interaction models fit correctly.
- Quadratic models fit correctly when estimable.
- Log-transformed factor models fit correctly.
- Rank-deficient models return warnings and do not silently drop terms without reporting.
- Models with insufficient observations fail with actionable errors.
- Missing response values are excluded according to declared policy.
- Residuals, fitted values, prediction values, leverage, and standard errors are shaped correctly.
```

Diagnostics tests must verify:

```text
- R2 and adjusted R2 match reference calculations.
- Q2 or cross-validated R2 uses declared folds or leave-one-out policy.
- RMSE matches reference calculation.
- Lack-of-fit behavior is correct when replicate data is available.
- Lack-of-fit is marked unavailable when pure-error estimation is not possible.
- Prediction intervals use the declared confidence level.
- Extrapolation warnings are emitted for predictions outside the modeled region.
```

### 8.7 Effect Analysis

Tests must verify:

```text
- Main effects are reported with sign, magnitude, standard error, and source term.
- Interaction effects are labeled by both factors.
- Square terms are labeled separately from linear main effects.
- Pareto ranking is deterministic for ties.
- Contour grids respect factor ranges and fixed factors.
- Response surfaces carry prediction uncertainty when available.
- Quality constraints can classify points as pass, fail, or uncertain.
```

### 8.8 Optional Cost and COGS Analysis

Cost tests must enforce the product rule:

```text
The plugin must run without cost inputs. Cost efficiency is calculated only when the user supplies direct component costs.
```

Tests must verify:

```text
- No cost table results in economics_status = unavailable.
- No cost table does not block DOE generation, model fitting, effect analysis, recommendations, or dashboard rendering.
- User-provided component costs are retained with source metadata.
- Component usage is calculated per run or condition according to declared formula.
- Cost per reaction, cost per volume, cost per mass, and ug per currency unit are calculated consistently.
- Mixed currencies fail unless an explicit conversion table is supplied by the user.
- Negative costs fail.
- Zero costs fail unless component is explicitly marked as no-cost internal material.
- Missing component usage emits a warning and excludes that component from condition cost only when policy allows partial costing.
- The output distinguishes observed cost efficiency from predicted cost efficiency.
- The tool never fetches, infers, or defaults reagent prices.
```

Cost fixture requirements:

```text
- complete cost table for all modeled components
- cost table missing one optional component
- cost table missing one required component
- mixed-currency table
- zero-cost internal buffer component
- invalid negative enzyme cost
```

### 8.9 Desirability and Recommendation Logic

Tests must verify:

```text
- Objective direction is respected for maximize, minimize, target, and in-range responses.
- Hard constraints eliminate candidate points before ranking.
- Soft constraints affect desirability according to declared weights.
- Missing cost efficiency does not remove otherwise valid candidates unless the user makes cost mandatory.
- Recommendations include reason codes.
- Recommendations include required caveats for extrapolation, sparse data, and model instability.
- Fixed seeds produce stable candidate rankings when stochastic search is used.
- Recommended runs are distinguishable from planned, observed, and verification runs.
```

### 8.10 Design-Space Probability

Design-space probability is part of the paper-class gate. Tests must verify:

```text
- Monte Carlo sample generation is reproducible with fixed seed.
- Pass, fail, and uncertain classifications sum to 100 percent within tolerance.
- Quality constraints apply in the correct response direction.
- Confidence or prediction-interval uncertainty changes uncertain-region classification.
- Hard factor bounds are respected.
- Output grid shape matches dashboard payload contract.
```

### 8.11 Verification Planning and Comparison

Verification planning tests must verify:

```text
- Selected verification runs cover design-space edges, corners, center points, and selected optimal points according to requested policy.
- Verification plans avoid duplicate observed runs unless rerun policy allows replication.
- Each proposed run includes the factor settings, rationale, expected response range, and relevant constraints.
- Plan generation fails with a useful error when no feasible verification run exists.
```

Verification comparison tests must verify:

```text
- Observed verification results are matched to planned verification runs.
- Results are classified as within prediction interval, outside low, outside high, pass quality, fail quality, or not comparable.
- Summary metrics count each verification run once.
- Comparison warnings surface model mismatch, unit mismatch, and missing response values.
```

### 8.12 Construct Transfer

Construct-transfer tests must verify:

```text
- Source and target constructs are both registered.
- Construct length ratio is calculated correctly.
- Time scaling is applied only when requested and recorded.
- Transferred predictions preserve source-model uncertainty treatment.
- The transfer output states assumptions and does not claim biological equivalence.
- Validation experiments for the target construct can be compared against transferred prediction intervals.
```

### 8.13 Counterion DOE

Counterion tests must verify:

```text
- Magnesium counterion is modeled as a categorical factor.
- Mg:NTP ratio can interact with counterion.
- Chloride and acetate labels remain stable in outputs.
- Counterion-specific effects are shown separately from continuous Mg:NTP effects.
- Designs with categorical and continuous factors generate valid candidate sets.
```

## 9. MCP Tool Contract Tests

Each MCP tool must have tests for:

```text
- valid request
- invalid request
- dry_run behavior
- strict_validation behavior
- generated run_id behavior
- explicit run_id behavior
- artifact writes
- audit-log writes
- warning payload shape
- error payload shape
- idempotency under identical input
- overwrite_policy behavior
```

### 9.1 Launch Tool Requirements

| Tool | Required Positive Tests | Required Negative Tests |
|---|---|---|
| create_or_update_study | creates new study, updates metadata, preserves existing artifacts | invalid study id, missing required metadata |
| validate_factor_space | validates continuous and categorical factors | invalid units, impossible ranges, unsupported transforms |
| design_doe | creates declared DOE type | unsupported design type, impossible run count |
| design_optimal_doe | creates D-optimal or augmented design | rank-deficient terms, insufficient candidate set |
| import_endpoint_observations | imports clean CSV/JSON observations | unknown run ids, invalid response units |
| import_time_resolved_observations | imports kinetic observations | invalid timepoints, duplicate rows without policy |
| register_construct | registers valid construct | invalid sequence, inconsistent length metadata |
| calculate_theoretical_yield | calculates limiting-nucleotide yield | missing construct, missing NTP availability |
| fit_response_surface | fits estimable model | insufficient rows, rank-deficient model in strict mode |
| analyze_effects | produces effects and contours | missing fitted model, incompatible factor selection |
| calculate_cogs_impact | calculates direct-input cost efficiency | missing cost table, invalid costs, mixed currency |
| suggest_next_experiment | ranks feasible candidates | no feasible candidates, missing objective definition |
| plan_verification_runs | proposes verification plan | no design space or no feasible verification candidates |
| generate_dashboard_payload | emits dashboard JSON | missing required artifacts for requested view |
| launch_dashboard_preview | starts or reports local preview route | missing dashboard app, unavailable payload |

### 9.2 Post-Launch Tool Contract Requirements

| Tool | Required Positive Tests | Required Negative Tests |
|---|---|---|
| estimate_design_space_probability | reproducible probability map | missing constraints, invalid sample size |
| compare_verification_results | classifies verification outcomes | unmatched verification run ids |
| transfer_construct_model | transfers source model to target construct | missing source model, missing target construct |
| analyze_counterion_doe | fits or summarizes counterion effect | insufficient categorical coverage |
| fit_time_resolved_response_model | fits time-resolved response model | invalid timepoint structure, sparse trajectory data |

## 10. Schema and Artifact Tests

### 10.1 Schema Validation

Every persisted artifact must validate against a schema:

```text
- study metadata
- factor definitions
- response definitions
- DOE designs
- endpoint observations
- time-resolved observations
- construct records
- theoretical-yield outputs
- model-fit outputs
- effect-analysis outputs
- cost-analysis outputs
- recommendation outputs
- verification plans
- verification comparisons
- design-space outputs
- dashboard payloads
- audit logs
```

Tests must verify:

```text
- valid launch fixtures pass schemas
- invalid fixtures fail with useful error paths
- additional unknown fields are either rejected or stored according to schema policy
- schema_version is required
- method_version is required for derived artifacts
- generated_at is required for derived artifacts
- source artifact references are required for derived artifacts
- input_hash and output_hash values are present where specified
```

### 10.2 Artifact Lineage

Lineage tests must verify:

```text
- Each derived artifact points to source artifacts.
- Source hashes match the artifacts used for calculation.
- A changed source artifact changes downstream input_hash values.
- The latest pointer changes only under declared overwrite_policy.
- Historical runs remain readable after a new run is written.
```

### 10.3 Audit Log Tests

Audit tests must verify:

```text
- Every tool call appends one audit event.
- Failed validation appends a failure event.
- Skipped optional cost analysis appends a skipped event.
- Warning events include machine-readable warning codes.
- Audit events include timestamp, tool name, run id, study id, input hash, result status, and artifact paths.
- Audit logs are append-only under normal tool execution.
```

## 11. Dashboard Validation

### 11.1 Payload Contract

Dashboard tests must verify:

```text
- The dashboard rejects malformed payloads.
- The dashboard renders unavailable states from payload status fields.
- The dashboard does not calculate scientific values client-side.
- Payload version mismatches show a clear incompatible-payload state.
- Artifact links and audit metadata render where provided.
```

### 11.2 View Tests

Required view-level tests:

```text
- Overview shows study identity, factor summary, response summary, run counts, latest model status, economics status, and warnings.
- Matrix shows planned, observed, recommended, augmented, and verification runs with distinct labels.
- Time Courses shows kinetic data when available and an unavailable state when absent.
- Effects shows main effects, interactions, square terms, warnings, and selected response controls.
- Relative Yield shows theoretical-yield assumptions and unavailable state when construct data is missing.
- Economics shows direct-input cost provenance and unavailable state when costs are absent.
- Recommendations shows ranked runs, objectives, constraints, and reason codes.
- Verification shows planned and observed verification classifications.
- Diagnostics shows model diagnostics, residuals, leverage, fit warnings, and audit links.
- Design Space shows pass, fail, and uncertain regions when paper-class output is available.
- Constructs shows source and target construct metadata.
- Counterion shows categorical counterion comparisons when available.
```

### 11.3 Responsive Layout Tests

Browser tests must verify:

```text
- Header, tab navigation, and primary content fit in desktop, tablet, and mobile viewports.
- Tables remain usable through horizontal scrolling or responsive column controls.
- Chart legends do not overlap charts.
- Warning banners do not cover primary controls.
- Empty states preserve layout stability.
- Buttons and controls have stable dimensions.
- Text does not overflow fixed-format UI elements.
```

### 11.4 Accessibility Tests

Dashboard accessibility tests must verify:

```text
- All interactive controls have accessible names.
- Tab order is logical.
- Charts have text summaries or table fallbacks.
- Color is not the only indicator of pass, fail, uncertain, observed, predicted, recommended, or unavailable state.
- Focus states are visible.
- Keyboard navigation works for tabs, filters, menus, and table controls.
```

### 11.5 Visual QA

Visual QA must capture screenshots for:

```text
- launch workflow with no costs
- launch workflow with costs
- invalid data state
- rank-deficient model warning
- time-resolved IVT workflow
- verification workflow
- mobile overview
- mobile matrix
- mobile economics unavailable state
```

Screenshots must be reviewed for:

```text
- blank panels
- overlapping UI
- unreadable text
- broken charts
- missing warning context
- incorrect status labels
- missing distinction between observed and predicted results
```

## 12. End-to-End Test Scenarios

### 12.1 Scenario A: Launch DOE Without Costs

Purpose:

```text
Prove the plugin works without economics inputs.
```

Steps:

```text
1. Create an IVT study.
2. Define four factors: Mg:NTP ratio, NTP concentration, DNA template, T7 RNAP.
3. Define responses: mRNA yield, dsRNA score, relative yield.
4. Generate a D-optimal DOE.
5. Import endpoint observations.
6. Register construct.
7. Calculate theoretical yield.
8. Fit response-surface models.
9. Analyze effects.
10. Generate dashboard payload.
11. Launch dashboard preview.
```

Expected results:

```text
- DOE matrix is generated and schema-valid.
- Observations import successfully.
- Theoretical yield is calculated.
- Relative yield is calculated.
- Model fit artifacts are created.
- Effects artifacts are created.
- Economics status is unavailable.
- Dashboard renders with economics unavailable and no blocked scientific workflow.
```

### 12.2 Scenario B: Launch DOE With Direct Component Costs

Purpose:

```text
Prove optional cost analysis works when the user supplies direct component costs.
```

Steps:

```text
1. Start from Scenario A artifacts.
2. Supply a component cost table for NTPs, Mg salt, DNA template, T7 RNAP, buffer, pyrophosphatase, and RNase inhibitor.
3. Run calculate_cogs_impact.
4. Regenerate dashboard payload.
5. Review economics tab.
```

Expected results:

```text
- Cost table is validated.
- Cost per condition is calculated.
- Cost efficiency is calculated.
- Cost provenance is shown.
- No external price data is used.
- Economics tab distinguishes user-supplied inputs from derived outputs.
```

### 12.3 Scenario C: Iterative D-Optimal Augmentation

Purpose:

```text
Prove the workflow can add new experiments to improve a model.
```

Steps:

```text
1. Create initial D-optimal design with a sparse run count.
2. Import observations.
3. Fit model and collect warnings.
4. Request augmented D-optimal design.
5. Import augmented observations.
6. Refit model.
7. Compare diagnostics across iterations.
```

Expected results:

```text
- Existing runs are preserved.
- New runs are clearly labeled as augmented.
- Model diagnostics improve or warnings explain why they do not.
- Dashboard shows iteration history.
```

### 12.4 Scenario D: Time-Resolved IVT Analysis

Purpose:

```text
Prove kinetic observations can be imported and reviewed.
```

Steps:

```text
1. Import time-resolved mRNA and NTP observations for IVT runs.
2. Validate timepoint structure.
3. Generate dashboard payload.
4. Review time-course view.
5. Fit time-resolved response model when paper-class tools are enabled.
```

Expected results:

```text
- Timepoints are normalized and sorted.
- Trajectories render by run and response.
- Endpoint and time-resolved data remain distinct.
- Time-resolved model output is schema-valid when generated.
```

### 12.5 Scenario E: Verification Planning and Comparison

Purpose:

```text
Prove the product can propose and evaluate verification experiments.
```

Steps:

```text
1. Fit IVT response models.
2. Define quality constraint for dsRNA score.
3. Define objective for yield and optional cost efficiency.
4. Plan verification runs.
5. Import verification observations.
6. Compare verification observations against predicted ranges.
7. Regenerate dashboard payload.
```

Expected results:

```text
- Verification runs include rationale and expected response ranges.
- Verification results are classified.
- Out-of-range results are surfaced with model warnings.
- Dashboard shows planned and observed verification state.
```

### 12.6 Scenario F: Construct Transfer

Purpose:

```text
Prove the product can support construct-transfer analysis without overstating validity.
```

Steps:

```text
1. Register source eGFP-like construct.
2. Fit source time-resolved model.
3. Register longer target construct.
4. Run transfer_construct_model.
5. Import target validation observations.
6. Compare target trajectories against transferred prediction intervals.
```

Expected results:

```text
- Length ratio is calculated.
- Transfer assumptions are recorded.
- Prediction intervals are preserved or widened according to method policy.
- Dashboard states transfer assumptions and validation status.
```

### 12.7 Scenario G: Counterion DOE

Purpose:

```text
Prove categorical counterion analysis works with Mg:NTP-related stress conditions.
```

Steps:

```text
1. Define Mg:NTP ratio as a continuous factor.
2. Define magnesium counterion as categorical factor with chloride and acetate levels.
3. Generate DOE.
4. Import observations.
5. Analyze counterion DOE.
6. Review dashboard counterion view.
```

Expected results:

```text
- Categorical factor encoding is stable.
- Counterion effects are separated from continuous Mg:NTP effects.
- Interaction effects are reported when estimable.
- Dashboard renders counterion comparison clearly.
```

### 12.8 Scenario H: Invalid and Sparse Data

Purpose:

```text
Prove fail-safe behavior.
```

Steps:

```text
1. Import observations with missing values, invalid units, and unknown run ids.
2. Attempt model fitting with insufficient observations.
3. Attempt cost analysis with missing direct costs.
4. Generate dashboard payload from partial state.
```

Expected results:

```text
- Invalid rows fail or warn according to strict_validation.
- Insufficient models do not produce fake coefficients.
- Missing costs produce economics unavailable.
- Dashboard renders partial state with clear warnings.
```

## 13. Reproducibility Tests

Tests must verify:

```text
- Fixed-seed DOE generation produces byte-stable artifact content except for allowed timestamp fields.
- Fixed-seed Monte Carlo design-space analysis produces stable summary statistics within tolerance.
- Identical input artifacts produce identical input hashes.
- Changed input artifacts produce changed input hashes.
- Method version changes are recorded in derived outputs.
- Package versions are recorded in run metadata.
- Dashboard payloads generated from unchanged artifacts are stable.
```

Allowed nondeterministic fields:

```text
- generated_at timestamp
- run_id when omitted by caller
- local preview port when automatic port selection is used
```

## 14. Performance Tests

Launch performance thresholds on a typical developer laptop:

| Operation | Dataset Size | Threshold |
|---|---:|---:|
| schema validation | 1 study payload | under 1 second |
| D-optimal design | 1,000 candidate points, 20 runs | under 10 seconds |
| endpoint import | 1,000 rows | under 3 seconds |
| time-resolved import | 10,000 rows | under 8 seconds |
| OLS model fit | 1,000 rows, 30 terms | under 5 seconds |
| effect grid generation | 10,000 grid points | under 5 seconds |
| dashboard payload generation | medium IVT study | under 3 seconds |
| dashboard first render | medium IVT study | under 3 seconds |

Paper-class performance thresholds:

| Operation | Dataset Size | Threshold |
|---|---:|---:|
| Monte Carlo design-space estimation | 100,000 samples | under 30 seconds |
| construct-transfer comparison | 100 runs x 20 timepoints | under 10 seconds |
| counterion DOE model fit | 500 rows | under 5 seconds |

Performance test outputs must include elapsed time, dataset size, method version, and machine class.

## 15. Security and Privacy Tests

Security tests must verify:

```text
- Tool requests cannot write outside allowed study output directories.
- Path traversal attempts are rejected.
- Artifact paths are normalized.
- Dashboard preview serves only intended local files and payloads.
- The backend does not transmit study data over the network in launch workflows.
- Error messages do not dump full sensitive payloads.
- Logs do not include large raw sequence data unless explicitly configured for debug mode.
- Generated HTML or dashboard content escapes user-provided labels.
- CSV imports do not execute spreadsheet formulas.
```

Privacy tests must verify:

```text
- Study artifacts remain local by default.
- No reagent prices are fetched externally.
- No construct sequences are sent to external services.
- No observation data is uploaded by the MCP server or dashboard.
```

## 16. Regression Policy

Regression tests must be added when:

```text
- A bug is fixed in scientific calculation.
- A schema field changes.
- A warning code changes.
- A dashboard payload shape changes.
- A DOE generation method changes.
- A model-fitting method changes.
- A cost-calculation formula changes.
- A paper-class workflow tool is promoted to launch scope.
```

Golden-output updates require:

```text
- explicit method version change when scientific behavior changed
- diff summary of old and new values
- explanation of numerical tolerance changes
- reviewer confirmation that changes are scientifically intended
```

## 17. Numerical Tolerance Policy

Default tolerances:

```text
- exact match for IDs, labels, schema versions, warning codes, and classifications
- absolute tolerance of 1e-9 for simple algebraic calculations
- relative tolerance of 1e-8 for regression coefficients where matrix conditioning is normal
- relative tolerance of 1e-6 for cross-validation metrics
- relative tolerance of 1e-4 for Monte Carlo probability summaries
```

Tolerances must be tightened or loosened per test when justified by:

```text
- matrix conditioning
- stochastic sampling
- package-level numerical differences
- intentionally approximate algorithms
```

Any tolerance above 1e-4 for core launch calculations requires a test comment explaining why the result cannot be made more deterministic.

## 18. Warning and Error Validation

Warnings must be tested as first-class outputs. Required warning categories:

```text
- sparse_design
- rank_deficient_model
- extrapolation
- insufficient_replicates
- lack_of_fit_unavailable
- missing_cost_inputs
- partial_cost_inputs
- construct_missing
- theoretical_yield_unavailable
- relative_yield_unavailable
- design_space_unavailable
- verification_unavailable
- time_resolved_data_missing
- transfer_assumption_required
```

Errors must be tested for:

```text
- invalid_schema
- invalid_factor_space
- invalid_unit
- invalid_sequence
- invalid_cost_table
- unsupported_design_type
- insufficient_observations
- missing_required_artifact
- artifact_hash_mismatch
- unsafe_path
```

Each warning and error test must verify:

```text
- machine-readable code
- human-readable message
- affected artifact or input path
- severity
- recommended user action
```

## 19. Manual Review Checklist

Manual release review must inspect:

```text
- One no-cost IVT workflow from start to dashboard.
- One direct-cost IVT workflow from cost table to economics dashboard.
- One invalid-data workflow with warnings and blocked model fit.
- One dashboard mobile screenshot.
- One generated audit log.
- One generated model-fit artifact.
- One generated dashboard payload.
- One generated verification plan.
```

Reviewer questions:

```text
- Can a scientist tell which results are measured, predicted, recommended, or unavailable?
- Can a scientist identify the source data and method version for a model result?
- Does the product continue when costs are absent?
- Does the product avoid implying cost data was inferred?
- Are model caveats visible where decisions are made?
- Are recommendations constrained by declared factors and quality limits?
- Does the dashboard make partial or invalid state obvious?
```

## 20. Defect Severity

### 20.1 Severity 0

Release-blocking defects:

```text
- fabricated numerical outputs
- silent wrong scientific calculation
- cost calculation without user-provided costs
- data loss or artifact overwrite outside declared policy
- unsafe file write outside study directory
- dashboard showing stale results as current
- missing audit trail for derived scientific output
```

### 20.2 Severity 1

Release-blocking unless explicitly deferred from release scope:

```text
- incorrect warning or unavailable-state behavior
- unstable fixed-seed output
- broken launch workflow
- dashboard view fails for core launch payload
- schema mismatch between backend and dashboard
- invalid model diagnostics
```

### 20.3 Severity 2

Must be fixed before paper-class claim, may ship in launch with documented limitation:

```text
- incomplete paper-class workflow coverage
- missing non-core chart
- degraded performance above paper-class threshold
- minor visual layout issue that does not block interpretation
- incomplete optional export artifact
```

### 20.4 Severity 3

Can be tracked after launch:

```text
- cosmetic issue
- non-blocking copy improvement
- additional fixture coverage for already passing behavior
- developer-experience improvement
```

## 21. Test Report Format

Every release candidate must produce a validation report with:

```text
- release candidate identifier
- date
- method versions
- package versions
- schema versions
- test command summary
- pass/fail count by suite
- failed tests and severity
- skipped tests and reason
- golden-output diffs
- performance results
- dashboard screenshot paths
- known limitations
- release-gate decision
```

The report must explicitly state:

```text
- whether launch readiness gate passed
- whether paper-class workflow gate passed
- whether optional COGS behavior passed both absent-cost and direct-cost scenarios
```

## 22. Launch Acceptance Criteria

The first product launch is acceptable when all of the following are true:

```text
1. The launch workflow succeeds end to end with no cost inputs.
2. The launch workflow succeeds end to end with direct component costs.
3. The plugin never blocks core DOE/modeling analysis because cost inputs are absent.
4. The plugin never calculates cost efficiency from inferred or fetched prices.
5. D-optimal design generation is deterministic under fixed seed.
6. Endpoint and time-resolved observation imports preserve source data.
7. Theoretical and relative yield calculations pass sequence fixtures.
8. Response-surface modeling diagnostics pass reference tests.
9. Recommendations include constraints, objectives, and caveats.
10. Dashboard payload generation is schema-valid.
11. Dashboard preview renders all launch views without blocking errors.
12. Audit logs identify every derived artifact and source artifact.
13. Security tests pass for path handling and local-data behavior.
14. Manual release review confirms measured, predicted, recommended, verification, and unavailable states are visually distinct.
```

## 23. Paper-Class Acceptance Criteria

The product can be described as able to support the reference paper's class of design and analysis when all of the following are true:

```text
1. Iterative D-optimal DOE with augmentation works on a four-factor IVT knowledge space.
2. Endpoint and time-resolved IVT measurements can be imported, modeled, and visualized.
3. mRNA yield, dsRNA or quality response, relative yield, and optional direct-input cost efficiency can be modeled as separate responses.
4. Theoretical yield is calculated from construct sequence and nucleotide availability.
5. Multi-response desirability can balance yield, quality, relative yield, and optional cost efficiency.
6. Design-space probability or equivalent pass/fail/uncertain classification can be produced from model uncertainty.
7. Verification runs can be planned and compared against model predictions.
8. Construct-transfer analysis can compare a source construct model against a longer target construct under declared assumptions.
9. Counterion DOE with categorical magnesium salt factor can be analyzed.
10. Dashboard views expose the complete workflow without relying on manual interpretation of raw JSON.
```

## 24. Final Validation Rule

The product should never present an analysis as complete because Codex can explain it fluently. An analysis is complete only when the scientific backend has produced schema-valid artifacts, the dashboard renders those artifacts without recalculating them, warnings are visible, and the validation gates for that feature have passed.
