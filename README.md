# DOE Scientific Toolchain

Local-first Codex plugin workflow for DOE and IVT/QbD analysis:

```text
Codex skill -> Python MCP server -> schema-valid artifacts -> React dashboard preview
```

Gate 0 provides repository layout, plugin metadata, MCP server registration,
minimum schemas, fixtures, validation, tests, and a dashboard shell. Scientific
algorithms start only after Gate 0 passes.

## Gate 0 Checks

```powershell
uv --directory mcp-server run pytest
uv --directory mcp-server run python ..\scripts\validate_schemas.py
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard build
uv --directory mcp-server run python -m doe_toolchain.server --list-tools
```

Plugin/MCP smoke-test details are documented in
`docs/plugin_mcp_smoke_test.md`.

## Fast Study Setup

For common first-pass workbench runs, prefer the `create_candidate_run_plan`
MCP tool. It creates or updates the study, generates candidate designs, compares
the preferred candidate, commits the run plan, and refreshes the dashboard
payload in one call. Use `scripts/validate_artifacts.ps1` and
`scripts/summarize_study.py` for compact follow-up checks without loading full
payload JSON into the chat context.
