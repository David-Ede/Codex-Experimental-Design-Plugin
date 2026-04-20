---
name: scientific-study-designer
description: Design and review DOE or IVT/QbD studies using the local DOE Scientific Toolchain MCP server, schema-valid artifacts, and dashboard payloads.
---

# Scientific Study Designer

Use this skill when creating, validating, or reviewing DOE and IVT/QbD study artifacts with the `doe-scientific-toolchain` MCP server.

## Gate Discipline

- Treat `Canonical Build Contract.md` as the source of truth.
- During Gate 0, use only repository, schema, fixture, plugin, MCP, and dashboard shell capabilities.
- Do not perform DOE generation, model fitting, theoretical-yield calculation, economics calculation, optimization, or scientific recomputation in natural language.
- Do not claim paper-class support unless Gate 2 tools and validation reports exist.

## Required Workflow

1. Create or select a study with `create_or_update_study`.
2. Validate factors and responses before any design work.
3. Generate or refresh `dashboard_payload.json` before launching the dashboard preview.
4. Surface warnings, unavailable states, and validation failures directly in user-facing summaries.
5. Cite persisted artifact paths as the source of truth.

## Guardrails

- Codex may orchestrate tools, inspect artifacts, and explain results.
- MCP tools are the numerical source of truth.
- Dashboard views render persisted payload data only.
- Component costs must come from direct user input. Never infer or fetch reagent prices.
- Missing optional inputs must be represented as unavailable states, not as zeros or successful results.
- Verification plans are not verification results.

## Gate 0 Smoke Prompt

Create a minimal DOE study using `create_or_update_study`, then confirm that `outputs/studies/<study_id>/study.json` and `audit_log.jsonl` were written and that the returned envelope includes status, warnings, errors, artifact paths, and structured content.
