# Workbench Redesign Execution Plan

Date: 2026-04-21
Status: Draft build execution plan

## 1. Purpose

This document defines the execution plan for updating the DOE Scientific Toolchain from a chat-plus-dashboard workflow into a study-object-first workbench with candidate design comparison, contextual AI explanation, explicit run-plan commitment, and study snapshots.

The plan is intentionally implementation-oriented. It identifies workstreams, phases, repo areas, dependencies, acceptance gates, fixtures, tests, and sequencing rules.

## 2. Execution Goal

Build the redesigned product shape in controlled slices:

```text
Validated study setup
  -> generated candidate designs
  -> side-by-side comparison
  -> contextual AI explanation
  -> committed run plan
  -> snapshots and sequential augmentation
```

The first usable milestone is not full scientific breadth. It is a fixture-backed and then MCP-backed workbench where a user can compare candidate DOE strategies without relying on chat as the inspection surface.

## 3. Non-Negotiable Constraints

1. MCP tools remain the numerical source of truth.
2. React may render, sort, filter, and select, but must not compute scientific results.
3. AI explanations must cite source objects, diagnostics, warnings, and artifacts.
4. Chat cannot be the only way to inspect run count, estimability, warnings, or recommendation rationale.
5. Missing or unsupported capabilities must render as unavailable states, not blank UI.
6. Existing project behavior should not be broken while the workbench is introduced.
7. The current `apps/dashboard` directory may remain until a rename is justified; user-facing language should move toward "workbench."

## 4. Target Architecture

Target build shape:

```text
Codex plugin and skill
  -> MCP tools and artifact writers
  -> workbench payload builder
  -> React workbench shell
  -> candidate comparison and run-plan panels
  -> contextual AI advisor panels
```

New product layers:

```text
Study setup layer:
  factors, responses, constraints, objective, execution limits

Candidate layer:
  multiple generated candidate designs with diagnostics and capabilities

Comparison layer:
  selected candidates, visible tradeoffs, ranking, recommendation rationale

Commit layer:
  selected candidate becomes a stable executable run plan

Version layer:
  snapshots, stale state, diffs, augmentation path

AI layer:
  scoped explanations tied to selected study objects
```

## 5. Workstreams

### 5.1 Product and Canonical Docs

Repo areas:

```text
Canonical Build Contract.md
Product Requirements Document.md
Dashboard UX Spec.md
Implementation Roadmap.md
MCP Tool API Spec.md
Data & Schema Contract.md
plugins/doe-scientific-toolchain/skills/scientific-study-designer/SKILL.md
```

Responsibilities:

```text
- make the study-object-first direction canonical
- define workbench terminology
- preserve deterministic computation boundaries
- update launch scope and validation gates
- convert dashboard-first language to workbench-first language
```

### 5.2 Data Contracts and Fixtures

Repo areas:

```text
schemas/
fixtures/dashboard/
fixtures/studies/
scripts/validate_schemas.py
```

Responsibilities:

```text
- add schemas for candidate designs, comparisons, snapshots, stale states, and contextual AI panels
- create fixture payloads before frontend implementation
- ensure schema validation catches missing source refs and invalid states
```

### 5.3 MCP Backend and Payload Builder

Repo areas:

```text
mcp-server/src/doe_toolchain/server.py
mcp-server/src/doe_toolchain/tools/
mcp-server/src/doe_toolchain/science/
mcp-server/src/doe_toolchain/artifacts/
mcp-server/src/doe_toolchain/validation/
mcp-server/tests/
```

Responsibilities:

```text
- generate candidate design sets
- rank and compare candidates
- emit can learn / cannot learn diagnostics
- commit selected design into a run plan artifact
- create and diff snapshots
- produce workbench payload sections
```

### 5.4 React Workbench

Repo areas:

```text
apps/dashboard/src/
apps/dashboard/src/App.tsx
apps/dashboard/src/payload.ts
apps/dashboard/src/payload.test.ts
apps/dashboard/src/styles.css
```

Responsibilities:

```text
- introduce WorkbenchShell while preserving current payload rendering
- render candidate cards and comparison table
- render right AI advisor rail
- render bottom drawer
- render stale state and unavailable states
- render committed run plan and snapshots
```

### 5.5 Validation and QA

Repo areas:

```text
Validation & Test Plan.md
validation-reports/
mcp-server/tests/
apps/dashboard/src/*.test.*
scripts/
```

Responsibilities:

```text
- add workbench gates
- add schema tests
- add payload tests
- add UI render tests
- add end-to-end workflow tests after backend tools exist
```

## 6. Phase Plan

### Phase 0: Baseline and Scope Lock

Goal:

```text
Lock the redesign direction and identify conflicts with current canonical docs.
```

Tasks:

```text
1. Review the workbench-redesign planning packet.
2. Decide which current docs are amended rather than replaced.
3. Create a short conflict matrix for current dashboard-first requirements.
4. Confirm that `apps/dashboard` remains the technical directory for now.
5. Confirm candidate comparison as the first build milestone.
```

Deliverables:

```text
- accepted redesign packet
- doc update list
- first milestone definition
```

Acceptance criteria:

```text
- stakeholders agree that the study is the primary object
- chat is explicitly a helper layer
- candidate design comparison is a required workbench surface
```

### Phase 1: Canonical Planning Update

Goal:

```text
Make the workbench model the official project direction.
```

Tasks:

```text
1. Update Product Requirements Document.md with workbench-first goals.
2. Update Dashboard UX Spec.md into a workbench UX layer or rename conceptually in text.
3. Update Canonical Build Contract.md with workbench payload and candidate comparison scope.
4. Update MCP Tool API Spec.md with candidate, comparison, commit, snapshot, and explanation contracts.
5. Update Implementation Roadmap.md with the workbench phases.
6. Update the skill to emphasize study-object-first behavior and contextual explanation.
```

Acceptance criteria:

```text
- canonical docs no longer describe dashboard review as the main product shape
- launch scope includes candidate design comparison or an explicit near-launch milestone
- deterministic calculation guardrails remain intact
```

### Phase 2: Schema and Fixture Foundation

Goal:

```text
Define workbench state before writing frontend or backend behavior.
```

New schema candidates:

```text
schemas/workbench_payload.schema.json
schemas/candidate_design_set.schema.json
schemas/candidate_design.schema.json
schemas/design_comparison.schema.json
schemas/run_plan_commit.schema.json
schemas/study_snapshot.schema.json
schemas/stale_state.schema.json
schemas/contextual_ai_panel.schema.json
schemas/learnability_summary.schema.json
```

Fixture payloads:

```text
fixtures/dashboard/workbench_empty_payload.json
fixtures/dashboard/workbench_validated_setup_payload.json
fixtures/dashboard/workbench_candidate_designs_payload.json
fixtures/dashboard/workbench_comparison_payload.json
fixtures/dashboard/workbench_stale_candidates_payload.json
fixtures/dashboard/workbench_committed_run_plan_payload.json
fixtures/dashboard/workbench_snapshot_diff_payload.json
fixtures/dashboard/workbench_contextual_ai_payload.json
```

Tasks:

```text
1. Add schemas with source artifact references as required where applicable.
2. Add fixture payloads that cover all main UI states.
3. Extend schema validation script to include new fixtures.
4. Add tests that invalid explanation panels fail when source refs are missing.
5. Add tests that stale candidate state is represented explicitly.
```

Acceptance criteria:

```text
- all workbench fixtures validate
- invalid source refs fail validation
- fixture set can drive frontend work without live MCP tools
```

### Phase 3: Static Workbench Shell

Goal:

```text
Prove the new product shape in React using fixtures.
```

Components:

```text
WorkbenchShell
StudyRail
StudyStageStatus
CandidateDesignGrid
CandidateDesignCard
DesignComparisonTable
AIAdvisorRail
WhyThisDesignCard
LearnCannotLearnPanel
StudyBottomDrawer
ArtifactSourcePanel
AvailabilityPanel
```

Tasks:

```text
1. Extend payload types to understand workbench sections.
2. Add a top-level WorkbenchShell layout.
3. Render the left study rail with stage status.
4. Render candidate design cards from fixture data.
5. Render side-by-side comparison table.
6. Render AI advisor rail with rationale and warning explanations.
7. Render bottom drawer with diagnostics and artifact refs.
8. Preserve current dashboard states until replacement is complete.
```

Acceptance criteria:

```text
- workbench candidate fixture renders without runtime errors
- user can see 3 candidate designs and their statuses
- comparison table shows run count, learnability, interaction support, curvature support, and warnings
- right rail shows Why this design and Can/Cannot Learn
- unavailable and stale states are visible
```

Validation:

```text
npm test -- --run
npm run build
```

### Phase 4: Candidate Design Backend Contracts

Goal:

```text
Make candidate design generation and comparison explicit MCP-backed artifacts.
```

Tool options:

```text
generate_candidate_designs
rank_candidate_designs
compare_candidate_designs
```

Implementation strategy:

```text
1. Start as orchestration tools over existing `design_doe` and `design_optimal_doe`.
2. Persist candidate design set metadata separately from individual design matrices.
3. Emit capability flags and diagnostics from design metadata.
4. Emit ranking reason codes and tradeoff summaries.
5. Generate workbench payload sections from persisted artifacts.
```

Artifacts:

```text
outputs/studies/<study_id>/candidate_design_sets/<set_id>/candidate_design_set.json
outputs/studies/<study_id>/candidate_design_sets/<set_id>/candidate_rankings.json
outputs/studies/<study_id>/comparisons/<comparison_id>/design_comparison.json
```

Acceptance criteria:

```text
- one setup can generate at least 3 candidates where feasible
- infeasible and unsupported candidates are represented, not omitted
- rankings include reason codes and source diagnostics
- comparison artifact is schema-valid
- audit log records each candidate/comparison tool call
```

Validation:

```text
pytest mcp-server/tests
python scripts/validate_schemas.py
```

### Phase 5: Workbench Payload Builder

Goal:

```text
Bridge backend artifacts into the React workbench.
```

Tasks:

```text
1. Extend `generate_dashboard_payload` or add `generate_workbench_payload`.
2. Include setup state, candidates, comparison, AI panels, stale state, and source refs.
3. Preserve compatibility with existing dashboard payloads during migration.
4. Add payload tests for no candidates, valid candidates, stale candidates, and committed plan.
5. Add strict unavailable states for unsupported design families.
```

Acceptance criteria:

```text
- generated workbench payload validates
- React can render generated payloads and fixture payloads
- stale state appears after upstream setup hash changes
- existing dashboard payload tests still pass or are intentionally migrated
```

### Phase 6: Setup Editing and Regeneration Path

Goal:

```text
Let the user experience the product as editing a study object.
```

Components:

```text
SetupForm
FactorEditor
ResponseGoalEditor
ConstraintEditor
ObjectiveSelector
ExecutionConstraintEditor
```

Tasks:

```text
1. Render structured setup from payload.
2. Add editable UI controls where local editing is supported.
3. Add dirty and stale state indicators.
4. Add regeneration call-to-action that clearly routes through Codex/MCP when direct tool calls are not available.
5. Show validation errors next to fields.
```

Acceptance criteria:

```text
- user can identify which setup fields drive candidate generation
- stale candidate state is visible after setup edits
- unsupported direct recomputation is not faked in the browser
- validation issues are object-specific, not only global
```

### Phase 7: Commit-to-Run-Plan

Goal:

```text
Convert selected candidate designs into stable executable run plans.
```

Tool:

```text
commit_run_plan
```

Artifacts:

```text
outputs/studies/<study_id>/run_plans/<run_plan_id>/run_plan.json
outputs/studies/<study_id>/run_plans/<run_plan_id>/run_matrix.csv
outputs/studies/<study_id>/run_plans/<run_plan_id>/protocol_notes.md
```

Tasks:

```text
1. Define run plan commit schema.
2. Add commit tool contract and implementation.
3. Persist selected candidate ID and source comparison ID.
4. Preserve randomization, blocking, center points, replicates, and fixed conditions.
5. Render committed run plan panel.
6. Add export preview and artifact refs.
```

Acceptance criteria:

```text
- committed plan remains stable after candidate selection changes
- run plan references source candidate and comparison artifacts
- audit event records commit
- UI distinguishes recommended, selected, and committed designs
```

### Phase 8: Contextual AI Actions

Goal:

```text
Make explanations object-bound and source-cited.
```

Tool or payload capability:

```text
explain_study_object
```

Scoped actions:

```text
Explain selected design
Explain this warning
Compare selected candidates
Suggest how to reduce runs
Suggest how to support curvature
Draft run-plan rationale
Summarize changes since snapshot
```

Tasks:

```text
1. Add explanation request/response schema.
2. Add object refs for explanation context.
3. Add source refs and diagnostic refs as required fields.
4. Render explanation cards in AIAdvisorRail.
5. Add tests that explanation cards cannot validate without source refs.
```

Acceptance criteria:

```text
- every AI explanation names the object it explains
- every numerical claim in an explanation traces to diagnostics or artifact refs
- warning explanations include impact and fix guidance
```

### Phase 9: Snapshots and Diffs

Goal:

```text
Support real design iteration across changing assumptions.
```

Tools:

```text
create_study_snapshot
diff_study_snapshots
```

Artifacts:

```text
outputs/studies/<study_id>/snapshots/<snapshot_id>/snapshot.json
outputs/studies/<study_id>/snapshots/<diff_id>/snapshot_diff.json
```

Tasks:

```text
1. Persist setup hash, candidate set ID, comparison ID, and committed run plan ID.
2. Add snapshot list to StudyRail.
3. Add snapshot diff view.
4. Add AI summary of snapshot differences from structured diff data.
```

Acceptance criteria:

```text
- Version A, B, and C can be represented
- diffs show factor, response, constraint, objective, and design changes
- stale state references snapshots where relevant
```

### Phase 10: Sequential DOE and Augmentation

Goal:

```text
Represent realistic staged DOE workflows directly.
```

Tasks:

```text
1. Add sequential_strategy to candidate design metadata.
2. Represent screening -> response surface -> optimization -> confirmation paths.
3. Add locked-row metadata to run plans and augmentation candidates.
4. Add augmentation candidate UI.
5. Distinguish model-building, augmentation, verification, and confirmation rows.
```

Acceptance criteria:

```text
- screening candidates can show follow-up augmentation paths
- augmentation candidates can preserve locked prior runs
- explanations state what the next stage improves and what remains unlearned
```

### Phase 11: Hardening, Visual QA, and Release Candidate

Goal:

```text
Make the workbench slice reliable enough to become the default project direction.
```

Tasks:

```text
1. Run schema validation for all fixtures.
2. Run backend tests.
3. Run frontend tests and build.
4. Add browser smoke tests for desktop, tablet, and mobile.
5. Add no-candidate, infeasible-candidate, stale, committed-plan, and snapshot-diff regression tests.
6. Update setup and packaging docs.
7. Produce validation report.
```

Acceptance criteria:

```text
- no critical render errors
- no invalid generated workbench payloads
- no explanation panel without source refs
- no unsupported capability rendered as successful
- no client-side scientific calculation introduced
```

## 7. First Build Milestone

Name:

```text
Workbench Candidate Comparison Slice
```

Scope:

```text
- workbench payload schema
- candidate design set schema
- comparison schema
- contextual AI panel schema
- fixture-backed React workbench shell
- candidate cards
- comparison table
- right advisor rail
- bottom drawer with source refs
```

Out of scope:

```text
- direct in-browser MCP calls
- full setup editing
- committed run plans
- snapshots
- live optimization
- paper-class DOE augmentation
```

Acceptance criteria:

```text
1. A fixture can show three candidate designs.
2. Each candidate shows run count, design family, status, capabilities, tradeoffs, and warnings.
3. Compare view shows can learn / cannot learn and design tradeoffs.
4. Right rail explains why one design is recommended.
5. All explanation cards cite source refs.
6. Existing dashboard tests still pass or are intentionally updated.
```

## 8. Suggested Implementation Order by Pull Request

PR 1:

```text
Canonical docs and skill language update
```

PR 2:

```text
Workbench schemas and validation fixtures
```

PR 3:

```text
Fixture-backed WorkbenchShell, StudyRail, CandidateDesignCard, and AIAdvisorRail
```

PR 4:

```text
DesignComparisonTable, LearnCannotLearnPanel, stale state, and bottom drawer
```

PR 5:

```text
MCP candidate design set and comparison artifacts
```

PR 6:

```text
Workbench payload builder integration
```

PR 7:

```text
Setup editing and regeneration state
```

PR 8:

```text
Commit run plan
```

PR 9:

```text
Snapshots and snapshot diffs
```

PR 10:

```text
Sequential augmentation model
```

PR 11:

```text
Workbench validation report and release hardening
```

## 9. Testing Strategy

### 9.1 Schema Tests

Required checks:

```text
- valid workbench fixtures pass
- invalid missing source refs fail
- invalid candidate statuses fail
- stale states require reason codes
- committed run plans require source candidate refs
```

### 9.2 Backend Tests

Required checks:

```text
- candidate generation writes candidate set artifact
- unsupported candidate design is represented with unavailable reason
- comparison ranking is deterministic with fixed seed
- commit_run_plan writes stable run plan artifacts
- snapshots preserve setup and comparison hashes
- audit log entries are written for all new tools
```

### 9.3 Frontend Tests

Required checks:

```text
- workbench fixture renders
- candidate cards show correct statuses
- comparison table shows key capabilities
- right rail shows source-cited explanations
- stale state is visible
- unavailable state is visible
- committed run plan is distinct from selected design
```

### 9.4 Browser QA

Viewports:

```text
1440x900
1024x768
390x844
```

Checks:

```text
- no overlapping text
- candidate cards remain scannable
- comparison table scrolls internally when needed
- right rail collapses or drawers correctly on narrow viewports
- bottom drawer does not hide primary actions
- warnings remain visible
```

## 10. Quality Gates

Workbench Gate 0:

```text
- schemas and fixtures exist
- validation script covers workbench fixtures
- static workbench route renders fixture payload
```

Workbench Gate 1:

```text
- candidate comparison UI is complete
- right rail explanation is source-cited
- stale and unavailable states render
```

Workbench Gate 2:

```text
- MCP candidate and comparison tools produce schema-valid artifacts
- generated payload renders in React
- audit log coverage exists
```

Workbench Gate 3:

```text
- committed run plan artifact exists
- committed plan renders distinctly
- export preview is traceable to committed plan
```

Workbench Gate 4:

```text
- snapshots and diffs exist
- sequential augmentation model is visible
- validation report records pass/fail status
```

## 11. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Workbench becomes a static dashboard | Users still rely on chat for decisions | Prioritize candidate comparison and commit workflow before advanced charts. |
| New schemas are too broad | Slow implementation and unclear contracts | Start with fixture-backed minimal schemas and expand only when a UI or tool needs fields. |
| AI explanations invent facts | Scientific trust failure | Require source refs and diagnostic refs in explanation schema. |
| Existing dashboard breaks | Regression in current plugin preview | Preserve current payload support until replacement is complete. |
| Direct recomputation from React is tempting | Scientific boundary violation | Keep React display-only; trigger recomputation through Codex/MCP flow. |
| Candidate generation gets over-scoped | Delays first milestone | Start by wrapping existing `design_doe` and `design_optimal_doe` outputs. |
| Terminology drifts between docs and UI | Confusing implementation | Treat "workbench" terminology update as Phase 1 acceptance criterion. |

## 12. Definition of Done

A workbench feature is done when:

```text
- schema exists
- valid and invalid fixtures exist
- MCP artifact or fixture source exists
- React renders loading, unavailable, warning, and valid states
- tests cover schema and rendering
- source refs are visible for scientific claims
- audit behavior is defined for generated artifacts
- docs explain the user-facing behavior
```

A scientific workbench feature is done when:

```text
- numerical output comes from MCP tools
- method and package versions are captured where applicable
- warnings are machine-readable
- generated payload references source artifacts
- UI does not overstate computed support
```

## 13. Immediate Next Actions

Recommended next sequence:

```text
1. Update canonical docs to accept the workbench direction.
2. Add workbench schemas and fixtures.
3. Build fixture-backed WorkbenchShell and CandidateDesignGrid.
4. Add DesignComparisonTable and AIAdvisorRail.
5. Implement candidate/comparison MCP artifacts.
6. Integrate generated workbench payloads.
```

The best first implementation target is still the same:

```text
A fixture-backed workbench showing Study Setup, three candidate design cards, a comparison table, and a right-rail Why this design explanation.
```

