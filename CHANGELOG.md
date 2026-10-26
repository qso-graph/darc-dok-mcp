# Changelog

All notable changes to `darc-dok-mcp` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] — 2026-10-26

### Changed

- `--transport streamable-http` now says where it bound, and the help text says
  it too. It binds `127.0.0.1`, and FastMCP takes no host option, so it was
  never reachable from another machine or from outside a container — and nothing
  said so. The bind address is unchanged: loopback-only is deliberate for a
  server that holds credentials and has no authentication of its own.

## [0.2.1] — 2026-10-26

- A release should appear on the Releases page
- Move every Node 20 action to its first Node 24 major
- The locked-dependency audit blocked every release
- Four upgrades arrived as 57 pull requests
- Nothing was auditing the lockfile
- Close every open security advisory in the lockfile
- A release is a workflow, not a merge
- Bump certifi from 2026.7.22 to 2026.10.19

## [0.2.0] — 2026-10-25

**Upgrading:** a tool that rejects your input now returns `isError: true` instead of a successful
result whose payload carried an `error` key. Anything reading `result["error"]` should read the
error flag instead. DARC's credit is no longer attached to a rejection — it is still on every
answer that carries data, including a "not found", which is where attribution belongs.

### MCP specification 2026-07-28 (#15)

- **Tool errors are flagged `isError`.** `_err` built `{"error": msg, "source": _credit()}` and six
  call sites returned it, so on the wire a refusal arrived as a *successful* result. It raises
  `ToolError` now, typed `NoReturn` so the checker understands control flow ends there.
- **All six tools declare the four annotation hints**, sharing one block because every tool answers
  from the DOK data carried in the wheel. `TestOneBlockIsCorrectHere` asserts that premise — no
  sockets, no writes, the data shipped — rather than the convenience.
- **`idempotentHint: true` needed thinking about here, not copying.** DARC's special DOKs carry real
  validity windows, so `darc_dok_valid_on` genuinely gives different answers on different dates.
  That is the argument changing, not the tool: the hint is about the tool changing nothing.
  `TestValidityIsRealHere` holds it, and first proves the data really does carry windows, so the
  test cannot pass vacuously.
- **A test of mine was wrong and the code was right.** `valid_on` *annotates* rather than filters: a
  code outside its window comes back `found: true` with `valid: false`. Collapsing those would make
  "DARC lists no such DOK" and "that DOK was not valid then" indistinguishable, which is a worse
  answer than either. The contract is pinned now, because the simplification is tempting.
- **Two source documents, not one**, unlike this server's siblings: DARC publishes the DOK-Liste as a
  PDF and `SDOK_List.csv` through a different department. `DK-C12` and `DK-C42` check both are
  carried and both are reported with a URL and a SHA-256.
- `tests/test_mcp_conformance.py` (DK-C01 onward, 17 tests), and `test_bad_input_is_an_error`
  renamed `test_bad_input_is_a_flagged_error`, asserting the flag rather than the word.
- **Every check falsified — 13 of 13** — including the two about DARC's second document and the one
  about the validity window.
- **Nothing moved on the wire but the annotations.** Every tool's name, description, `inputSchema`
  and `outputSchema` dumped through a real `fastmcp.Client` before and after: byte-identical.

### Lint (#14, qso-graph-devel#70)

- **`E501` is adopted.** It reported **27 lines** and not one was a defect — the finding, not an
  argument against enforcing it.
- **The exemption this issue was filed for is not needed.** The title says the publisher-name lines
  are "explicitly exempt", and the deferral note in `pyproject.toml` said six such lines "will not
  be reflowed at all". Measured: **four** lines name ADIF's `Primary_Administrative_Subdivision` or
  `DXCC_Entity_Code`, and all four reflow with the field name whole — bind the subscript chain to a
  name first and `subdivisions = pas["Adif"]["Enumerations"]["Primary_Administrative_Subdivision"]`
  is 83 characters. **Zero exemptions**; there is no `# noqa: E501` in the repo. That prediction has
  now failed in all three owner-list servers it was written about.
- **Four tool descriptions change on the wire, in whitespace only.** `source_info`, `lookup`,
  `codes_for` and `valid_on` had summary lines over 95 columns, and FastMCP publishes the docstring
  as the description — so reflowing one reaches a client. Checked rather than assumed: with
  whitespace normalised all four are identical, **no words changed**, and every `inputSchema`,
  `outputSchema` and annotation block is byte-identical.
- The server's `instructions` string came out **byte-identical**: it is a run of adjacent literals,
  so splitting it at word boundaries changes the source and not the value.
- Falsified: a long line planted in `src/` and another in `tests/`, both caught.

### Not applicable here

- **No `certifi` work and no issue for it** (qso-graph-devel#73). Nothing in the package makes an
  outbound call of any kind; DARC's two files are referenced by URL and SHA-256 and the facts taken
  from them ship as data. `DK-C10` keeps it that way.
- **Provenance checked, unprompted.** Both files re-fetched with the cache cleared first:
  `DOK-Liste.pdf` still hashes `e853684c…` and `SDOK_List.csv` `da5e65b3…`, matching `SOURCE.json`.
  Checked because `cq-zones-mcp`'s release was blocked by exactly this.

## [0.1.2] — 2026-10-11

- **ruff and mypy run in CI** (qso-graph-devel#66), as a job the `ci-all-green` gate requires.
  Settings follow `adif-mcp`, the reference for every qso-graph Python repo.
- **Fixed: a dataclass field named `list` made every annotation after it wrong.** `OwnerList.list`
  shadowed the builtin inside the class body, so `records: list[dict[str, Any]]` resolved to that
  field subscripted rather than to the builtin — as did `by_code`. Nothing broke at run time,
  because `from __future__ import annotations` means the strings are never evaluated, but anything
  that resolves them saw the wrong type. The field is `list_name` now, which is what `search()`
  already called the same thing; the `"list"` key in tool output is unchanged, being the published
  field name. Found by mypy, which is the argument for having it.
- `source()` no longer returns `Any` from a function promising a dict, and `mcp.run` is given the
  literal fastmcp asks for rather than a `str` that happens to hold the right word.
- `E501` is deferred rather than adopted (qso-graph-devel#70): the lines it reports here are not
  defects, and some are long because they name a publisher's field exactly.
- **`fastmcp` is bounded: `>=4.0,<5`** (qso-graph-devel#60). It was `>=3.0` with no upper bound, and
  these servers are run with `uvx`, which resolves fresh — so a `fastmcp` 5.0 would have reached
  every user automatically, before anything here had been run against it. The floor rises to 4.0
  because that is what is actually tested: every lock in the fleet held a 4.x, and nothing in CI
  has ever exercised 3.x. A claim of 3.x support that no test backs is not support.
- `fastmcp` is locked at 4.1.0, the current release, so CI runs against what a new install gets.
- **The published contact is `maintainers@qso-graph.io`** (qso-graph-devel#69). The `authors` field
  carried a personal address, and that field is what PyPI shows on the package page. Everything in
  qso-graph is open source and open to contribution, so the contact is the project's.

## [0.1.1] — 2026-10-07

- CI: DARC's files are fetched and checked only on the release PR (develop → main); the row-by-row checks against them are the gate. A changed SHA-256 is now a warning, not a failure.
- `load.sql` says in the database that the owner is the authority for this list: where ADIF's tables also carry a value for it, this schema is the answer (qso-graph-devel#56).

## [0.1.0] — 2026-10-06

- First release: DARC's DOK lists, as published and credited, with the shared QG Reference tools
  (`source_info`, `lookup`, `search`, `codes_for`, `valid_on`) and `get_version_info`.
