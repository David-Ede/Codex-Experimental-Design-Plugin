---
name: plugin-smoke-tester
description: Run DOE Scientific Toolchain plugin smoke tests and Gate 0 validation. Use when checking plugin installability, MCP startup, tool discovery, schema validation, fixture validation, dashboard checks, or end-to-end minimal study artifact generation for the doe-scientific-toolchain plugin.
---

# Plugin Smoke Tester

Use this skill to validate DOE Scientific Toolchain plugin usability, release-gate readiness, MCP startup and discovery, schema and fixture checks, dashboard checks, and minimal persisted study artifact generation.

## Source Discipline

1. Always read `Canonical Build Contract.md` before deciding pass/fail criteria.
2. Read `README.md` for the current canonical command list.
3. Read `docs/plugin_mcp_smoke_test.md` when MCP startup, tool discovery, or minimal study creation is in scope.
4. Read plugin metadata only when checking packaged plugin structure:
   - `plugins/doe-scientific-toolchain/.codex-plugin/plugin.json`
   - `plugins/doe-scientific-toolchain/.mcp.json`
   - `.agents/plugins/marketplace.json`
   - `.codex/config.toml.example`

## Scope

- Gate 0 checks repository layout, plugin metadata, marketplace exposure, skill files, project-scoped MCP configuration, MCP startup, launch tool registry, schemas, fixtures, dashboard shell checks, and minimal study artifact persistence.
- Gate 1 checks launch workflows, launch fixtures within tolerance, dashboard smoke coverage, launch schemas, provenance, audit entries, and security tests when those checks are available.
- Paper-class readiness is separate. Report paper-class tools, fixtures, dashboard views, and validation reports separately, and do not require them for Gate 0 or Gate 1 unless `Canonical Build Contract.md` changes.

## Canonical Commands

Prefer the repository-documented commands and run the smallest useful subset for the user's request. State every skipped check.

```powershell
uv --directory mcp-server run pytest
uv --directory mcp-server run python ..\scripts\validate_schemas.py
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard build
uv --directory mcp-server run python -m doe_toolchain.server --list-tools
uv --directory mcp-server run python -m doe_toolchain.server --startup-check
uv --directory mcp-server run python -m doe_toolchain.server --smoke-create-study
```

## Workflow

1. Check plugin metadata exists and uses plugin-root-relative paths.
2. Check `.agents/plugins/marketplace.json` exposes `doe-scientific-toolchain`.
3. Check the primary `scientific-study-designer` skill exists.
4. Check this `plugin-smoke-tester` skill exists.
5. Check project-scoped MCP configuration exists in `.codex/config.toml.example`.
6. Start or inspect the MCP server with the startup-check command when MCP is in scope.
7. List MCP tools and compare launch tools against `Canonical Build Contract.md`.
8. Run schema and fixture validation when data contracts are in scope.
9. Run dashboard typecheck, tests, and build when dashboard readiness is in scope.
10. Run minimal study artifact smoke when the MCP smoke path is available.
11. Confirm persisted artifact paths exist and cite them as the source of truth.

## MCP Minimum Surface

Gate 0 MCP smoke passes only when:

- server startup works
- tool listing works
- `create_or_update_study` is exposed
- minimal study creation returns the expected response envelope
- expected artifacts are written under `outputs/studies/<study_id>/`

For launch-oriented checks, compare listed tools against this launch inventory:

```text
create_or_update_study
validate_factor_space
design_doe
design_optimal_doe
import_endpoint_observations
import_time_resolved_observations
register_construct
calculate_theoretical_yield
fit_response_surface
analyze_effects
calculate_cogs_impact
suggest_next_experiment
plan_verification_runs
generate_dashboard_payload
launch_dashboard_preview
```

Report paper-class tools separately.

## Artifact Smoke Criteria

A minimal study smoke test passes only when the response envelope includes:

```text
study_id
run_id
status
artifact_paths
warnings
errors
structured_content
```

These files must exist:

```text
outputs/studies/<study_id>/study.json
outputs/studies/<study_id>/audit_log.jsonl
```

Warnings do not automatically fail the smoke test, but they must be surfaced in the final report.

## Failure Classification

Use these owner areas:

```text
plugin metadata
marketplace registration
skill packaging
MCP configuration
MCP server
tool registry
schema validation
fixtures
dashboard
artifact persistence
dependency setup
unknown
```

## Report Format

```text
Status: Passed | Failed | Partial | Skipped

Checks:
- Plugin metadata: Passed | Failed | Skipped
- Marketplace exposure: Passed | Failed | Skipped
- Skill files: Passed | Failed | Skipped
- MCP startup: Passed | Failed | Skipped
- MCP tool listing: Passed | Failed | Skipped
- Backend tests: Passed | Failed | Skipped
- Schema validation: Passed | Failed | Skipped
- Dashboard typecheck: Passed | Failed | Skipped
- Dashboard tests: Passed | Failed | Skipped
- Dashboard build: Passed | Failed | Skipped
- Minimal study artifact smoke: Passed | Failed | Skipped

Blocking issue:
- Exact command or file
- Exit code or validation failure
- Short log excerpt
- Likely owner area

Artifacts:
- outputs/studies/<study_id>/study.json
- outputs/studies/<study_id>/audit_log.jsonl
```

## Guardrails

- Do not perform DOE generation, model fitting, optimization, cost calculation, or scientific recomputation in natural language.
- Do not describe a smoke pass as scientific validation.
- Do not claim paper-class readiness unless the required paper-class tools, fixtures, dashboard views, and validation reports exist.
- Treat warnings and unavailable states as meaningful output.
- Cite persisted artifact paths as the source of truth.
- Keep failures concrete and reproducible.
- Do not hide skipped checks.
- Do not recommend DOE strategies, review scientific model quality, interpret experimental results, generate paper-class claims, replace `scientific-study-designer`, add MCP behavior, or add dashboard features.

## Acceptance Criteria

The smoke-test skill packaging is valid when:

- `plugins/doe-scientific-toolchain/skills/plugin-smoke-tester/SKILL.md` exists.
- Frontmatter uses only `name` and `description`.
- The description triggers on plugin smoke tests, MCP startup, tool discovery, schema validation, fixture validation, dashboard checks, and minimal artifact generation.
- The body is concise and procedural.
- The body references `Canonical Build Contract.md`, `README.md`, and `docs/plugin_mcp_smoke_test.md`.
- The body distinguishes Gate 0, Gate 1, and paper-class readiness.
- The body defines a fixed report format.
- The body includes guardrails against scientific overclaiming.
- Standard skill validation passes.
