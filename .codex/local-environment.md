# Local Environment

This repository is local-first. Gate 0 development uses the project-scoped MCP
configuration in `.codex/config.toml.example`.

Required local tools:

- Python 3.11 or 3.12
- uv
- Node.js 20 or newer
- pnpm 9 or newer

Gate 0 commands:

```powershell
uv --directory mcp-server sync --all-extras --dev
uv --directory mcp-server run pytest
uv --directory mcp-server run python ..\scripts\validate_schemas.py
pnpm --dir apps/dashboard install --frozen-lockfile
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard build
uv --directory mcp-server run python -m doe_toolchain.server --list-tools
uv --directory mcp-server run python -m doe_toolchain.server --startup-check
```
