# Product Redesign Brief: Experiment Strategy Studio

Date: 2026-04-21
Status: Draft redesign direction

## 1. Summary

The DOE Scientific Toolchain should be redesigned as an experiment strategy studio: a structured, visual, stateful workbench for designing, comparing, explaining, and committing experimental designs.

The current plugin direction correctly separates scientific computation from natural-language explanation. The missing product shift is that the user should not experience the product as "chat plus charts." The primary experience should be editing and inspecting a study object.

Target product shape:

```text
Structured study state
  -> candidate design generation
  -> visual and quantitative comparison
  -> contextual explanation
  -> committed run plan
  -> auditable artifacts
```

## 2. Problem

DOE work is not primarily a question-answer interaction. It is an iterative decision process in which the user defines assumptions, compares alternatives, inspects tradeoffs, changes constraints, and commits a defensible experimental plan.

A chat-first interface creates three product problems:

1. The user must ask for facts that should be visible.
2. The AI feels detached from the scientific object being edited.
3. Visualizations feel like output destinations rather than native parts of the workflow.

The redesign solves this by making the experiment design itself the main object.

## 3. Product North Star

A scientist should be able to open one workbench and answer:

```text
- What am I trying to learn?
- Which factors, ranges, responses, and constraints define the study?
- Which candidate designs are feasible?
- What can each candidate design estimate?
- What can each candidate design not estimate?
- What are the run-count, cost, robustness, and interpretability tradeoffs?
- Why is one design recommended?
- What happens when I change a factor range, objective, or constraint?
- Which run plan am I committing to execute?
```

The AI should be visible where it helps:

```text
- explaining a specific design choice
- critiquing a weak study setup
- translating intent into design criteria
- recommending next experimental steps
- warning about overfitting, confounding, insufficient runs, or missing pure error
```

## 4. Product Principles

### 4.1 Study Object First

The study is the durable object. Conversation is a control and explanation layer around it.

The workbench should expose:

```text
- objective
- responses
- factors
- ranges and constraints
- fixed conditions
- candidate design families
- generated run matrices
- diagnostics
- recommendations
- committed run plans
- study versions and snapshots
```

### 4.2 Computed State Must Be Inspectable

Users should not need to ask the model:

```text
- what interactions are estimable
- how many runs are required for curvature
- why one design is better
- what changed after editing a factor range
- whether economics is available
- whether a design is underpowered
```

These answers should be visible in structured UI, with AI available for deeper explanation.

### 4.3 AI Is Advisor, Not Interface

AI should act as:

```text
- interpreter of vague goals
- advisor on design choices
- critic of weak setups
- explainer of diagnostics
- guide for sequential augmentation
```

AI should not be:

```text
- the only way to construct a design
- the only way to inspect a matrix or diagnostic
- the source of numerical calculations
- the hidden decision-maker behind recommendations
```

### 4.4 Visualizations Are Native Workflow Panels

Visualizations must be bound to study state. When the user changes ranges, constraints, objective mode, design family, or selected candidate, related views should update from regenerated payloads.

Core visual views:

```text
- design matrix table
- factor space map
- alias/confounding view
- power or precision tradeoff view
- response surface preview
- Pareto or effect ranking
- desirability and optimization panel
- scenario compare view
```

### 4.5 Recommendation Modes Beat Generic Chat

The user should choose a declared intent such as:

```text
- Minimize runs
- Screen important factors
- Estimate interactions
- Fit curvature
- Optimize response
- Respect material/time constraints
- Prepare for scale-up robustness
```

The tool can then rank designs against an explicit objective, explain the tradeoff, and expose what is not learnable.

### 4.6 Sequential DOE Is First-Class

Many DOE workflows are not one design. The workbench should represent staged strategies:

```text
screening -> augmentation -> response surface -> optimization -> confirmation
```

The product should show how a first-pass design can be augmented later instead of implying one design solves every goal.

## 5. Primary User Jobs

### 5.1 Setup

As a scientist, I need to define factors, ranges, response goals, known constraints, fixed conditions, and expected noise so the system can propose feasible designs.

### 5.2 Compare

As a scientist, I need to compare candidate designs side by side so I can choose based on learning value, run count, interpretability, and execution constraints.

### 5.3 Understand

As a scientist, I need to see what each design can and cannot estimate so I do not overclaim interactions, curvature, or optimization quality.

### 5.4 Modify

As a scientist, I need to change assumptions and immediately see affected designs, warnings, and diagnostics.

### 5.5 Commit

As a scientist, I need to commit one candidate design into an executable run plan with randomization, blocking, replication, center points, and exportable protocol details.

### 5.6 Iterate

As a scientist, I need to preserve design versions and compare snapshots so I can understand why one strategy replaced another.

## 6. Non-Goals

1. Do not make chat the primary editor for study structure.
2. Do not require users to ask for basic diagnostics.
3. Do not show a detached visualization that cannot explain its source study state.
4. Do not imply design recommendation is AI intuition; it must trace to MCP diagnostics and declared objectives.
5. Do not perform numerical DOE, modeling, power, cost, or optimization calculations in the LLM.
6. Do not claim live recomputation until the MCP payload refresh path exists.

## 7. Product Surfaces

The redesigned workbench has five major surfaces:

```text
1. Study Setup
2. Candidate Designs
3. Compare
4. Run Plan
5. Learn / Explain
```

These can be implemented as tabs, center-panel modes, or route-level views inside the React workbench.

## 8. Highest-Value Upgrade

The highest-value redesign is the candidate design comparison workspace.

It should let the user:

```text
1. define problem structure
2. generate multiple feasible candidate designs
3. compare them visually and quantitatively
4. inspect what each design can and cannot learn
5. ask inline "explain this" questions
6. commit one design into an executable run plan
```

This directly moves the product from messaging to decision-making.

## 9. Success Criteria

The redesign succeeds when:

```text
- A user can choose between 2 to 4 candidate designs without asking a chat question.
- Every candidate design shows run count, estimable effects, curvature support, confounding risk, and execution tradeoffs.
- Every recommendation includes best-for, tradeoff, and watch-out explanations.
- Changing study assumptions produces visible changed-state indicators.
- The committed run plan is traceable to the selected candidate design and its diagnostics.
- AI explanations cite the specific object they explain.
- Numerical claims remain backed by MCP artifacts.
```

## 10. Key Product Risks

| Risk | Mitigation |
|---|---|
| The workbench becomes a prettier dashboard, not a planning tool | Make candidate generation, comparison, and commit-to-run-plan first-class surfaces. |
| AI explanations drift away from computed facts | Bind every explanation card to artifact IDs, diagnostic codes, and recommendation reason codes. |
| Users mistake recommendation for validation | Use explicit labels: planned, recommended, predicted, verified, unavailable. |
| Sequential DOE is hidden | Add study versions, snapshots, and augmentation pathways. |
| Current architecture cannot embed a native Codex UI | Implement the workbench as the React dashboard opened through local preview. |

