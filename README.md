<!-- mcp-name: io.github.qso-graph/darc-dok-mcp -->
# darc-dok-mcp

[![PyPI](https://img.shields.io/pypi/v/darc-dok-mcp?label=PyPI&color=blue)](https://pypi.org/project/darc-dok-mcp/)
[![MCP Registry](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fregistry.modelcontextprotocol.io%2Fv0%2Fservers%3Fsearch%3Dio.github.qso-graph%2Fdarc-dok-mcp%26version%3Dlatest&query=%24.servers%5B0%5D.server.version&label=MCP%20Registry&color=blue)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.qso-graph/darc-dok-mcp&version=latest)

MCP server for **DARC DOKs and special DOKs** as DARC publishes them: the local-club codes of DARC's [DOK-Liste](https://www.darc.de/fileadmin/filemounts/referate/dx/DOK-Liste.pdf) (2016-12-26) and the event codes of DARC's [special-DOK list](https://www.darc.de/fileadmin/filemounts/referate/sdok/SDOK_List.csv), with each special DOK's validity window. DOKs are used for DARC's DLD award, the DOK best-lists and the WAG contest, and in ADIF's `DARC_DOK` field.

Part of the [qso-graph](https://qso-graph.io/) project. **No network, no authentication**: the owner's list ships with the package, and every answer names its source.

## Install

```bash
uvx darc-dok-mcp            # run it; nothing to install
```

## Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `darc_dok_lookup` | One DOK or special DOK: district and club, or purpose, callsign, window and sponsoring club | code |
| `darc_dok_valid_on` | Whether a DOK or special DOK was valid on a QSO's date | code, on_date |
| `darc_dok_search` | Find DOKs by club, town, district or purpose | text, limit |
| `darc_dok_codes_for` | Kept for the shared tool set; DOKs map to no ADIF subdivision | dxcc, subdivision |
| `darc_dok_source_info` | Owner, editions, terms and the shipped files' checksums | — |
| `get_version_info` | Service version + the owner's edition served (fleet identity attestation) | — |

## Quick Start

No credentials needed — just install and configure your MCP client.

### Configure your MCP client

darc-dok-mcp works with any MCP-compatible client. Add the server config and restart — tools appear automatically.

#### Claude Desktop

Add to `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

#### Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

#### ChatGPT Desktop

```json
{
  "mcpServers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

#### VS Code / GitHub Copilot

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

#### Gemini CLI

Add to `~/.gemini/settings.json` (global) or `.gemini/settings.json` (project):

```json
{
  "mcpServers": {
    "darc-dok": {
      "command": "uvx",
      "args": ["darc-dok-mcp"]
    }
  }
}
```

### Ask questions

> "Which club is DOK A01?"

> "Was special DOK 01ALT valid on 2004-06-01?"

> "Which DOKs are in district Baden?"

## MCP Inspector

```bash
darc-dok-mcp --transport streamable-http --port 8018
```

Then open the MCP Inspector at `http://localhost:8018`.

## Development

```bash
git clone https://github.com/qso-graph/darc-dok-mcp.git
cd darc-dok-mcp
uv sync --group dev
uv run pytest
```

`scripts/build.py` checks the owner's files against their checksums and regenerates `derived/` and `load.sql`, a PostgreSQL load for QSO Graph's reference data (load QG ADIF's `adif` schema first).

## License

darc-dok-mcp's own code is GPL-3.0-or-later. See [LICENSE](LICENSE) for details.

**The DOK lists are DARC's, not ours.** The package ships DARC's **DOK-Liste** (DARC DX-Referat, by Karsten Radwan, DL2ABM, 26.12.2016) and **SDOK_List.csv** (DARC SDOK-Referat) unchanged, with their SHA-256s, and answers from facts read from them, each citing its page or row. They are the Deutscher Amateur-Radio-Club e.V.'s work; our licence doesn't cover them, and we claim no rights in them. The district index (`derived/`) is ours. See [NOTICE](NOTICE).
