# Plugin/MCP Smoke Test

Gate 0 requires proving that the repo-local plugin metadata, project-scoped MCP
configuration, skill, server startup, and `create_or_update_study` skeleton work
together.

## Procedure

1. Confirm plugin metadata exists:

   ```powershell
   Test-Path .\plugins\doe-scientific-toolchain\.codex-plugin\plugin.json
   Test-Path .\plugins\doe-scientific-toolchain\skills\scientific-study-designer\SKILL.md
   ```

2. Confirm the repo-local marketplace exposes the plugin:

   ```powershell
   Get-Content .\.agents\plugins\marketplace.json
   ```

3. Copy or apply the project-scoped MCP settings:

   ```powershell
   Copy-Item .\.codex\config.toml.example .\.codex\config.toml
   ```

4. Start or inspect the MCP server from the repository root:

   ```powershell
   uv --directory mcp-server run python -m doe_toolchain.server --list-tools
   uv --directory mcp-server run python -m doe_toolchain.server --startup-check
   ```

5. Call the Gate 0 study creation smoke command:

   ```powershell
   uv --directory mcp-server run python -m doe_toolchain.server --smoke-create-study
   ```

6. Confirm the expected artifacts exist:

   ```powershell
   Test-Path .\outputs\studies\gate0_smoke_study\study.json
   Test-Path .\outputs\studies\gate0_smoke_study\audit_log.jsonl
   ```

7. In Codex, enable the repo-local plugin, load the
   `scientific-study-designer` skill, start the configured MCP server, and call
   `create_or_update_study` with a minimal title.

The smoke test passes when the response envelope includes `study_id`, `run_id`,
`status`, `artifact_paths`, `warnings`, `errors`, and `structured_content`, and
the generated `study.json` and `audit_log.jsonl` are present under
`outputs/studies/<study_id>/`.
