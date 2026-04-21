# Workbench Redesign Migration Roadmap

Date: 2026-04-21
Status: Draft redesign direction

## 1. Purpose

This roadmap converts the workbench redesign into implementation phases. It is intended to sit above the current implementation roadmap until the redesign is accepted, then be folded into the canonical build contract and milestone plan.

## 2. Migration Strategy

Do not discard the existing architecture. The current architecture has the right scientific boundary:

```text
Codex orchestration
  -> MCP calculations
  -> schema-valid artifacts
  -> React rendering
```

The migration changes product shape and payload contracts:

```text
from:
  dashboard renders outputs from one requested workflow

to:
  workbench manages a structured study, candidate alternatives, comparison, commitment, explanations, and snapshots
```

## 3. Phase 0: Redesign Alignment

Goal:

```text
Decide which planning direction supersedes the current dashboard-first product language.
```

Tasks:

```text
1. Review this planning packet.
2. Decide whether "Experiment Strategy Studio" is the product metaphor.
3. Decide which current docs need amendments.
4. Mark existing dashboard-only requirements as launch implementation detail, not product north star.
5. Approve the candidate design comparison workspace as the highest-value redesign.
```

Deliverables:

```text
- accepted redesign packet
- list of canonical docs to update
- revised product principle: study object first
```

Exit criteria:

```text
- Product direction explicitly states that chat is a helper layer.
- Candidate design comparison is a launch or near-launch surface.
- The React app is renamed conceptually from dashboard to workbench, even if directory name remains apps/dashboard temporarily.
```

## 4. Phase 1: Workbench Payload Foundation

Goal:

```text
Add the minimum state model needed to render candidate design comparison.
```

Backend and schema tasks:

```text
1. Add recommendation_mode to study setup.
2. Add execution_constraints to factor/response setup.
3. Add candidate_design_set schema.
4. Add candidate_design schema with capabilities and diagnostics.
5. Add can_learn / cannot_learn structured section.
6. Add comparison schema.
7. Add stale_state schema.
8. Add contextual_ai_panel schema with source refs.
```

MCP tasks:

```text
1. Add or adapt generate_candidate_designs.
2. Add or adapt compare_candidate_designs.
3. Add ranking reason codes.
4. Emit candidate design cards and comparison payload sections.
5. Ensure all generated explanations cite structured diagnostics.
```

Frontend tasks:

```text
1. Add WorkbenchShell around current dashboard routes.
2. Add left study rail.
3. Add candidate design cards.
4. Add comparison table.
5. Add right AI advisor rail.
6. Add bottom drawer shell.
```

Exit criteria:

```text
- Fixture payload can show 3 candidate designs from one setup.
- Comparison view shows run count, estimability, curvature support, and warnings.
- AI advisor rail shows Why this design and Can/Cannot Learn from structured payload data.
```

## 5. Phase 2: Study Setup Editing and Regeneration Loop

Goal:

```text
Make the workbench feel like editing a study, not viewing static results.
```

Tasks:

```text
1. Build factor editor.
2. Build response goal editor.
3. Build constraint editor.
4. Build recommendation mode selector.
5. Build max run and execution constraint controls.
6. Add validation state display next to inputs.
7. Add regenerate candidates action path.
8. Add stale-state indicators when setup changes.
```

Implementation note:

```text
If the React app cannot call MCP tools directly at launch, regeneration can remain a Codex-mediated action. The UI should still model the action explicitly and show that Codex/MCP must refresh payload artifacts.
```

Exit criteria:

```text
- User can see which setup edits invalidate candidate designs.
- Workbench displays stale candidate sets until regenerated.
- Validation errors appear next to affected fields.
```

## 6. Phase 3: Commit-to-Run-Plan

Goal:

```text
Convert comparison decisions into executable, auditable run plans.
```

Tasks:

```text
1. Add commit_run_plan artifact.
2. Preserve selected candidate design ID.
3. Preserve run matrix, randomization, blocking, center points, and replicates.
4. Add protocol notes and export metadata.
5. Mark committed design distinctly from recommended design.
6. Add run-plan rationale generated from source diagnostics.
```

Exit criteria:

```text
- User can commit one candidate design.
- Run Plan surface shows a stable matrix and execution metadata.
- Commit event is written to audit log.
- Export preview references committed run plan, not an arbitrary latest design.
```

## 7. Phase 4: Snapshots and Design Versioning

Goal:

```text
Support realistic iterative reasoning across alternative assumptions.
```

Tasks:

```text
1. Add create_study_snapshot tool or artifact writer.
2. Add snapshot list in left rail.
3. Add snapshot diff payload.
4. Add compare snapshots view.
5. Add AI summary for differences between versions.
6. Add labels for screening, curvature, constrained custom, augmentation, and verification strategy snapshots.
```

Exit criteria:

```text
- User can preserve Version A, B, and C of a study.
- User can compare factor ranges, objectives, candidates, and committed plan across snapshots.
- AI explanation summarizes differences using snapshot diff data.
```

## 8. Phase 5: Sequential DOE Strategy

Goal:

```text
Represent augmentation pathways directly instead of treating each design as a one-shot answer.
```

Tasks:

```text
1. Add sequential_strategy section to candidate designs.
2. Represent screening -> response surface -> optimize -> confirm paths.
3. Add locked rows and augmentation candidates.
4. Distinguish model-building, augmentation, and verification runs.
5. Add next-step recommendation modes for post-observation workflows.
```

Exit criteria:

```text
- A screening design can show a proposed augmentation path.
- Run plan can mark locked existing rows and new candidate rows.
- Explanation panel states what the augmentation is intended to improve.
```

## 9. Phase 6: Rename and Product Polish

Goal:

```text
Align language, docs, and UI with the study-workbench product direction.
```

Tasks:

```text
1. Update product docs from dashboard review language to workbench language.
2. Decide whether apps/dashboard should remain technical directory name or be renamed later.
3. Update skill instructions to make study-object-first behavior explicit.
4. Update README and packaging docs.
5. Add visual QA for left rail, right rail, comparison table, and bottom drawer.
6. Add screenshots or fixtures for workbench states.
```

Exit criteria:

```text
- Product docs, skill docs, schemas, and dashboard/workbench fixtures use consistent terminology.
- User-facing product no longer reads as chat plus separate visualization.
```

## 10. Backlog Items

| ID | Item | Phase |
|---|---|---|
| WB-001 | Add recommendation mode schema | Phase 1 |
| WB-002 | Add candidate design set schema | Phase 1 |
| WB-003 | Add candidate design capabilities schema | Phase 1 |
| WB-004 | Add can learn / cannot learn schema | Phase 1 |
| WB-005 | Add design comparison schema | Phase 1 |
| WB-006 | Add contextual AI panel schema | Phase 1 |
| WB-007 | Render candidate design cards | Phase 1 |
| WB-008 | Render design comparison table | Phase 1 |
| WB-009 | Render right advisor rail | Phase 1 |
| WB-010 | Render bottom drawer shell | Phase 1 |
| WB-011 | Build structured setup editors | Phase 2 |
| WB-012 | Add stale-state tracking | Phase 2 |
| WB-013 | Add commit run plan artifact | Phase 3 |
| WB-014 | Add run plan UI | Phase 3 |
| WB-015 | Add study snapshots | Phase 4 |
| WB-016 | Add snapshot diff | Phase 4 |
| WB-017 | Add sequential augmentation path | Phase 5 |
| WB-018 | Update canonical docs and skill language | Phase 6 |

## 11. Validation Gates

### Workbench Gate 0: Static Planning Fixtures

```text
- candidate design fixture exists
- comparison fixture exists
- contextual AI fixture exists
- stale-state fixture exists
- workbench route renders fixtures
```

### Workbench Gate 1: Candidate Comparison Workflow

```text
- setup validates
- at least 3 candidates are generated
- comparison ranks candidates
- can/cannot learn panel is populated
- warnings are visible
- recommendation rationale cites source diagnostics
```

### Workbench Gate 2: Commit Workflow

```text
- selected candidate can be committed
- run plan artifact is persisted
- run matrix is exportable
- audit event records commit
- committed design remains stable after unrelated UI selection changes
```

### Workbench Gate 3: Iteration Workflow

```text
- snapshots can be created
- snapshots can be diffed
- stale state is visible after setup edits
- augmentation path can be shown after observed data exists
```

## 12. Required Canonical Doc Updates After Approval

If this redesign is accepted, update:

```text
Product Requirements Document.md
  Add study-object-first product goals and candidate comparison requirements.

Dashboard UX Spec.md
  Reframe as Workbench UX Spec or add workbench layer above dashboard tabs.

MCP Tool API Spec.md
  Add candidate generation, comparison, commit, snapshot, and explanation contracts.

Data & Schema Contract.md
  Add schemas for candidate design sets, comparisons, snapshots, stale states, and contextual AI panels.

Implementation Roadmap.md
  Insert workbench phases before or alongside current dashboard launch surface.

Canonical Build Contract.md
  Update only after the redesign direction is accepted.
```

## 13. Migration Rule

Every migration step must preserve the current scientific guarantee:

```text
No numerical DOE, modeling, optimization, power, cost, or diagnostic result may come from AI prose. Computed claims must trace to MCP tools and persisted artifacts.
```

