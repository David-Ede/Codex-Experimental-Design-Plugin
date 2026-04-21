# Plugin Smoke Tester Skill Plan

## Decision

Add one additional skill to the DOE Scientific Toolchain plugin: `plugin-smoke-tester`.

This skill should be focused on plugin usability and release-gate confidence. It should not expand the scientific advisory surface or duplicate the existing `scientific-study-designer` workflow.

## Current State

The plugin already has one primary skill:

```text
plugins/doe-scientific-toolchain/skills/scientific-study-designer/SKILL.md
```

The plugin manifest already exposes plugin skills through:

```text
plugins/doe-scientific-toolchain/.codex-plugin/plugin.json
```

The canonical build contract defines the product flow as:

```text
Codex skill -> Python MCP server -> schema-valid artifacts -> React dashboard preview
```

The smoke-test skill should sit beside `scientific-study-designer` and make that product flow easier to validate repeatedly.

## Skill Name and Location

Recommended skill name:

```text
plugin-smoke-tester
```

Recommended path:

```text
plugins/doe-scientific-toolchain/skills/plugin-smoke-tester/SKILL.md
```

Optional UI metadata path:

```text
plugins/doe-scientific-toolchain/skills/plugin-smoke-tester/agents/openai.yaml
```

Do not add bundled scripts in the first version unless the smoke workflow becomes hard to run consistently by instruction alone.

## Frontmatter

Use trigger-heavy frontmatter so Codex selects this skill for validation and smoke-test requests:

```yaml
---
name: plugin-smoke-tester
description: Run DOE Scientific Toolchain plugin smoke tests and Gate 0 validation. Use when checking plugin installability, MCP startup, tool discovery, schema validation, fixture validation, dashboard typecheck/test/build, or end-to-end minimal study artifact generation for the doe-scientific-toolchain plugin.
---
```

## Interface Metadata

If `agents/openai.yaml` is added, use concise values:

```yaml
display_name: Plugin Smoke Tester
short_description: Validate DOE plugin metadata, MCP startup, schemas, fixtures, and dashboard checks.
default_prompt: Run the DOE Scientific Toolchain plugin smoke checks and report pass/fail with blocking issues and artifact paths.
```

Generate this file through the standard skill tooling if possible instead of hand-writing it.

## Source Documents to Read

The skill should instruct Codex to read only what is needed:

1. Always read `Canonical Build Contract.md` before deciding pass/fail criteria.
2. Read `README.md` for the current canonical command list.
3. Read `docs/plugin_mcp_smoke_test.md` when MCP startup, tool discovery, or study creation smoke tests are involved.
4. Read plugin metadata only when checking packaged plugin structure:

```text
plugins/doe-scientific-toolchain/.codex-plugin/plugin.json
plugins/doe-scientific-toolchain/.mcp.json
.agents/plugins/marketplace.json
.codex/config.toml.example
```

## Core Responsibilities

The skill should help Codex:

- Verify plugin metadata exists and uses plugin-root-relative paths.
- Verify the repo-local marketplace exposes `doe-scientific-toolchain`.
- Verify the primary skill exists.
- Verify this smoke-test skill exists after implementation.
- Verify project-scoped MCP configuration exists.
- Start or inspect the MCP server.
- Confirm the expected launch tool registry is present.
- Run schema and fixture validation.
- Run dashboard typecheck, tests, and build.
- Create a minimal Gate 0 study when the MCP smoke path is available.
- Confirm persisted study artifacts exist.
- Report failures with command, exit code, short error excerpt, and likely owner area.

## Canonical Command Set

The skill should prefer the commands already documented by the repository:

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

The skill should not require every command to run for every request. It should select the smallest useful set based on the user's request, then state skipped checks clearly.

## MCP Minimum Surface

For Gate 0, the minimum MCP smoke path must prove:

- server startup works
- tool listing works
- `create_or_update_study` is exposed
- minimal study creation produces the expected response envelope
- expected artifacts are written under `outputs/studies/<study_id>/`

For launch-oriented checks, the skill should compare the listed tools against the launch tool inventory in `Canonical Build Contract.md`, including:

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

Paper-class tools should be reported separately and must not be required for Gate 0 or Gate 1 unless the contract changes.

## Artifact Smoke Criteria

A minimal study smoke test passes only when both conditions are true:

1. The response envelope includes:

```text
study_id
run_id
status
artifact_paths
warnings
errors
structured_content
```

2. These files exist:

```text
outputs/studies/<study_id>/study.json
outputs/studies/<study_id>/audit_log.jsonl
```

Warnings do not automatically fail the smoke test, but they must be surfaced in the final report.

## Reporting Format

The skill should produce a compact, repeatable report:

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

## Failure Classification

Use these owner areas in reports:

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

This keeps failures actionable without requiring the user to inspect raw logs first.

## Guardrails

The skill must include these guardrails:

- Do not perform DOE generation, model fitting, optimization, cost calculation, or scientific recomputation in natural language.
- Do not describe a smoke pass as scientific validation.
- Do not claim paper-class readiness unless the required paper-class tools, fixtures, dashboard views, and validation reports exist.
- Treat warnings and unavailable states as meaningful output.
- Cite persisted artifact paths as the source of truth.
- Keep failures concrete and reproducible.
- Do not hide skipped checks.

## Non-Goals

The skill should not:

- Recommend DOE strategies.
- Review scientific model quality.
- Interpret experimental results.
- Generate paper-class claims.
- Replace `scientific-study-designer`.
- Add new MCP behavior.
- Add dashboard features.

Those responsibilities belong to the primary scientific skill, the MCP server, or future targeted skills.

## Optional Future Script

If repeated manual smoke checks become noisy, add:

```text
plugins/doe-scientific-toolchain/skills/plugin-smoke-tester/scripts/run_gate_smoke.ps1
```

The script should:

- run the canonical commands in order
- capture per-command logs
- emit a JSON or Markdown summary
- preserve exit codes
- avoid destructive cleanup unless explicitly requested

Do not add this script in the first version unless command orchestration becomes a real maintenance problem.

## Acceptance Criteria

The skill is ready when:

- `SKILL.md` exists at the recommended path.
- Frontmatter uses only `name` and `description`.
- The description clearly triggers on plugin smoke tests, MCP startup, tool discovery, schema validation, fixture validation, dashboard checks, and minimal artifact generation.
- The body stays concise and procedural.
- The body references `Canonical Build Contract.md`, `README.md`, and `docs/plugin_mcp_smoke_test.md`.
- The skill distinguishes Gate 0, Gate 1, and paper-class readiness.
- The skill defines a fixed report format.
- The skill includes guardrails against scientific overclaiming.
- Skill validation passes with the standard skill validation tool.

## Implementation Checklist

1. Create `plugins/doe-scientific-toolchain/skills/plugin-smoke-tester/`.
2. Create `SKILL.md` with the frontmatter and workflow above.
3. Optionally generate `agents/openai.yaml`.
4. Run skill validation.
5. Run a representative smoke check using the skill.
6. Update this plan if the first real use exposes missing checks or ambiguous reporting.
