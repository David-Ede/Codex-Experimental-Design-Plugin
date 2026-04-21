# Local Environment

This repository is local-first. Gate 0 development uses the project-scoped MCP
configuration in `.codex/config.toml.example`.

Required local tools:

- Python 3.11 or 3.12
- uv
- Node.js 20 or newer
- pnpm 9 or newer
- Optional but recommended: a native `rg` install on PATH. If Codex resolves
  `rg` from `WindowsApps` and gets `Access is denied`, use PowerShell
  `Select-String` or install ripgrep with `winget install BurntSushi.ripgrep.MSVC`.

Gate 0 commands:

```powershell
uv --directory mcp-server sync --all-extras --dev
uv --directory mcp-server run pytest
uv --directory mcp-server run python ..\scripts\validate_schemas.py
.\scripts\validate_artifacts.ps1 -StudyId <study_id>
.\mcp-server\.venv\Scripts\python.exe .\scripts\summarize_study.py --study-id <study_id>
pnpm --dir apps/dashboard install --frozen-lockfile
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard build
uv --directory mcp-server run python -m doe_toolchain.server --list-tools
uv --directory mcp-server run python -m doe_toolchain.server --startup-check
```
