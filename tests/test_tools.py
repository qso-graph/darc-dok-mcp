"""The MCP tools, through FastMCP."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from darc_dok_mcp import server

TOOLS = {"get_version_info", "darc_dok_source_info", "darc_dok_lookup", "darc_dok_search", "darc_dok_codes_for", "darc_dok_valid_on"}


def call(name: str, args: dict | None = None) -> dict:
    async def go():
        async with Client(server.mcp) as c:
            return (await c.call_tool(name, args or {})).data
    return asyncio.run(go())


def test_tool_list():
    async def go():
        async with Client(server.mcp) as c:
            return {t.name for t in await c.list_tools()}
    assert asyncio.run(go()) == TOOLS


def test_version_info():
    r = call("get_version_info")
    assert r["service_name"] == "darc-dok-mcp" and r["spec_version"]


def test_source_info_credits_the_owner():
    r = call("darc_dok_source_info")
    assert r["owner"] and r["url"].startswith("https://") and r["terms"]
    assert all(f["sha256"] for f in r["published_files"].values())


def test_every_answer_names_its_source():
    for name, args in (("darc_dok_lookup", {"code": "A01"}), ("darc_dok_search", {"text": "Konstanz"}),
                       ("darc_dok_codes_for", {"dxcc": 230}), ("darc_dok_valid_on", {"code": "A01", "on_date": "2026-10-06"})):
        r = call(name, args)
        assert "error" not in r, (name, r)
        assert r["source"]["owner"] and r["source"]["url"], name


def test_bad_input_is_an_error():
    assert "error" in call("darc_dok_lookup", {"code": "A B; DROP"})
    assert "error" in call("darc_dok_search", {"text": "x" * 101})
    assert "error" in call("darc_dok_codes_for", {"dxcc": 5000})
    assert "error" in call("darc_dok_codes_for", {"dxcc": 1, "subdivision": "TOOLONG"})
    assert "error" in call("darc_dok_valid_on", {"code": "A01", "on_date": "06.10.2026"})


def test_unknown_code_is_not_found():
    assert call("darc_dok_lookup", {"code": "ZZZ999"})["found"] is False


def test_help_and_version_exit_without_serving(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["darc-dok-mcp", "--version"])
    server.main()
    assert "darc-dok-mcp" in capsys.readouterr().out
