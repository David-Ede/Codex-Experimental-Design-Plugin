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
