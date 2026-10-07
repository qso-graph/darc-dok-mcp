# Changelog

All notable changes to `darc-dok-mcp` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-10-07

- CI: DARC's files are fetched and checked only on the release PR (develop → main); the row-by-row checks against them are the gate. A changed SHA-256 is now a warning, not a failure.
- `load.sql` says in the database that the owner is the authority for this list: where ADIF's tables also carry a value for it, this schema is the answer (qso-graph-devel#56).

## [0.1.0] — 2026-10-06

- First release: DARC's DOK lists, as published and credited, with the shared QG Reference tools
  (`source_info`, `lookup`, `search`, `codes_for`, `valid_on`) and `get_version_info`.
