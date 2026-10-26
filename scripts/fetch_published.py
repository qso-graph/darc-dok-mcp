#!/usr/bin/env python3
"""Fetch the owner's published file(s) into published/ (not shipped, not committed) and check them.

    python scripts/fetch_published.py

The owner's files are the owner's: this package never redistributes them. data/SOURCE.json
records each file's URL, retrieval date and SHA-256; this fetches the files for the build and
the tests.

Two different things can go wrong, and they used to look identical:

* **The download did not arrive whole.** That is a failure here, and it must not be mistaken for
  the owner editing their document. On 2026-10-26 itu-zones-mcp's release failed this way: the
  IARU handbook arrived truncated, pypdf reported "Stream has ended unexpectedly", and the
  SHA-256 warning invited an operator to "record the new SHA-256" -- which would have written a
  truncated file's hash into this package as its provenance, after which the check would have
  passed on garbage forever. Both upstreams were serving correctly at the time; only the transfer
  was broken.
* **The owner's document changed.** That stays a warning rather than a failure, because owners'
  websites change menus and markup without changing the list. Whether our facts are still in the
  document is what the pre-release tests check (planning/QSO-GRAPH-REFERENCE-DATA.md §8).
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED = ROOT / "published"
AGENT = "qso-graph reference-data check (https://qso-graph.io)"


class IncompleteDownload(RuntimeError):
    """The transfer failed. Not the same thing as the owner changing their file."""


def _download(url: str, dest: Path) -> None:
    """Fetch url to dest, refusing anything that did not arrive whole.

    Written to a .part file and moved into place only once verified, so a bad transfer never
    becomes the cached file that later runs and later tests read.
    """
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:  # https only, from SOURCE.json
        declared = resp.headers.get("Content-Length")
        body = resp.read()

    if not body:
        raise IncompleteDownload("the response was empty")
    if declared is not None and len(body) != int(declared):
        raise IncompleteDownload(
            f"got {len(body)} bytes, the server said {int(declared)}"
        )
    # A PDF that does not start with %PDF- is an error page or a partial transfer, not a
    # revised document. Checked by magic bytes rather than Content-Type, which a
    # misconfigured server will happily state wrongly.
    if dest.suffix.lower() == ".pdf" and not body.startswith(b"%PDF-"):
        raise IncompleteDownload(
            f"not a PDF: begins {body[:8]!r}"
        )

    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(body)
    tmp.replace(dest)


def source() -> dict:
    pkg = next(p for p in (ROOT / "src").iterdir() if (p / "data" / "SOURCE.json").exists())
    return json.loads((pkg / "data" / "SOURCE.json").read_text(encoding="utf-8"))


def fetch(name: str, meta: dict) -> Path:
    """The owner's file, fetched once into published/, checked against its SHA-256."""
    path = PUBLISHED / name
    if not path.exists():
        PUBLISHED.mkdir(exist_ok=True)
        try:
            _download(meta["url"], path)
        except (IncompleteDownload, OSError, urllib.error.URLError) as exc:
            # A gate, not a warning: nothing downstream can be checked against a document
            # that did not arrive. Deliberately says not to record a hash.
            sys.exit(
                f"{name}: download failed -- {exc}\n"
                f"  {meta['url']}\n"
                f"  This is a transfer failure, not the owner changing their document. "
                f"Do NOT record a new SHA-256. Re-run; if it persists, fetch the URL by hand "
                f"and compare."
            )
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != meta["sha256"]:
        # Provenance, not a gate: websites change menus and markup without changing the list.
        # The pre-release check that matters is that our facts are still in the document.
        # Reaching here means the file arrived whole and still hashes differently, so the
        # owner's document really did change.
        print(f"::warning title=Owner file changed::{name}: SHA-256 {got[:16]}... is not the "
              f"{meta['sha256'][:16]}... read on {meta['retrieved']}. The file arrived whole, "
              f"so the document changed. Check the facts still match, then record the new "
              f"SHA-256 ({meta['url']}). To re-fetch, delete published/{name}")
    return path


def main() -> None:
    for name, meta in source()["published"].items():
        if not meta["url"].startswith("https://"):
            sys.exit(f"{name}: not an https URL")
        print(f"ok  {fetch(name, meta).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
