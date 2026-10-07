#!/usr/bin/env python3
"""Fetch the owner's published file(s) into published/ (not shipped, not committed) and check them.

    python scripts/fetch_published.py

The owner's files are the owner's: this package never redistributes them. data/SOURCE.json
records each file's URL, retrieval date and SHA-256; this fetches the files for the build and
the tests. A different SHA-256 is a warning, not a failure: owners' websites change menus and
markup without changing the list. Whether our facts are still in the document is checked by the
pre-release tests (planning/QSO-GRAPH-REFERENCE-DATA.md §8).
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED = ROOT / "published"
AGENT = "qso-graph reference-data check (https://qso-graph.io)"


def source() -> dict:
    pkg = next(p for p in (ROOT / "src").iterdir() if (p / "data" / "SOURCE.json").exists())
    return json.loads((pkg / "data" / "SOURCE.json").read_text(encoding="utf-8"))


def fetch(name: str, meta: dict) -> Path:
    """The owner's file, fetched once into published/, checked against its SHA-256."""
    path = PUBLISHED / name
    if not path.exists():
        PUBLISHED.mkdir(exist_ok=True)
        req = urllib.request.Request(meta["url"], headers={"User-Agent": AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp:  # https only, from SOURCE.json
            path.write_bytes(resp.read())
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != meta["sha256"]:
        # Provenance, not a gate: websites change menus and markup without changing the list.
        # The pre-release check that matters is that our facts are still in the document.
        print(f"::warning title=Owner file changed::{name}: SHA-256 {got[:16]}... is not the "
              f"{meta['sha256'][:16]}... read on {meta['retrieved']}. Check the facts still match, "
              f"then record the new SHA-256 ({meta['url']})")
    return path


def main() -> None:
    for name, meta in source()["published"].items():
        if not meta["url"].startswith("https://"):
            sys.exit(f"{name}: not an https URL")
        print(f"ok  {fetch(name, meta).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
