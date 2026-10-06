# Reading DARC's DOK lists

Neither list is included (they are DARC's): `data/SOURCE.json` records their URLs and SHA-256s, and
`scripts/fetch_published.py` fetches them into `published/` (not committed) for the build and the
`--live` tests. The facts the tools answer from are in `data/facts/`, each record citing its page or
row.

## DOK-Liste (`darc_dok.json`, 1,192 DOKs, 25 districts)

DARC DX-Referat's **DOK-Liste** by Karsten Radwan, DL2ABM, dated 26.12.2016
(<https://www.darc.de/fileadmin/filemounts/referate/dx/DOK-Liste.pdf>), is a 21-page table: DOK,
Distrikt, Ortsverband, Bemerkungen.

It was read once by `scripts/transcribe_dok_list.py`, using pypdf's layout mode, and the result is
committed and reviewed:
- The cells after a DOK are the district, then the local club, then the remark. A cell that starts in
  the Bemerkungen column is a remark, so a row with no club (a dissolved DOK) is read correctly.
- A remark that wraps continues from the row's own line. pypdf's layout mode prints it that way.
  (Poppler's `pdftotext -layout` centres a wrapped cell vertically, printing its first line *above*
  the row, which attaches it to the wrong DOK. That was caught by the tests and is why pypdf is used.)
- `replaced_by` is set only where the remark itself names the successor: "… 2001 zu A12" (merged into)
  or "jetzt F76" (now). 12 DOKs have one. Other history ("bis 1961 Augsburg (wurde T01)", the club's
  earlier name and where that name went) stays in the remark as published.
- Every DOK has `covers` empty: the list doesn't tie a DOK to an ADIF subdivision.

Tests check every row against the PDF's own reading-order text: each DOK, district, club and remark
appears, and each remark sits between its own DOK and the next.

**Open:** whether DARC publishes a newer regular DOK list than this 2016 PDF.

## Special DOKs (`darc_special_dok.json`, 6,238 rows)

DARC SDOK-Referat's **SDOK_List.csv**
(<https://www.darc.de/fileadmin/filemounts/referate/sdok/SDOK_List.csv>): `;`-separated, Latin-1, six
columns: DOK; purpose; callsign; valid from; valid to; sponsoring club's DOK.

It is machine-readable, so the build reads it every time (`scripts/package_build.py`); the facts are
never edited by hand. One record per row: a special DOK issued more than once (different callsigns or
periods) has one record per row.
- Dates are DARC's `dd.mm.yy`, read as 19yy for yy ≥ 50 and 20yy below. The list runs 1957–2027. The
  published text is also kept in `attributes` (`valid_from_published`, `valid_to_published`).
- An empty "valid to" means DARC published no end date: the record has `valid_to` null.
- Values are kept as published. For example, `1000ER` runs 01.06.02 to 02.06.31; it is read as 2031,
  as written.
