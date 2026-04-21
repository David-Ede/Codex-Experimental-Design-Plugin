# Workspace Information Architecture

Date: 2026-04-21
Status: Draft redesign direction

## 1. Purpose

This document defines the information architecture for the redesigned DOE workbench. The goal is to replace a chat-first flow with a structured workspace where study setup, candidate design comparison, run planning, diagnostics, and AI explanation are all connected to the same study state.

## 2. Global Layout

Recommended desktop layout:

```text
left rail      center workspace            right rail
study map  |  active study panel       |   AI advisor
navigation |  forms, tables, charts    |   warnings
versions   |  comparison, run matrix   |   explanations

bottom drawer:
run matrix, diagnostics, export, audit trail, source artifacts
```

### 2.1 Left Rail

Purpose:

```text
- study navigation
- study maturity status
- version and snapshot list
- workflow stage markers
- primary object selection
```

Contents:

```text
- Study Setup
- Candidate Designs
- Compare
- Run Plan
- Learn / Explain
- Diagnostics
- Snapshots
```

Status indicators:

```text
not_started
needs_input
computed_with_warnings
ready
committed
blocked
unavailable
```

### 2.2 Center Workspace

The center panel is the primary work area. It changes mode based on the selected workflow stage.

Center modes:

```text
- setup form
- candidate design cards
- comparison table
- factor-space visualization
- run matrix
- optimization view
- diagnostics and audit view
```

### 2.3 Right Rail

The right rail is not generic chat. It is a contextual advisor bound to the selected object.

Right rail modules:

```text
- Why this design?
- What you can learn / cannot learn
- Warnings
- Recommendation rationale
- Explain selected chart
- Suggested next edit
- Artifact source
```

The rail can include a compact question input, but the default state should be generated explanations and warnings, not an empty chat box.

### 2.4 Bottom Drawer

The bottom drawer supports dense inspection without losing the active workspace.

Drawer modes:

```text
- run matrix
- design diagnostics
- source artifacts
- export preview
- audit trail
- selected-row details
```

## 3. Main Workbench Surfaces

### 3.1 Study Setup

Purpose:

```text
Capture the problem structure before design generation.
```

Required sections:

```text
- problem statement
- recommendation mode
- response goals
- factors and ranges
- categorical levels
- fixed conditions
- constraints
- budget and max runs
- expected noise or replicate policy
- hard-to-change factors
- batch, day, or material limits
```

Key interactions:

```text
- add factor
- mark factor fixed
- add forbidden combination
- set response goal
- set max run count
- set execution constraints
- validate setup
```

Inline AI behavior:

```text
- translate vague goals into candidate response goals
- flag insufficient factor ranges
- explain why a constraint changes feasible design families
- suggest missing response metadata
```

Acceptance criteria:

```text
- User can define all launch factor and response metadata without chat.
- Validation warnings appear next to affected fields.
- The setup panel shows whether candidate design generation is ready.
```

### 3.2 Candidate Designs

Purpose:

```text
Generate and inspect multiple feasible design families.
```

Candidate families:

```text
- full factorial
- fractional factorial
- Plackett-Burman
- Box-Behnken
- central composite
- D-optimal / custom
- Latin hypercube
- Bayesian or sequential candidate, when supported
```

Card fields:

```text
- design family
- recommendation status
- run count
- supported effect types
- curvature support
- interaction support
- blocking/randomization support
- center points and replicates
- robustness to missing runs
- feasibility against constraints
- best use case
- tradeoff
- watch out for
```

Card states:

```text
recommended
available
available_with_warnings
not_recommended
infeasible
unsupported
not_computed
```

Acceptance criteria:

```text
- User can compare feasible families before committing a design.
- Infeasible designs explain why they are infeasible.
- Unsupported designs do not look like failures when the method is out of scope.
```

### 3.3 Compare

Purpose:

```text
Enable side-by-side decision-making across 2 to 4 selected candidate designs.
```

Comparison columns:

```text
- run count
- factor count
- response goals supported
- main effects estimable
- two-factor interactions estimable
- curvature estimable
- alias/confounding risk
- pure error support
- missing-run sensitivity
- hard-to-change factor handling
- blocking support
- randomization support
- expected interpretability
- execution burden
- best use case
```

Views:

```text
- comparison table
- factor-space coverage map
- estimability matrix
- run-count vs learning-value plot
- warning comparison
- AI recommendation summary
```

Acceptance criteria:

```text
- The selected recommendation can be justified from visible evidence.
- The comparison exposes what each design cannot learn.
- The user can commit a selected design from this surface.
```

### 3.4 Run Plan

Purpose:

```text
Convert a selected candidate design into an executable experiment plan.
```

Required sections:

```text
- committed design summary
- run matrix
- randomization order
- blocking
- replication
- center points
- fixed conditions
- forbidden combination checks
- protocol notes
- export package
```

Run matrix indicators:

```text
planned
center_point
replicate
blocked
hard_to_change_group
verification
augmentation
```

Acceptance criteria:

```text
- User can distinguish selected candidate from committed run plan.
- Run plan includes enough execution metadata for lab use.
- Export does not imply scientific validation.
```

### 3.5 Learn / Explain

Purpose:

```text
Provide contextual scientific explanation, warnings, and next-step advice.
```

Required sections:

```text
- Why this design?
- What you can learn
- What you cannot learn
- What could go wrong
- What to run next after results
- How to augment this design
- Source artifacts
```

Acceptance criteria:

```text
- Explanations cite the selected design, diagnostic, warning, or artifact.
- The user can open deeper explanations without leaving the current study object.
- AI copy distinguishes computed diagnostics from advisory interpretation.
```

## 4. Screen-by-Screen Flow

### 4.1 New Study Flow

```text
1. User opens empty workbench.
2. Study Setup asks for objective, factors, responses, constraints, and max runs.
3. Validate Setup runs MCP validation.
4. Candidate Designs shows feasible families.
5. Compare opens with recommended candidates preselected.
6. User commits one candidate.
7. Run Plan shows randomized matrix and export.
8. Learn / Explain summarizes rationale and next-step strategy.
```

### 4.2 Assumption Change Flow

```text
1. User changes a factor range, max runs, or recommendation mode.
2. A stale-state indicator appears on affected candidate designs.
3. User regenerates candidates.
4. Compare shows changed diagnostics.
5. Right rail explains what changed.
6. User snapshots the new version or commits it.
```

### 4.3 Sequential Augmentation Flow

```text
1. User imports observed data.
2. Model diagnostics become available.
3. Recommendation mode changes to augment / optimize / confirm.
4. Candidate Designs proposes augmentation options.
5. Compare shows original vs augmented strategy.
6. Run Plan marks locked rows and new rows.
7. Learn / Explain states what the augmentation is intended to improve.
```

## 5. Responsive Behavior

Desktop:

```text
- persistent left rail
- center workspace
- persistent right rail
- bottom drawer
```

Tablet:

```text
- collapsible left rail
- center workspace
- right rail as drawer
- bottom drawer remains available
```

Mobile:

```text
- top segmented workflow navigation
- single active panel
- AI advisor and diagnostics as bottom sheets
- run matrix optimized for review, not heavy editing
```

## 6. Component Inventory

New or revised components:

```text
WorkbenchShell
StudyRail
StudyStageStatus
SnapshotList
SetupForm
FactorEditor
ResponseGoalEditor
ConstraintEditor
ObjectiveSelector
CandidateDesignGrid
CandidateDesignCard
DesignCapabilityMatrix
DesignComparisonTable
EstimabilityMatrix
FactorSpaceMap
RunCountLearningPlot
RunPlanMatrix
CommitDesignPanel
AIAdvisorRail
WhyThisDesignCard
LearnCannotLearnPanel
WarningReasonPanel
ExplainThisButton
StudyBottomDrawer
ArtifactSourcePanel
```

## 7. UX Rules

1. Do not make the user ask for facts the workspace already knows.
2. Put warnings next to the affected study object and in global summary.
3. Show unavailable states as scientific state, not empty UI.
4. Make the selected design, recommended design, and committed design visually distinct.
5. Keep AI explanations close to the object they explain.
6. Use tables for dense comparisons and cards only for repeated candidate summaries.
7. Do not imply a design is verified until observed verification results exist.

