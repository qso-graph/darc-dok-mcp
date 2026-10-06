"""This package's part of scripts/build.py: what it reads and what it derives."""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import date
from pathlib import Path

SDOK = "SDOK_List.csv"
FACTS = "darc_special_dok.json"


def _date(text: str) -> tuple[str | None, str | None]:
    """DARC's dd.mm.yy as an ISO date; yy >= 50 is 19yy, below is 20yy (the list runs 1957-2027).
    Returns (iso, note)."""
    text = text.strip()
    if not text:
        return None, None
    try:
        d, m, y = (int(p) for p in text.split("."))
        return date(1900 + y if y >= 50 else 2000 + y, m, d).isoformat(), None
    except ValueError:
        return None, f"date {text!r} as published could not be read"


def special_doks(data: Path) -> dict:
    """DARC's special-DOK CSV (';'-separated, Latin-1), one record per row, read as published:
    DOK; purpose; callsign; valid from; valid to; sponsoring club's DOK."""
    raw = (data / "published" / SDOK).read_bytes().decode("latin-1")
    records = []
    for n, row in enumerate(csv.reader(io.StringIO(raw), delimiter=";"), 1):
        if len(row) != 6:
            sys.exit(f"{SDOK} row {n}: expected 6 columns, got {len(row)}")
        code, purpose, call, start, end, club = (c.strip() for c in row)
        vf, n1 = _date(start)
        vt, n2 = _date(end)
        notes = [x for x in (n1, n2) if x]
        if vf and vt and vt < vf:
            notes.append("valid to is before valid from, as published")
        rec = {
            "code": code, "name": purpose or None, "valid_from": vf, "valid_to": vt,
            "replaced_by": None, "covers": [],
            "attributes": {"purpose": purpose or None, "callsign": call or None,
                           "valid_from_published": start or None, "valid_to_published": end or None,
                           "club_dok": club or None},
            "source": f"{SDOK}, row {n}",
        }
        if notes:
            rec["transcription_note"] = "; ".join(notes)
        records.append(rec)
    return {"list": "darc_special_dok",
            "owner": "Deutscher Amateur-Radio-Club e.V. (DARC), SDOK-Referat",
            "document": SDOK, "edition": "as retrieved (DARC updates it continually)",
            "records": records}


def read_published(data: Path, source: dict, write: bool) -> None:
    """The special-DOK list is DARC's own CSV, so the build reads it (decision 7): facts are
    regenerated from published/ each build, never edited by hand."""
    text = json.dumps(special_doks(data), indent=2, ensure_ascii=False) + "\n"
    out = data / "facts" / FACTS
    if write:
        out.write_text(text, encoding="utf-8")
    elif not out.exists() or out.read_text(encoding="utf-8") != text:
        sys.exit(f"facts/{FACTS} is stale: run scripts/build.py")


def derived(source: dict, facts: dict[str, dict]) -> dict[str, dict]:
    """derived/by_district.json: DARC district -> its DOKs. Ours, built from the facts."""
    by: dict[str, list[str]] = {}
    for r in facts["darc_dok.json"]["records"]:
        by.setdefault(r["attributes"]["district"] or "?", []).append(r["code"])
    return {"by_district.json": {
        "_about": "Derived by this package, not published by DARC: each district in DARC's "
                  "DOK-Liste and the DOKs listed under it, built from facts/darc_dok.json.",
        "derived_from": "facts/darc_dok.json",
        "edition": "2016-12-26",
        "districts": dict(sorted(by.items())),
    }}
