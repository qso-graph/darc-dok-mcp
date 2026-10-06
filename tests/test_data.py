"""The data: the owner's files recorded (not shipped), the facts valid and cited, ADIF's codes, the build current."""

from __future__ import annotations

import json
import runpy
import sys
from functools import cache
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from darc_dok_mcp import reference

ROOT = Path(__file__).resolve().parent.parent
DATA = files("darc_dok_mcp").joinpath("data")
SOURCE = reference.source()


@cache
def adif() -> tuple[set[int], set[tuple[str, int]]]:
    """ADIF 3.1.7's DXCC entity codes and (subdivision, entity) pairs, from adif-mcp's copy."""
    spec = files("adif_mcp").joinpath("resources", "spec", "317")
    ent = json.loads(spec.joinpath("enumerations_dxcc_entity_code.json").read_text(encoding="utf-8"))
    pas = json.loads(spec.joinpath("enumerations_primary_administrative_subdivision.json").read_text(encoding="utf-8"))
    dxcc = {int(r["Entity Code"]) for r in ent["Adif"]["Enumerations"]["DXCC_Entity_Code"]["Records"].values()}
    subs = {(r["Code"], int(r["DXCC Entity Code"]))
            for r in pas["Adif"]["Enumerations"]["Primary_Administrative_Subdivision"]["Records"].values()
            if r.get("Deleted") != "true"}
    return dxcc, subs


def test_owner_files_are_recorded_not_shipped():
    """The owner's files are referenced by URL and SHA-256, never shipped (NOTICE)."""
    assert not DATA.joinpath("published").is_dir()
    for meta in SOURCE["published"].values():
        assert meta["url"].startswith("https://") and meta["retrieved"]
        assert len(meta["sha256"]) == 64


@pytest.mark.live
def test_owner_files_still_match_their_sha256():
    """Fetch each owner file and compare: a mismatch means the owner published a change."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import fetch_published

    for name, meta in SOURCE["published"].items():
        fetch_published.fetch(name, meta)


def test_source_credits_the_owner():
    for key in ("owner", "document_title", "edition", "url", "terms", "authority"):
        assert SOURCE[key], key


@pytest.mark.parametrize("name", SOURCE["facts"])
def test_facts_match_the_shared_schema(name):
    schema = json.loads(DATA.joinpath("owner-list.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(json.loads(DATA.joinpath("facts", name).read_text(encoding="utf-8")), schema)


def test_every_record_cites_the_owners_document():
    docs = tuple(SOURCE["published"])
    for ol in reference.lists().values():
        assert ol.records
        for r in ol.records:
            assert r["source"].startswith(docs), r


def test_covers_use_adif_codes():
    dxcc, subs = adif()
    for ol in reference.lists().values():
        for r in ol.records:
            for c in r["covers"]:
                if c["dxcc"] is not None:
                    assert c["dxcc"] in dxcc, (r["code"], c)
                if c["pas"] is not None:
                    assert (c["pas"], c["dxcc"]) in subs, (r["code"], c)


def test_build_is_current(monkeypatch):
    """derived/ and load.sql are what scripts/build.py makes from facts/ (and facts read
    from a machine-readable published file are what the build reads)."""
    monkeypatch.setattr(sys, "argv", ["build.py", "--check"])
    runpy.run_path(str(ROOT / "scripts" / "build.py"), run_name="__main__")


def test_derived_files_say_they_are_ours():
    for p in DATA.joinpath("derived").iterdir():
        d = json.loads(p.read_text(encoding="utf-8"))
        assert "not published by" in d["_about"] and d["derived_from"].startswith("facts/")


def test_load_sql_needs_adif_first_and_cites_the_source():
    sql = DATA.joinpath("load.sql").read_text(encoding="utf-8")
    assert "PREREQUISITE" in sql and "REFERENCES adif.dxcc_entity_code" in sql
    assert f"CREATE TABLE {SOURCE['schema']}.source" in sql
