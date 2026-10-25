"""darc-dok-mcp: DARC DOKs and special DOKs, as DARC publishes them (QG Reference).

Read-only. The facts the tools answer from are in data/facts/, each citing where it appears
in the owner's document, which is referenced by URL and SHA-256 (data/SOURCE.json), not shipped.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from typing import Any, NoReturn

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from . import __spec_version__, __version__, reference

P = "darc_dok"

mcp = FastMCP(
    "darc-dok-mcp",
    version=__version__,
    instructions=(
        "DARC's DOKs (local-club codes, e.g. A01) and special DOKs (event codes with a validity window) as DARC publishes them. "
        "Every answer names its source. Facts are the owner's; anything marked derived is ours. "
        "Use darc_dok_lookup for a code, darc_dok_valid_on to check a special DOK on a QSO's date, and darc_dok_search for a club or town."
    ),
)

_CODE = re.compile(r"^[A-Za-z0-9]{1,12}$")
_PAS = re.compile(r"^[A-Za-z0-9]{1,4}$")


# MCP 2026-07-28 tool annotations. The defaults are pessimistic — a tool that declares
# nothing is advertised as destructive, non-idempotent and open-world, and the
# specification tells a client it may keep a human in the loop for that.
#
# All six tools share one block, and that is honest rather than lazy: every one answers
# from the DOK data bundled in the wheel. Nothing in this package opens a socket and
# nothing writes, so the four hints are the same for all six and the reason is the same
# too. tests/test_mcp_conformance.py asserts that premise rather than the convenience,
# because one shared block is also exactly what a careless copy produces.
_ANSWERS_FROM_CARRIED_DATA = {
    "readOnlyHint": True,
    "destructiveHint": False,
    # Stronger than in most of this fleet: the data ships in the wheel, so the same call
    # returns the same answer until the package is upgraded. Servers that read a live
    # service are idempotent only in the sense the specification means — the tool changes
    # nothing — while their answers still move. Here neither moves.
    #
    # Note this holds even for darc_dok_valid_on, which unlike its siblings answers a real
    # question: special DOKs carry published validity windows, so the same code gives
    # different answers on different dates. That is the *argument* changing, not the tool.
    "idempotentHint": True,
    # Nothing leaves the machine. DARC's DOK-Liste and SDOK_List.csv are referenced by URL
    # and SHA-256, not fetched at runtime; the facts taken from them ship as data.
    "openWorldHint": False,
}


def _credit() -> dict[str, Any]:
    s = reference.source()
    return {"owner": s["owner"], "document": s["document_title"], "edition": s["edition"],
            "url": s["url"]}


def _err(msg: str) -> NoReturn:
    """Reject bad input the way the protocol specifies.

    This returned ``{"error": msg, "source": _credit()}`` as a *successful* result, so a
    client could not tell a rejection from an answer. The specification says of
    ``CallToolResult.isError`` that otherwise "the LLM would not be able to see that an
    error occurred and self-correct".

    DARC's credit is not carried into the raised error, and nothing is lost by that: every
    successful answer builds its own ``source`` from ``_credit()``, which was checked before
    this changed. Attribution belongs on the data, and a rejected input returns no data.
    """
    raise ToolError(msg)


def _version_info_payload() -> dict[str, Any]:
    return {"service_name": "darc-dok-mcp", "service_version": __version__,
            "spec_version": __spec_version__}


@mcp.tool(annotations=_ANSWERS_FROM_CARRIED_DATA)
def get_version_info() -> dict[str, Any]:
    """Get darc-dok-mcp's version and the edition of DARC's list it serves.

    Returns:
        service_name, service_version (PyPI), and spec_version (the owner's edition).
    """
    return _version_info_payload()


@mcp.tool(name=f"{P}_source_info", annotations=_ANSWERS_FROM_CARRIED_DATA)
def source_info() -> dict[str, Any]:
    """Who owns this list, which edition is served, its terms, and the owner's files' URLs and SHA-256s."""
    s = reference.source()
    return {
        "owner": s["owner"],
        "document": s["document_title"],
        "edition": s["edition"],
        "url": s["url"],
        "authority": s.get("authority"),
        "terms": s["terms"],
        "retrieved": {n: m["retrieved"] for n, m in s["published"].items()},
        "published_files": {n: {"url": m["url"], "sha256": m["sha256"]} for n, m in s["published"].items()},
        "lists": {n: len(ol.records) for n, ol in reference.lists().items()},
        "derived_note": s["derived_note"],
    }


@mcp.tool(name=f"{P}_lookup", annotations=_ANSWERS_FROM_CARRIED_DATA)
def lookup(code: str) -> dict[str, Any]:
    """One DOK or special DOK: the district and local club (DOKs), or the purpose, callsign, validity window and sponsoring club (special DOKs), with the citation.

    Args:
        code: A DOK (e.g. A01) or special DOK (e.g. 1000ER).
    """
    code = (code or "").strip()
    if not _CODE.match(code):
        _err("code must be 1 to 12 letters or digits")
    code = code.lstrip("0") or code if code.isdigit() else code
    recs = reference.lookup(code)
    if not recs:
        return {"code": code, "found": False, "source": _credit()}
    return {"code": code, "found": True, "records": recs, "source": _credit()}


@mcp.tool(name=f"{P}_search", annotations=_ANSWERS_FROM_CARRIED_DATA)
def search(text: str, limit: int = 50) -> dict[str, Any]:
    """Find codes whose name, prefixes, area wording or attributes contain every word of text.

    Args:
        text: Words to look for, e.g. "Konstanz", "Baden" or "Jubiläum".
        limit: Most records to return (1 to 200, default 50).
    """
    text = (text or "").strip()
    if not 1 <= len(text) <= 100:
        _err("text must be 1 to 100 characters")
    limit = max(1, min(int(limit), 200))
    hits, total = reference.search(text, limit=limit)
    return {"text": text, "total": total, "returned": len(hits), "records": hits, "source": _credit()}


@mcp.tool(name=f"{P}_codes_for", annotations=_ANSWERS_FROM_CARRIED_DATA)
def codes_for(dxcc: int, subdivision: str | None = None) -> dict[str, Any]:
    """DOK lists don't map to ADIF subdivisions: this answers for entity 230 (Germany) with nothing per subdivision. Use darc_dok_search for a district or town.

    Args:
        dxcc: ADIF DXCC entity code (e.g. 291 for the United States, 1 for Canada).
        subdivision: ADIF Primary_Administrative_Subdivision code, e.g. "QC" or "AZ".
    """
    if not isinstance(dxcc, int) or not 0 <= dxcc <= 999:
        _err("dxcc must be an ADIF DXCC entity code, 0 to 999")
    if subdivision is not None and not _PAS.match(subdivision.strip()):
        _err("subdivision must be an ADIF subdivision code, 1 to 4 letters or digits")
    hits = reference.codes_for(dxcc, subdivision)
    return {"dxcc": dxcc, "subdivision": subdivision, "codes": hits, "source": _credit()}


@mcp.tool(name=f"{P}_valid_on", annotations=_ANSWERS_FROM_CARRIED_DATA)
def valid_on(code: str, on_date: str) -> dict[str, Any]:
    """Whether a DOK or special DOK was valid on a date: a special DOK counts only inside the window DARC published for it. A DOK merged into another (e.g. A49, merged into A12 in 2001) shows replaced_by.

    Args:
        code: A DOK (e.g. A01) or special DOK (e.g. 1000ER).
        on_date: The date, YYYY-MM-DD.
    """
    code = (code or "").strip()
    if not _CODE.match(code):
        _err("code must be 1 to 12 letters or digits")
    code = code.lstrip("0") or code if code.isdigit() else code
    try:
        d = date.fromisoformat((on_date or "").strip())
    except ValueError:
        _err("on_date must be YYYY-MM-DD")
    recs = reference.valid_on(code, d)
    if not recs:
        return {"code": code, "found": False, "source": _credit()}
    return {"code": code, "on_date": d.isoformat(), "found": True, "records": recs, "source": _credit()}


def main() -> None:
    """Run the darc-dok-mcp server."""
    args = sys.argv[1:]
    if "--version" in args:
        print(f"darc-dok-mcp {__version__} ({__spec_version__})")
        return
    if "--help" in args or "-h" in args:
        print("darc-dok-mcp: DARC DOKs and special DOKs as DARC publishes them, over MCP (stdio).\n"
              "Options: --transport streamable-http --port N, --version")
        return
    transport, port = "stdio", 8018
    for i, arg in enumerate(args):
        if arg == "--transport" and i + 1 < len(args):
            transport = args[i + 1]
        if arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
    # Written out rather than passed through: fastmcp takes a literal, and a
    # str that happens to hold the right word is not the same thing.
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
