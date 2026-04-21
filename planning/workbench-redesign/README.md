# DOE Workbench Redesign Planning Packet

Date: 2026-04-21
Status: Draft redesign direction
Related existing documents:

```text
- Canonical Build Contract.md
- Product Requirements Document.md
- Dashboard UX Spec.md
- MCP Tool API Spec.md
- Implementation Roadmap.md
```

## Purpose

This planning packet reframes the plugin from a chat-first scientific assistant into an experiment strategy studio: a stateful DOE workbench where the study object is the main product surface and Codex is a contextual advisor around that object.

The current repository already establishes the correct numerical boundary:

```text
Codex skill -> deterministic MCP tools -> persisted artifacts -> React dashboard
```

This redesign keeps that boundary but changes the product center of gravity:

```text
Old product shape:
  conversation first, dashboard second

New product shape:
  structured study workspace first, AI explanation and chat second
```

## Planning Documents

| Document | Purpose |
|---|---|
| `Product_Redesign_Brief.md` | Defines the north star, product principles, user jobs, anti-patterns, and success criteria for the study-object-first redesign. |
| `Workspace_Information_Architecture.md` | Specifies the main workbench layout, panel system, screen-by-screen surfaces, and interaction model. |
| `Study_Object_and_State_Model.md` | Defines the core study object, candidate designs, snapshots, comparisons, recommendation modes, and artifact implications. |
| `Contextual_AI_and_Recommendation_Model.md` | Defines how AI should appear in context as advisor, critic, explainer, and recommendation layer rather than as the primary interface. |
| `Migration_Roadmap.md` | Converts the redesign into implementation phases and backlog items that can be reconciled with the current canonical build contract. |
| `Execution_Plan.md` | Defines the comprehensive build execution plan with workstreams, phases, repo areas, validation gates, tests, risks, and first milestone scope. |

## Core Redesign Thesis

The product should not make users ask the AI to discover basic scientific state. If a scientist needs to know run count, estimable terms, curvature support, confounding risk, missing inputs, or why a design is recommended, that information should be visible in the workspace.

AI should deepen, translate, critique, and guide. It should not be the only way to inspect a study.

## Implementation Reality

This packet does not assume a native embedded Codex plugin UI that is not currently documented. The practical implementation path remains:

```text
Codex plugin and skill
  calls MCP tools
  writes schema-valid study artifacts
  generates dashboard/workbench payloads
  opens a local React workbench in the Codex in-app browser
```

The redesign therefore treats the React dashboard as the primary workbench surface. Codex chat remains available, but the user should experience the workbench as the place where DOE decisions are made.

## Redesign Decisions

1. The central product object is a `study`, not a conversation.
2. The main workspace is candidate design comparison, not a chat transcript.
3. Every major view is bound to live study state and persisted artifacts.
4. Candidate design cards and comparison tables are first-class product surfaces.
5. Recommendation modes replace generic "ask what design is best" interactions.
6. AI explanations attach to specific study objects, diagnostics, warnings, and decisions.
7. "What you can learn / cannot learn" is visible for every candidate design.
8. Sequential DOE workflows are represented directly through versions, snapshots, augmentation paths, and follow-up strategies.
9. The MCP server remains the numerical source of truth.
10. Chat is a helper layer, not the primary inspection mechanism.

## How To Use This Packet

Use these docs before revising the canonical build plan. The intended sequence is:

```text
1. Review the redesign packet.
2. Decide which current docs become superseded or amended.
3. Update Canonical Build Contract.md only after the redesign scope is accepted.
4. Convert Migration_Roadmap.md phases into implementation issues or milestones.
5. Update schemas, MCP tools, and dashboard fixtures to support the workbench model.
```
