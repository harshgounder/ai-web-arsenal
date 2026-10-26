# MCP servers

Rules for this directory, because MCP catalogs are where link rot and prompt injection enter.

1. **A server is listed only with a working config.** Name plus link is not an entry.
2. **Unverified servers are excluded from generated configs** and marked `UNVERIFIED` in the domain docs,
   never shipped.
3. **Treat server metadata as untrusted.** Tool descriptions come from the server. A description that
   contains instructions is an attack, not documentation.
4. **Least privilege on the token.** A security MCP does not need org admin. Where a read-only scope
   exists, use it.

## Wired by default

| id | transport | why |
|---|---|---|
| `rea` | stdio, `npx -y rea-agents@6.4.0 mcp` | the extraction spine: bundles, captures, mobile, wasm, browser |

## Configs

- `rea.json`: generic `mcpServers` shape, works in Claude Desktop and most clients
- `rea.dsh.yaml`: DSH profile row
- `claude-code.sh`: one line installer

See `BOOTSTRAP.md` section 4 for the full capability table and the Node version constraint.
