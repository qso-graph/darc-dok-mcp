#!/usr/bin/env python3
"""Transcribe DARC's DOK-Liste (published/DOK-Liste.pdf) into facts/darc_dok.json, once.

The DOK-Liste is a table in a PDF (DOK, Distrikt, Ortsverband, Bemerkungen). This reads it
with pypdf's layout mode, which prints each row's wrapped remark from the row's own line on:
the cells after the DOK are the district, then the club, then the remark, and a cell that
starts in the Bemerkungen column (from each page's header) is a remark. A line with no DOK
continues the remark above. The result is committed and reviewed; the tests check every row
against the PDF's reading-order text (planning/QSO-GRAPH-REFERENCE-DATA.md decision 7).

Run again only when DARC publishes a new DOK-Liste:  uv run python scripts/transcribe_dok_list.py
Build tooling only (pypdf is a dev dependency).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "darc_dok_mcp" / "data"
PDF = ROOT / "published" / "DOK-Liste.pdf"  # fetched by scripts/fetch_published.py
OUT = DATA / "facts" / "darc_dok.json"

ROW = re.compile(r"^([A-Z]\d\d)\s")
CHUNK = re.compile(r"\S+(?: \S+)*")  # runs separated by two or more spaces
MERGED = re.compile(r"\b(?:zu|jetzt) ([A-Z]\d\d)\b")  # merged into, or now


def pages() -> list[str]:
    return [p.extract_text(extraction_mode="layout") for p in PdfReader(PDF).pages]


def transcribe() -> list[dict]:
    records: list[dict] = []
    for pno, page in enumerate(pages(), 1):
        cols = None
        for line in page.splitlines():
            if line.startswith("DOK ") and "Distrikt" in line:
                cols = {k: line.index(k) for k in ("Distrikt", "Ortsverband", "Bemerkungen")}
                continue
            if cols is None or not line.strip():
                continue
            if line.lstrip().startswith(("DARC Referat", "http", "DOK-Liste", "von Karsten")):
                continue
            m = ROW.match(line)
            chunks = [(c.start(), c.group()) for c in CHUNK.finditer(line)]
            if m:
                fields = {"Distrikt": None, "Ortsverband": None, "Bemerkungen": None}
                order = ["Distrikt", "Ortsverband", "Bemerkungen"]
                for start, text in chunks[1:]:
                    if start >= cols["Bemerkungen"] - 4:
                        col = "Bemerkungen"
                    else:
                        col = next(k for k in order if fields[k] is None)
                    fields[col] = text if fields[col] is None else fields[col] + " " + text
                records.append({"code": m.group(1), "page": pno, **fields})
            elif records and chunks and chunks[0][0] >= cols["Bemerkungen"] - 4:
                prev = records[-1]
                cont = " ".join(t for _, t in chunks)
                prev["Bemerkungen"] = cont if prev["Bemerkungen"] is None else prev["Bemerkungen"] + " " + cont
            else:
                raise SystemExit(f"page {pno}: unexpected line: {line!r}")
    return records


def main() -> None:
    rows = transcribe()
    out = []
    for r in rows:
        merged = MERGED.search(r["Bemerkungen"] or "")
        out.append({
            "code": r["code"],
            "name": r["Ortsverband"],
            "valid_from": None,
            "valid_to": None,
            "replaced_by": merged.group(1) if merged else None,
            "covers": [],
            "attributes": {"district": r["Distrikt"], "club": r["Ortsverband"],
                           "remarks": r["Bemerkungen"]},
            "source": f"DOK-Liste.pdf, page {r['page']}, DOK {r['code']}",
        })
    OUT.write_text(json.dumps({
        "list": "darc_dok",
        "owner": "Deutscher Amateur-Radio-Club e.V. (DARC), DX-Referat (list by Karsten Radwan, DL2ABM)",
        "document": "DOK-Liste.pdf",
        "edition": "2016-12-26",
        "records": out,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out)} DOKs, {sum(1 for r in out if r['replaced_by'])} with replaced_by")


if __name__ == "__main__":
    main()
