"""An owner's published list, loaded from this package's data folder (QG Reference).

The same module in every owner-list package (cq-zones-mcp, itu-zones-mcp, darc-dok-mcp):
the data and its JSON Schema are the shared contract, not this code.

data/
  SOURCE.json   the owner, document, edition, terms, and each file's URL, retrieval date, SHA-256
  facts/        the facts as JSON; every record cites where it appears in the published file
  derived/      our additions, labelled as ours
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from importlib.resources import files
from typing import Any

DATA = files(__package__).joinpath("data")


def _json(*parts: str) -> Any:
    node = DATA
    for p in parts:
        node = node.joinpath(p)
    return json.loads(node.read_text(encoding="utf-8"))


@dataclass
class OwnerList:
    """One facts file and its indexes."""

    # Named list_name, not list: a field called `list` shadows the builtin
    # inside the class body, so `records: list[dict[str, Any]]` below resolved
    # to this field subscripted rather than to the builtin. Nothing broke at
    # run time — `from __future__ import annotations` means the strings are
    # never evaluated — but every annotation after it was wrong, and anything
    # that resolves them (mypy, a dataclass validator, a docs generator) saw
    # the wrong type. Found by mypy (qso-graph-devel#66).
    #
    # `list_name` is what search() already calls the same thing. The `"list"`
    # key in tool output is unchanged: that is the published field name.
    list_name: str
    owner: str
    document: str
    edition: str
    records: list[dict[str, Any]]
    by_code: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for r in self.records:
            self.by_code.setdefault(r["code"].upper(), []).append(r)


@cache
def source() -> dict[str, Any]:
    # Annotated rather than returned straight: _json returns Any, because it
    # reads whatever JSON is in the file, and handing that back from a function
    # that promises a dict is the promise being unchecked.
    data: dict[str, Any] = _json("SOURCE.json")
    return data


@cache
def lists() -> dict[str, OwnerList]:
    out: dict[str, OwnerList] = {}
    for name in source()["facts"]:
        d = _json("facts", name)
        out[d["list"]] = OwnerList(d["list"], d["owner"], d["document"], d["edition"], d["records"])
    return out


@cache
def derived(name: str) -> Any:
    return _json("derived", name)


def _with_list(name: str, r: dict[str, Any]) -> dict[str, Any]:
    return {"list": name, **r}


def lookup(code: str) -> list[dict[str, Any]]:
    """Every record with this code, in every list of this package."""
    key = code.strip().upper()
    return [_with_list(n, r) for n, ol in lists().items() for r in ol.by_code.get(key, [])]


def _text(r: dict[str, Any]) -> str:
    parts = [r["code"], r.get("name") or ""]
    parts += [v or "" for v in (r.get("attributes") or {}).values()]
    for c in r["covers"]:
        parts += [c.get("prefix") or "", c.get("boundary") or "", c.get("pas") or ""]
    return " ".join(parts).casefold()


def search(text: str, list_name: str | None = None, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
    """Records whose code, name, attributes, prefixes or boundaries contain every word of text.
    Returns (up to limit matches, total matches)."""
    words = [w for w in re.split(r"\s+", text.casefold().strip()) if w]
    if not words:
        return [], 0
    hits = [
        _with_list(n, r)
        for n, ol in lists().items()
        if list_name in (None, n)
        for r in ol.records
        if all(w in _text(r) for w in words)
    ]
    return hits[:limit], len(hits)


def codes_for(dxcc: int, pas: str | None = None) -> list[dict[str, Any]]:
    """Codes whose published entry covers this DXCC entity (and subdivision, if given).

    With pas, a cover names that subdivision, or names the entity with no subdivision
    (the whole entity, or a part described only by its boundary). Each match carries
    the covers that matched, with the owner's boundary wording."""
    want = pas.strip().upper() if pas else None
    out = []
    for n, ol in lists().items():
        for r in ol.records:
            hit = [
                c for c in r["covers"]
                if c.get("dxcc") == dxcc and (want is None or c.get("pas") in (None, want))
            ]
            if hit:
                out.append({"list": n, "code": r["code"], "name": r.get("name"),
                            "covers": hit, "source": r["source"]})
    return out


def valid_on(code: str, on: date) -> list[dict[str, Any]]:
    """Whether each record with this code was valid on a date.

    A record with no valid_from / valid_to has no published validity window: valid."""
    out = []
    for r in lookup(code):
        start = date.fromisoformat(r["valid_from"]) if r.get("valid_from") else None
        end = date.fromisoformat(r["valid_to"]) if r.get("valid_to") else None
        ok = (start is None or start <= on) and (end is None or on <= end)
        out.append({
            "list": r["list"], "code": r["code"], "valid": ok,
            "valid_from": r.get("valid_from"), "valid_to": r.get("valid_to"),
            "replaced_by": r.get("replaced_by"), "source": r["source"],
        })
    return out
