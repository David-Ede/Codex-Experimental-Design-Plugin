# Contextual AI and Recommendation Model

Date: 2026-04-21
Status: Draft redesign direction

## 1. Purpose

This document defines how AI should behave in the redesigned DOE workbench. The AI should be an embedded advisor, explainer, critic, and planning assistant attached to concrete study objects. It should not be the main interface for constructing or inspecting designs.

## 2. Role Boundary

AI owns:

```text
- framing vague goals into structured objectives
- explaining why a design fits or fails an objective
- translating diagnostics into plain scientific language
- flagging weak setups and risky assumptions
- suggesting sequential next steps
- drafting run-plan notes and protocol explanations
```

MCP tools own:

```text
- factor validation
- design generation
- estimability diagnostics
- alias/confounding diagnostics
- model fitting
- power/precision calculations when implemented
- cost calculations
- optimization and recommendation scoring
- payload generation
```

React workbench owns:

```text
- rendering study state
- user editing controls
- comparison tables
- chart interactions
- selection state
- display-only filtering and sorting
```

## 3. AI Surfaces

### 3.1 Right-Rail Advisor

Default modules:

```text
- Why this design?
- What you can learn
- What you cannot learn
- Key warnings
- Recommended next edit
- Source artifacts
```

The rail content changes when the user selects:

```text
- a factor
- a response
- a constraint
- a candidate design
- a comparison metric
- a warning
- a chart point
- a run matrix row
- a committed run plan
```

### 3.2 Inline Explain Buttons

Inline "explain this" buttons should exist near:

```text
- design family labels
- run count
- condition number
- alias/confounding warnings
- estimability matrix cells
- power or precision metrics
- center-point policy
- replication policy
- factor-space coverage plots
- response surface previews
- recommendations
```

The button should pass object context to the explanation layer. It should not require the user to write a prompt from scratch.

### 3.3 Why This Design Card

Always visible for recommended and committed designs.

Required fields:

```text
- one-paragraph rationale
- best for
- tradeoff
- watch out for
- source diagnostics
```

Example shape:

```json
{
  "title": "Why this design?",
  "summary": "This D-optimal candidate is ranked highest because it estimates the requested interaction terms within the 16-run budget while respecting the forbidden combinations.",
  "best_for": [
    "Estimating selected two-factor interactions",
    "Working within a fixed run budget"
  ],
  "tradeoff": [
    "It does not support a full quadratic model."
  ],
  "watch_out_for": [
    "Pure error is unavailable without replicated runs."
  ],
  "source_refs": [
    "design_metadata.json#diagnostics",
    "candidate_ranking.json#scores"
  ]
}
```

### 3.4 Can Learn / Cannot Learn Panel

Required fields:

```text
- estimable main effects
- estimable interactions
- curvature support
- pure error support
- lack-of-fit support
- confounded or aliased terms
- sensitivity to missing runs
- extrapolation limits
```

This must be generated from structured diagnostics first, then explained by AI.

### 3.5 Warning Explainer

Warnings should have:

```text
- plain-language meaning
- scientific impact
- recommended fix
- affected object
- source artifact
- severity
```

Example:

```text
High condition number means the model matrix is close to unstable. The design may still run, but coefficient estimates can be sensitive to noise. Consider more runs, narrower model terms, or a design family with better spread.
```

## 4. Recommendation Modes

Recommendation modes replace open-ended "what design is best?" prompts.

Modes:

```text
Minimize runs
Screen important factors
Estimate interactions
Fit curvature
Optimize response
Respect material/time constraints
Prepare for scale-up robustness
Custom weighted objective
```

Each mode should define:

```text
- user-facing label
- intended scientific job
- required inputs
- preferred design families
- ranking weights
- warning thresholds
- explanation template
```

### 4.1 Minimize Runs

Prioritize:

```text
- lowest run count
- main-effect estimability
- feasibility
```

Watch-outs:

```text
- interactions may be aliased
- curvature is usually unsupported
- missing runs can be more damaging
```

### 4.2 Screen Important Factors

Prioritize:

```text
- main effects
- broad factor coverage
- economical run count
- categorical factor handling
```

Watch-outs:

```text
- not enough detail for optimization
- weak interaction interpretation
- response curvature may be missed
```

### 4.3 Estimate Interactions

Prioritize:

```text
- selected two-factor interaction estimability
- model rank
- reduced aliasing
- sufficient run count
```

Watch-outs:

```text
- run count increases quickly
- not every interaction may be interpretable
- hierarchy and parsimony rules matter
```

### 4.4 Fit Curvature

Prioritize:

```text
- quadratic support
- center points
- prediction precision near optimum
- response-surface design family
```

Watch-outs:

```text
- requires enough continuous factor levels
- categorical-heavy designs may not fit
- pure error requires replication
```

### 4.5 Optimize Response

Prioritize:

```text
- response-surface quality
- prediction precision
- desirability support
- constraint handling
```

Watch-outs:

```text
- optimization is model-based until verified
- extrapolation outside design space must be blocked
- quality constraints may dominate productivity goals
```

### 4.6 Respect Material/Time Constraints

Prioritize:

```text
- max run count
- batch/day limits
- hard-to-change factors
- forbidden combinations
- split-plot or blocked design support when implemented
```

Watch-outs:

```text
- constraints may reduce estimability
- randomization may be partial
- execution practicality can trade off with statistical quality
```

### 4.7 Prepare for Scale-Up Robustness

Prioritize:

```text
- robustness across factor variation
- boundary coverage
- verification strategy
- sensitivity to noise
- follow-up augmentation path
```

Watch-outs:

```text
- more runs may be required
- robustness is not proven until confirmatory data exist
- scale-up factors may need explicit inclusion
```

## 5. AI Output Requirements

AI-generated explanation blocks must include:

```text
- object type
- object ID
- source artifact refs
- diagnostic refs
- unavailable-state refs, if any
- clear distinction between computed facts and advisory interpretation
```

AI must not:

```text
- invent run counts
- invent DOE matrices
- invent estimable terms
- invent power, p-values, model metrics, costs, or recommendations
- override MCP diagnostics
- hide warnings to make a recommendation sound cleaner
```

## 6. Prompting Model

Instead of a blank chat prompt, use scoped actions:

```text
Explain selected design
Explain this warning
Compare selected candidates
Suggest how to reduce runs
Suggest how to support curvature
Suggest augmentation path
Draft run-plan rationale
Summarize changes since snapshot
```

Each action should provide structured context:

```text
- study_id
- snapshot_id
- selected object ID
- visible warnings
- relevant artifact paths
- user selected recommendation mode
```

## 7. Recommendation Explanation Contract

Every recommended design should produce:

```text
- recommendation label
- ranking score or ordinal rank
- top positive drivers
- top tradeoffs
- blocking warnings
- unavailable assumptions
- next-step advice
```

Example:

```json
{
  "candidate_design_id": "candidate_dopt_16",
  "rank": 1,
  "recommendation_label": "recommended",
  "positive_drivers": [
    "Selected interactions are estimable.",
    "Run count is within the 16-run budget.",
    "Forbidden combinations are excluded."
  ],
  "tradeoffs": [
    "Full curvature is not estimable.",
    "Pure error is unavailable without replicates."
  ],
  "next_step": "Commit this design or increase max runs if curvature is required."
}
```

## 8. Acceptance Criteria

The contextual AI layer is sufficient when:

```text
- Explanations appear before the user asks for them.
- Every explanation is attached to a specific object.
- Inline explain actions do not require freeform prompting.
- Warnings include impact and fix guidance.
- Recommendation summaries expose tradeoffs, not only strengths.
- No AI explanation contains numerical claims without source diagnostics or artifacts.
```

