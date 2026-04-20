# Dashboard UX Spec: Codex Scientific Toolchain

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
- Canonical Build Contract.md
```

## 1. Purpose

This document defines the user experience contract for the local React dashboard used by the Codex Scientific Toolchain. It specifies the dashboard routes, information architecture, views, interactions, chart behavior, visual states, warning placement, accessibility expectations, and acceptance criteria.

The dashboard is a review and interpretation surface. It renders scientific state produced by MCP tools. It must not perform final scientific calculations such as DOE generation, model fitting, theoretical-yield calculation, cost calculation, optimization, or design-space classification.

## 2. UX Goals

The dashboard must help a scientist quickly answer:

```text
- What study am I looking at?
- Which factors and responses are in scope?
- What experiments are planned, observed, augmented, recommended, or verification runs?
- Which results are measured, derived, predicted, or recommended?
- Which model warnings affect interpretation?
- What effects and interactions appear important?
- Where are quality constraints satisfied or risky?
- Is cost efficiency available, and if so what user-provided cost table produced it?
- What should I run next?
- What has been experimentally verified?
- Which analyses are unavailable because required inputs are missing?
```

## 3. Product Boundaries

### 3.1 Dashboard Owns

```text
- Rendering study state.
- Filtering and sorting tables.
- Selecting responses, factors, scenarios, and runs.
- Chart display and hover details.
- Showing warnings and unavailable states.
- Linking views to source artifacts and audit metadata.
- Presenting local preview routes.
```

### 3.2 Dashboard Does Not Own

```text
- DOE generation.
- Model fitting.
- Coefficient calculation.
- Theoretical-yield calculation.
- Relative-yield calculation.
- Cost and cost-efficiency calculation.
- Design-space probability simulation.
- Next-experiment optimization.
- Verification comparison.
```

## 4. Primary Users and Review Modes

### 4.1 Process-Development Scientist

Needs dense, inspectable views:

```text
- experiment matrix
- response trends
- model warnings
- next-run queue
- verification plan
```

### 4.2 Bioprocess or IVT Engineer

Needs domain-specific views:

```text
- IVT factors and ranges
- time-course plots
- theoretical and relative yield
- dsRNA threshold views
- cost-efficiency tradeoffs
- construct comparison
```

### 4.3 Scientific Data Analyst

Needs traceability:

```text
- formulas
- coefficients
- R2/Q2/RMSE
- residual diagnostics
- artifact hashes
- payload version
- method versions
```

### 4.4 Codex/User Collaborative Review

The dashboard is opened in the Codex in-app browser. It should support quick visual review and comments, but must also be understandable when viewed outside Codex in a normal local browser.

## 5. Information Architecture

### 5.1 Routes

Launch routes:

```text
/
  Redirects to latest known study when available, otherwise shows empty state.

/studies/:studyId
  Main dashboard with tabbed sections.

/studies/:studyId/matrix
  Focused experiment matrix.

/studies/:studyId/effects
  Effects, Pareto, factor-response, and contour views.

/studies/:studyId/diagnostics
  Model diagnostics, warnings, payload, and audit metadata.
```

Post-launch routes:

```text
/studies/:studyId/design-space
  Design-space probability maps.

/studies/:studyId/economics
  Cost-efficiency and cost breakdown analysis.

/studies/:studyId/verification
  Verification plan and observed verification comparison.

/studies/:studyId/constructs
  Construct metadata and transfer analysis.
```

Launch may implement the post-launch routes as tabs with unavailable states rather than separate routes.

### 5.2 Main Dashboard Tabs

Required launch tabs:

```text
Overview
Matrix
Time Courses
Effects
Relative Yield
Economics
Recommendations
Verification
Diagnostics
```

Post-launch tabs:

```text
Design Space
Constructs
Counterion
Audit
```

### 5.3 Global Page Regions

Every study route uses:

```text
Study header
Global warning strip
Primary tab navigation
Active view content
Context side panel or details drawer
Payload/audit footer
```

## 6. Global Layout

### 6.1 Study Header

The header must show:

```text
- study title
- study ID
- domain template
- active design ID
- active fit ID when available
- active construct ID when available
- payload generated timestamp
- payload version
- overall study status
```

Header actions:

```text
- refresh payload, display-only button that explains Codex must run generate_dashboard_payload
- copy study ID
- open diagnostics
```

Because the dashboard cannot call MCP tools directly at launch, action buttons that require computation must show clear disabled or informational states instead of pretending to run calculations.

### 6.2 Global Warning Strip

The global warning strip appears below the header when any warning has severity `warning` or `blocking`.

Behavior:

```text
- Blocking warnings are shown first.
- Warnings are grouped by affected section.
- User can jump to the relevant section.
- Warnings never disappear because a chart is filtered.
```

### 6.3 Tabs

Tabs must:

```text
- show availability status;
- show warning count when relevant;
- preserve selected response/factor where possible across tabs;
- support direct route linking.
```

Availability indicators:

```text
available
unavailable_missing_input
unavailable_not_run
unavailable_failed_validation
unavailable_unsupported
```

### 6.4 Details Drawer

The dashboard uses a right-side details drawer for row, point, warning, and artifact inspection.

Drawer content can include:

```text
- selected run details
- selected chart point details
- source artifact path
- model formula
- warning details
- cost breakdown
- verification rationale
```

The drawer must never obscure core table or chart controls on desktop. On mobile it becomes a full-height bottom sheet.

### 6.5 Footer

The footer must show:

```text
- payload hash
- source artifact hashes
- generated by tool name
- method versions
- schema version
- generated timestamp
```

Footer content can be collapsed but must be available from every study route.

## 7. Visual Design Direction

### 7.1 Tone

The dashboard is a scientific review surface. It should be dense, calm, and precise, not marketing-like.

Design qualities:

```text
- high information density
- clear hierarchy
- restrained color
- strong table readability
- explicit warning and unavailable states
- minimal decorative elements
```

### 7.2 Color Semantics

Use color semantically:

```text
blue:
  selected response or neutral informational state

green:
  feasible, within threshold, available, verified within interval

amber:
  warning, weak model, missing optional input, prediction uncertainty

red:
  blocking issue, outside threshold, failed validation, outside prediction interval

gray:
  unavailable, not run, diagnostic metadata
```

Rules:

```text
- Do not rely on color alone; pair color with text, icon, or pattern.
- CQA threshold regions must be distinguishable for color-blind users.
- Cost-efficiency should not use the same palette as dsRNA risk.
```

### 7.3 Typography and Density

Requirements:

```text
- Use tabular numerals for tables and metric cards.
- Keep chart labels readable at dashboard widths.
- Do not scale font size with viewport width.
- Avoid text truncation for factor names unless tooltip and full label are available.
```

### 7.4 Layout Constraints

```text
- No nested cards for page sections.
- Use full-width section bands or unframed layouts.
- Cards are allowed for repeated items such as warning summaries, recommendations, or metric tiles.
- Tables and charts must have stable dimensions so loading and hover states do not shift layout.
```

## 8. Common UI Components

### 8.1 Availability Panel

Shown when a section cannot render.

Required content:

```text
- status
- reason
- required missing inputs
- tool that would produce the missing artifact
- source artifact state, if relevant
```

Example:

```text
Economics unavailable
Cost efficiency was not calculated because direct component costs were not supplied.
Required tool: calculate_cogs_impact
```

### 8.2 Warning List

Warning list rows show:

```text
- severity
- warning code
- message
- affected field or section
- details
- source artifact
```

Interactions:

```text
- filter by severity
- jump to affected section
- open details drawer
```

### 8.3 Metric Tile

Used for key values such as run count, R2, Q2, cost efficiency, and relative yield.

Requirements:

```text
- show value, unit, label, source type, and warning state;
- avoid false precision;
- show unavailable state when value is null;
- link to source artifact or section.
```

### 8.4 Source Badge

Every displayed scientific value should identify source type:

```text
measured
derived
predicted
recommended
planned
verified
unavailable
```

### 8.5 Unit Label

Units must appear:

```text
- in table headers;
- chart axes;
- metric tiles;
- tooltip values;
- details drawer rows.
```

### 8.6 Threshold Marker

Threshold markers are used for dsRNA and other CQAs.

Requirements:

```text
- label threshold value and operator;
- show pass/fail semantics;
- work on charts and tables;
- avoid implying verification when threshold is model-predicted.
```

## 9. Overview Tab

### 9.1 Purpose

The overview tab gives a compact study status snapshot and directs the user to the next relevant review area.

### 9.2 Required Content

```text
- study metadata
- active factor space summary
- response goals summary
- design status
- observation import status
- model status
- theoretical/relative-yield status
- economics status
- recommendation status
- verification status
- top warnings
```

### 9.3 Status Summary Rows

Each row includes:

```text
- section name
- availability status
- latest artifact
- latest timestamp
- warning count
- primary action text
```

Primary action text is display-only guidance such as:

```text
Run fit_response_surface to populate this section.
```

### 9.4 Acceptance Criteria

```text
- User can tell study maturity within 10 seconds.
- Missing major inputs are visible without opening diagnostics.
- Economics status is explicit and does not imply failure when costs are absent.
- Top warnings link to affected sections.
```

## 10. Matrix Tab

### 10.1 Purpose

The matrix tab shows planned, observed, augmented, recommended, and verification runs in a dense table.

### 10.2 Required Columns

```text
run_id
run_type
iteration
randomization_order
block
replicate
factor columns with units
response columns when observed
derived response columns when available
prediction columns when available
warning count
```

### 10.3 Run Type Styling

```text
model_building:
  neutral

augmentation:
  blue accent

center_point:
  gray accent

replicate:
  gray patterned accent

verification:
  green or amber accent depending on status

candidate_recommendation:
  blue outline
```

### 10.4 Interactions

```text
- sort by any numeric or categorical column;
- filter by run_type, iteration, warnings, observed/unobserved;
- pin identifier columns;
- open row details drawer;
- show raw, coded, or transformed factor values when available;
- toggle measured/derived/predicted columns.
```

### 10.5 Cell States

```text
measured:
  normal text with measured badge

derived:
  derived badge and formula source in tooltip

predicted:
  predicted badge and interval where available

missing:
  muted unavailable state

warning:
  warning icon with details drawer link
```

### 10.6 Acceptance Criteria

```text
- Table remains readable with at least 12 runs and 4 factors.
- User can distinguish planned rows from observed rows.
- User can distinguish measured, derived, predicted, and recommended values.
- Units are visible in headers.
- Row selection opens a details drawer with all available metadata.
```

## 11. Time Courses Tab

### 11.1 Purpose

The time courses tab renders long-format kinetic observations by run and analyte.

### 11.2 Required Views

```text
- analyte selector
- response/run selector
- line plot by run
- endpoint summary marker
- timecourse coverage table
- unavailable state when no time-resolved data exists
```

### 11.3 Chart Behavior

X-axis:

```text
time with normalized unit
```

Y-axis:

```text
selected analyte value and unit
```

Tooltip:

```text
run_id
time
value
unit
sample_id when available
replicate when available
endpoint summary flag when applicable
```

### 11.4 Endpoint Summary Display

Endpoint summary markers must show:

```text
- summary method
- selected time
- derived value
- source table
- warnings
```

### 11.5 Acceptance Criteria

```text
- User can inspect mRNA concentration trajectory by run.
- User can switch analytes without losing run filters.
- Endpoint summary method is visible.
- Missing or insufficient timecourse data is explained.
```

## 12. Effects Tab

### 12.1 Purpose

The effects tab shows model-derived effects, factor-response curves, interaction slices, and contours.

### 12.2 Required Layout

```text
response selector
model status strip
Pareto/effect ranking
factor-response panel
contour panel
effect details drawer
```

### 12.3 Model Status Strip

Shows:

```text
- formula
- R2
- Q2
- RMSE
- residual degrees of freedom
- rank status
- model warning count
```

If Q2 is unavailable, show:

```text
Q2 unavailable: <reason>
```

### 12.4 Pareto Chart

Requirements:

```text
- horizontal bar chart;
- sorted by absolute effect magnitude;
- sign encoded by direction and label;
- warning state when significance threshold is unavailable;
- no p-value or significance marker unless available in model artifact.
```

Tooltip:

```text
term
effect value
sign
rank
standard error when available
warnings
```

### 12.5 Factor-Response Curves

Controls:

```text
factor selector
hold strategy selector
confidence/prediction band toggle when available
```

Requirements:

```text
- show hold values;
- show prediction interval only when available;
- mask extrapolated regions;
- distinguish measured observations from predicted curve.
```

### 12.6 Contour Panel

Controls:

```text
factor X selector
factor Y selector
response selector
hold strategy selector
overlay toggles: observations, constraints, cost, dsRNA threshold
```

Requirements:

```text
- contour map uses predicted response grid;
- infeasible regions are masked;
- dsRNA threshold overlay labels threshold;
- cost overlay appears only when economics is calculated;
- chart does not imply design-space probability unless probability artifact exists.
```

### 12.7 Acceptance Criteria

```text
- User can see model warnings before interpreting effects.
- Pareto chart never shows unsupported significance.
- Factor-response curves show hold values and units.
- Contour map masks infeasible regions and labels thresholds.
```

## 13. Relative Yield Tab

### 13.1 Purpose

The relative yield tab explains theoretical yield, limiting NTP, and relative yield by run or condition.

### 13.2 Required Content

```text
- construct summary
- nucleotide counts
- molecular weight source
- limiting NTP table
- theoretical yield table
- measured yield source
- relative yield table
- relative yield chart
- warnings for missing inputs or >100% relative yield
```

### 13.3 Chart Options

```text
- relative yield by run
- relative yield vs selected factor
- theoretical vs measured yield scatter
- limiting NTP distribution
```

### 13.4 Formula Provenance

The view must show formula text:

```text
relative_yield_percent = 100 * measured_yield / theoretical_yield
```

And link to:

```text
derived/theoretical_yield.json
constructs.json
```

### 13.5 Acceptance Criteria

```text
- User can identify limiting NTP per run.
- User can see whether molecular weight was calculated or user-supplied.
- Relative yield unavailable states identify missing inputs.
- Values over 100% warn without breaking the view.
```

## 14. Economics Tab

### 14.1 Purpose

The economics tab shows optional cost-efficiency analysis based only on user-supplied component costs.

### 14.2 Availability States

If no costs:

```text
Economics unavailable
Cost efficiency was not calculated because direct component costs were not supplied.
```

If invalid costs:

```text
Economics failed validation
Show missing fields or unit/currency issues.
```

If calculated:

```text
Show component-cost provenance, condition costs, cost efficiency, and warnings.
```

### 14.3 Required Content When Available

```text
- component cost table
- cost input hash
- currency
- cost basis units
- total condition cost by run
- cost breakdown by component
- cost-efficiency metric
- product mass source: measured, derived, or predicted
- baseline comparison when available
- sensitivity range when available
```

### 14.4 Charts

Required launch charts:

```text
- cost efficiency by run or condition
- cost breakdown stacked bar for selected run
- cost efficiency vs selected response scatter
```

Post-launch charts:

```text
- cost-efficiency contour overlay
- sensitivity tornado chart
- scenario comparison scatter
```

### 14.5 Guardrails

The view must show:

```text
- "Uses user-provided component costs only."
- "Model-predicted" label when product mass is predicted.
- "Measured" label when product mass is observed.
- "No validated savings claim" when baseline or verification is missing.
```

### 14.6 Acceptance Criteria

```text
- Missing costs do not look like an error in the overall study.
- Cost table provenance is visible.
- Mixed currency or missing basis errors are clear.
- Dashboard never implies prices were fetched.
- Dashboard never states validated COGS reduction without required evidence.
```

## 15. Recommendations Tab

### 15.1 Purpose

The recommendations tab shows next-experiment candidates produced by `suggest_next_experiment`.

### 15.2 Required Content

```text
- recommendation set ID
- strategy
- objective list
- ranked recommendations
- factor settings
- predicted responses
- desirability score
- uncertainty score
- constraint status
- rationale type
- warnings
```

### 15.3 Recommendation Table

Columns:

```text
rank
rationale_type
constraint_status
factor settings
predicted yield
predicted dsRNA
relative yield when available
cost efficiency when available
desirability
uncertainty
warning count
```

### 15.4 Rationale Types

Display labels:

```text
exploitation:
  likely improvement based on current model

exploration:
  reduces uncertainty or samples sparse region

constraint_probing:
  tests boundary or quality-risk region

verification:
  confirms predicted optimum or design-space edge

control:
  repeated or reference condition
```

### 15.5 Acceptance Criteria

```text
- User can distinguish recommendations from planned/observed runs.
- Every recommendation shows why it was selected.
- Cost efficiency appears only when economics is calculated.
- Weak model warnings remain visible.
```

## 16. Verification Tab

### 16.1 Purpose

The verification tab shows planned verification runs and, post-launch, comparison of observed verification results against predictions.

### 16.2 Launch Required Content

```text
- verification plan ID
- verification run table
- run type
- factor settings
- predicted responses
- prediction intervals when available
- purpose
- selection rationale
- warnings
```

### 16.3 Post-Launch Result Content

```text
- observed verification response
- predicted value
- prediction interval
- within interval
- prediction error
- relative error
- interpretation: supports_model, challenges_model, inconclusive, outside_scope
```

### 16.4 Visual States

```text
planned:
  neutral planned state

within_interval:
  green verified-within-model state

outside_interval:
  red/amber challenges-model state

missing_observation:
  unavailable state

interval_unavailable:
  predicted-vs-observed only, no interval judgment
```

### 16.5 Acceptance Criteria

```text
- Dashboard never calls a design space verified without observed comparison.
- Verification plan is visible before verification results exist.
- Observed verification results are linked to planned run IDs.
- Interval status is visually and textually clear.
```

## 17. Diagnostics Tab

### 17.1 Purpose

The diagnostics tab is the traceability and trust surface.

### 17.2 Required Sections

```text
- payload validation state
- source artifacts
- audit summary
- model diagnostics
- warning registry for current payload
- unavailable section registry
- schema and method versions
```

### 17.3 Model Diagnostics

Show per model:

```text
- response
- formula
- n observations
- model columns
- rank
- residual degrees of freedom
- R2
- adjusted R2
- Q2
- RMSE
- condition number
- lack-of-fit status
- high leverage rows
- large residual rows
```

### 17.4 Payload Diagnostics

Show:

```text
- payload ID
- payload hash
- schema version
- generated at
- generated by
- source artifact count
- missing source artifacts
- hash mismatch warnings
```

### 17.5 Acceptance Criteria

```text
- A data analyst can trace any displayed value to an artifact.
- Weak model status is visible even if user does not open chart tabs.
- Payload validation errors are visible and block misleading charts.
```

## 18. Design Space Tab

### 18.1 Purpose

The design space tab shows quality threshold maps and probability-of-failure regions when available.

### 18.2 Launch Behavior

At launch, this tab may show:

```text
- unavailable state for Monte Carlo design-space probability;
- quality threshold definition;
- model-predicted contour foundation when generated by analyze_effects;
- guidance that estimate_design_space_probability is required for probability maps.
```

### 18.3 Paper-Class Behavior

When `design_space_probability.json` exists, show:

```text
- factor X/Y selectors
- probability-of-failure map
- in/out/unknown classification
- threshold details
- simulation settings
- valid simulation count
- failure limit
- warnings
```

### 18.4 Acceptance Criteria

```text
- User can distinguish predicted response contours from probability-of-failure maps.
- Missing Monte Carlo output does not look like zero risk.
- Probability map shows simulation settings.
- Threshold labels remain visible.
```

## 19. Constructs Tab

### 19.1 Purpose

The constructs tab shows construct metadata and, post-launch, construct-transfer analysis.

### 19.2 Launch Content

```text
- construct ID
- display name
- construct type
- transcript length
- poly(A) tail length
- nucleotide counts
- molecular weight and source
- modifications
- theoretical-yield availability
```

### 19.3 Post-Launch Transfer Content

```text
- reference construct
- target construct
- length ratio
- nucleotide composition difference
- molarity adjustment
- time-scaling assumption
- transfer warnings
- validation status
```

### 19.4 Acceptance Criteria

```text
- Dashboard can compare construct metadata without implying transfer prediction.
- Transfer assumptions are visible when transfer analysis exists.
- Warnings appear for large length or composition differences.
```

## 20. Counterion Tab

### 20.1 Purpose

The counterion tab shows a specialized view for Mg2+ counterion follow-up DOE.

### 20.2 Content

```text
- Mg:NTP ratio levels or range
- counterion levels
- response by counterion
- interaction plot when estimable
- model diagnostics
- warnings for sparse categorical levels
```

### 20.3 Launch Behavior

This tab can be unavailable at launch unless counterion factor exists. If `mg_counterion` is present as a categorical factor, the generic matrix/effects views must still render it correctly.

### 20.4 Acceptance Criteria

```text
- Categorical counterion is visible in matrix and effects views.
- Interaction plot appears only when estimable.
- Dashboard states conclusions apply only within tested conditions.
```

## 21. Loading, Empty, Error, and Stale States

### 21.1 Loading

Loading states must:

```text
- preserve layout dimensions;
- show which payload section is loading;
- avoid replacing tables with layout-shifting spinners.
```

### 21.2 Empty

Empty states are used when no study or payload exists.

Required text:

```text
No study payload is available.
Run generate_dashboard_payload from Codex to create one.
```

### 21.3 Unavailable

Unavailable states are scientific states, not UI errors.

They must show:

```text
- reason
- required input
- producing tool
- whether workflow can continue without it
```

### 21.4 Error

Error states show:

```text
- error code
- message
- affected section
- source payload field
- recovery action
```

### 21.5 Stale Payload

If payload source artifact hashes do not match latest known artifacts, show stale warning:

```text
Payload may be stale. Regenerate dashboard_payload.json.
```

The dashboard must not attempt to regenerate the payload itself at launch.

## 22. Responsive Behavior

### 22.1 Desktop

Target:

```text
1280px and wider
```

Behavior:

```text
- full tab navigation;
- matrix with pinned columns;
- charts and details drawer side-by-side;
- diagnostics tables visible without horizontal page scroll, though data tables may scroll internally.
```

### 22.2 Tablet

Target:

```text
768px to 1279px
```

Behavior:

```text
- tab navigation may wrap or become scrollable;
- details drawer can overlay content;
- charts stack vertically;
- matrix uses horizontal internal scroll.
```

### 22.3 Mobile

Target:

```text
360px to 767px
```

Behavior:

```text
- header condenses metadata;
- tabs become horizontally scrollable;
- details drawer becomes bottom sheet;
- matrix shows key columns first and allows horizontal scroll;
- charts stack with controls above chart;
- no text overlap or clipped button labels.
```

Mobile is required to be usable for review, but dense scientific analysis is optimized for desktop.

## 23. Accessibility Requirements

```text
- All interactive controls are keyboard reachable.
- Focus states are visible.
- Text and meaningful non-text UI meet WCAG 2.2 AA contrast targets.
- Charts have adjacent data-table or summary equivalents.
- Color is not the only carrier of status.
- Warning and error icons include text labels.
- Form controls have accessible names.
- Tables use proper header associations.
- Dense tables expose row and column context to screen readers.
- Tooltip content is available through focus as well as hover.
- Motion is minimal and respects reduced-motion preferences.
- Playwright or accessibility tests cover tab navigation, details drawer behavior, and warning summaries.
```

## 24. Data Handling Requirements

### 24.1 Payload Loading

The dashboard reads:

```text
outputs/studies/<study_id>/dashboard_payload.json
```

or a local dev-server endpoint that serves the same payload.

### 24.2 Runtime Validation

On payload load:

```text
1. Validate payload schema.
2. If valid, render available sections.
3. If partially invalid, render diagnostics and block affected sections.
4. If invalid at top level, show payload error page.
```

### 24.3 No Scientific Recalculation

Client-side transforms allowed:

```text
- sorting
- filtering
- grouping for display
- chart coordinate transforms
- formatting numbers and units
```

Client-side transforms forbidden:

```text
- fitting models
- calculating theoretical yield
- calculating cost efficiency
- generating new recommendations
- classifying design-space probability
```

## 25. Number Formatting

Default formatting:

```text
- show 3 significant figures for modeled scientific outputs unless response config overrides.
- show more precision in details drawer when stored value has it.
- show units everywhere.
- use tabular numerals.
- do not round stored payload values.
```

Warnings:

```text
- If precision is limited or assay is semi-quantitative, display that near the value.
- dsRNA score must show score scale when available.
```

## 26. Browser Preview Requirements

The dashboard must work in:

```text
- Codex in-app browser local preview
- normal local browser
```

Preview assumptions:

```text
- no authentication required;
- served from 127.0.0.1 or file-backed preview;
- no reliance on existing browser cookies;
- no external network required for core rendering;
- payload path is local and workspace-relative.
```

## 27. Component Map

Launch component groups:

```text
AppShell
StudyHeader
GlobalWarningStrip
DashboardTabs
AvailabilityPanel
MetricTile
SourceBadge
UnitLabel
DetailsDrawer
ExperimentMatrix
TimeCoursePanel
ModelStatusStrip
ParetoEffectsChart
FactorResponsePanel
ContourPanel
RelativeYieldPanel
EconomicsPanel
RecommendationsTable
VerificationPlanTable
DiagnosticsPanel
PayloadFooter
```

Post-launch component groups:

```text
DesignSpaceProbabilityMap
ConstructComparisonPanel
CounterionInteractionPanel
VerificationResultsPanel
ScenarioComparisonPanel
SensitivityPanel
```

## 28. UX Acceptance Criteria

Launch UX is complete when:

```text
1. `/studies/:studyId` renders a valid dashboard payload.
2. Payload schema errors produce diagnostics instead of blank screen.
3. Overview, Matrix, Time Courses, Effects, Relative Yield, Economics, Recommendations, Verification, and Diagnostics tabs exist.
4. Unavailable sections explain missing inputs and producing tool.
5. Warnings are visible globally and within affected sections.
6. Matrix distinguishes planned, observed, derived, predicted, recommended, and verification values.
7. Time-course plots render when time-resolved data exists.
8. Effects tab shows model status before charts.
9. Relative yield tab shows formula provenance.
10. Economics tab shows unavailable state without treating missing costs as study failure.
11. Economics tab shows user-cost provenance when calculated.
12. Verification tab does not imply verification before observed comparison.
13. Diagnostics tab links displayed values to artifacts and hashes.
14. Dashboard is usable at desktop, tablet, and mobile widths.
15. Dashboard uses no external network dependencies for core rendering.
```

## 29. Visual QA Checklist

Before launch:

```text
- Verify desktop viewport at 1440x900.
- Verify tablet viewport at 1024x768.
- Verify mobile viewport at 390x844.
- Confirm no overlapping text.
- Confirm matrix headers remain readable.
- Confirm charts have stable dimensions.
- Confirm unavailable states are visually distinct from errors.
- Confirm warning strip appears for warning fixtures.
- Confirm cost charts are absent or unavailable when costs are missing.
- Confirm design-space probability map does not render fake zero-risk output.
- Confirm payload footer shows hash and versions.
```

## 30. Required UX Fixtures

Dashboard fixtures:

```text
empty_payload_state.json
phase0_design_only_payload.json
ivt_with_timecourses_payload.json
ivt_with_model_fit_payload.json
ivt_with_relative_yield_payload.json
ivt_economics_unavailable_payload.json
ivt_with_economics_payload.json
ivt_with_recommendations_payload.json
ivt_with_verification_plan_payload.json
ivt_with_payload_validation_error.json
ivt_with_blocking_warnings_payload.json
```

Fixture requirements:

```text
- Each fixture maps to a visible screenshot test.
- Each fixture includes known warnings and unavailable states.
- Economics fixtures use artificial user-provided prices.
- Validation-error fixture must not crash the app.
```

## 31. UX Copy Rules

Use direct scientific copy.

Preferred phrases:

```text
Cost efficiency was not calculated because direct component costs were not supplied.
Prediction intervals are unavailable for this model.
This value is derived from theoretical_yield.json.
This recommendation is model-predicted and not experimentally verified.
Design-space probability has not been calculated.
```

Avoid:

```text
No data, when the real issue is a missing optional input.
Optimized, when the condition is only recommended.
Verified, when no verification observations exist.
Savings, when baseline/cost/verification requirements are missing.
Significant, when statistical significance is unavailable.
```

## 32. Final UX Rule

The dashboard succeeds when it makes the scientific state hard to misread. A user should always be able to distinguish:

```text
- planned from observed;
- measured from derived;
- predicted from verified;
- available from unavailable;
- warning from error;
- model-based estimate from experimental evidence;
- optional economics from required analysis.
```
