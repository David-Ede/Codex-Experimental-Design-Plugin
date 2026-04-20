# DOE Toolchain MCP Server

Gate 0 provides the package skeleton, launch tool registration, schema/fixture
tests, and a callable `create_or_update_study` implementation.

Start or inspect the server from the repository root:

```powershell
uv --directory mcp-server run python -m doe_toolchain.server --list-tools
uv --directory mcp-server run python -m doe_toolchain.server --startup-check
uv --directory mcp-server run python -m doe_toolchain.server --smoke-create-study
uv --directory mcp-server run python -m doe_toolchain.server
```
