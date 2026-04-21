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

1. For common first-pass DOE setup where the user wants a committed run matrix, prefer `create_candidate_run_plan` with study metadata, factors, responses, candidate families, recommendation mode, and run budget in one request.
2. Use the explicit multi-step workbench tools only when the user is comparing alternatives interactively: `create_or_update_study`, `generate_candidate_designs`, `compare_candidate_designs`, `commit_run_plan`, then `generate_dashboard_payload`.
3. Skip placeholder-only tools such as `validate_factor_space` when they are registered as Gate 0 placeholders and cannot persist validation artifacts.
4. Prefer study-object-first workbench flows over chat-only inspection.
5. Generate or refresh `dashboard_payload.json` before launching the dashboard or workbench preview.
6. Surface warnings, unavailable states, and validation failures directly in user-facing summaries.
7. Cite persisted artifact paths as the source of truth.
8. Use compact artifact checks such as `scripts/validate_artifacts.ps1` and `scripts/summarize_study.py` instead of reading full dashboard payloads unless detailed inspection is required.

## Guardrails

- Codex may orchestrate tools, inspect artifacts, and explain results.
- MCP tools are the numerical source of truth.
- Dashboard views render persisted payload data only.
- Component costs must come from direct user input. Never infer or fetch reagent prices.
- Missing optional inputs must be represented as unavailable states, not as zeros or successful results.
- Verification plans are not verification results.
- Candidate recommendations must expose tradeoffs and what the design can and cannot learn.
- Contextual AI explanations must cite source artifacts or diagnostics.

## Gate 0 Smoke Prompt

Create a minimal DOE study using `create_or_update_study`, then confirm that `outputs/studies/<study_id>/study.json` and `audit_log.jsonl` were written and that the returned envelope includes status, warnings, errors, artifact paths, and structured content.
