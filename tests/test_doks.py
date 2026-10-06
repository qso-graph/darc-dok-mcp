"""DARC's DOK-Liste and special DOKs: checked against DARC's own files."""

from __future__ import annotations

import csv
import io
import re
from datetime import date
from functools import cache
from importlib.resources import files

from pypdf import PdfReader

from darc_dok_mcp import reference

PUB = files("darc_dok_mcp").joinpath("data", "published")


@cache
def pdf_text() -> str:
    with PUB.joinpath("DOK-Liste.pdf").open("rb") as fh:
        text = " ".join(p.extract_text() or "" for p in PdfReader(fh).pages)
    return re.sub(r"\s+", " ", text)


def doks():
    return reference.lists()["darc_dok"].records


def test_dok_list_rows():
    recs = doks()
    assert len(recs) == 1192 and len({r["code"] for r in recs}) == 1192
    assert all(re.fullmatch(r"[A-Z]\d\d", r["code"]) for r in recs)
    assert len({r["attributes"]["district"] for r in recs}) == 25


def test_every_dok_row_is_in_darcs_pdf():
    """Each DOK and its club, district and remarks appear in the PDF's own text."""
    text = pdf_text()
    missing = []
    for r in doks():
        a = r["attributes"]
        for value in (r["code"], a["district"], a["club"], a["remarks"]):
            if value and re.sub(r"\s+", " ", value) not in text:
                missing.append((r["code"], value))
    assert not missing, missing[:10]


def test_merged_doks_point_to_their_successor():
    assert reference.lookup("A49")[0]["replaced_by"] == "A12"
    assert all(reference.lookup(r["replaced_by"]) for r in doks() if r["replaced_by"])


def test_special_doks_are_darcs_csv_row_for_row():
    raw = PUB.joinpath("SDOK_List.csv").read_bytes().decode("latin-1")
    rows = list(csv.reader(io.StringIO(raw), delimiter=";"))
    recs = reference.lists()["darc_special_dok"].records
    assert len(recs) == len(rows)
    for row, r in zip(rows, recs):
        assert r["code"] == row[0].strip() and r["attributes"]["callsign"] == (row[2].strip() or None)
        assert r["attributes"]["valid_from_published"] == (row[3].strip() or None)


def test_a_special_dok_counts_only_inside_its_window():
    # 01ALT, DK0AI, 16.05.04 - 15.06.04 (row 1 of DARC's CSV)
    inside = reference.valid_on("01ALT", date(2004, 6, 1))
    outside = reference.valid_on("01ALT", date(2004, 7, 1))
    assert any(v["valid"] for v in inside) and not any(v["valid"] for v in outside)


def test_two_digit_years():
    co57 = reference.lookup("CO57")[0]
    assert co57["valid_from"] == "1957-08-02"
    assert reference.lookup("01ALT")[0]["valid_from"] == "2004-05-16"


def test_each_remark_belongs_to_its_own_row():
    """In the PDF's reading order a row reads 'DOK district club remarks', and the next row
    starts with the next DOK: each remark must sit between its own DOK and the next one."""
    text = pdf_text()
    recs = doks()
    starts = []
    for r in recs:
        i = text.find(f"{r['code']} {r['attributes']['district']}")
        assert i >= 0, r["code"]
        starts.append(i)
    assert starts == sorted(starts)
    for k, r in enumerate(recs):
        remarks = r["attributes"]["remarks"]
        if not remarks:
            continue
        end = starts[k + 1] if k + 1 < len(recs) else len(text)
        segment = text[starts[k]:end]
        assert all(part in segment for part in re.split(r"\s+", remarks)), (r["code"], remarks)
