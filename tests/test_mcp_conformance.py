"""Conformance with the Model Context Protocol, revision 2026-07-28.

We documented how to *publish* an MCP server in detail and never wrote down what makes
one *valid*, which is how missing ``isError`` and missing annotations reached every
server in the fleet.

This is the third owner-list server, after cq-zones-mcp and itu-zones-mcp, and the
temptation is to assume the siblings' premises hold. They are asserted here instead,
because two things about this repo are genuinely different:

* **Two source documents, not one.** DARC publishes the DOK-Liste as a PDF and the
  special-DOK list as a CSV, from two different departments. ``source_info`` therefore
  reports two files, and ``TestAttributionSurvives`` checks the credit names the owner
  rather than one document.

* **``valid_on`` answers a real question here.** In itu-zones-mcp the tool exists only so
  every owner-list server answers the same questions — the chapter publishes no validity
  window. DARC's special DOKs carry real windows, so the same code gives different
  answers on different dates. ``TestValidityIsRealHere`` holds that, and it is the reason
  ``idempotentHint`` needs a sentence of its own: the argument changes, not the tool.

Test IDs: DK-C01 onward.
"""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from darc_dok_mcp import server

ANNOTATION_HINTS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")

TOOLS = {
    "get_version_info", "darc_dok_source_info", "darc_dok_lookup", "darc_dok_search",
    "darc_dok_codes_for", "darc_dok_valid_on",
}


def _tools() -> dict[str, object]:
    return {t.name: t for t in asyncio.run(server.mcp.list_tools())}


def _wire(tool: object) -> dict[str, object]:
    annotations = getattr(tool, "annotations", None)
    assert annotations is not None, "tool declares no annotations"
    return annotations.model_dump(by_alias=True, exclude_none=True)


def call(name: str, args: dict | None = None):
    async def go():
        async with Client(server.mcp) as c:
            return (await c.call_tool(name, args or {})).data
    return asyncio.run(go())


def fails(name: str, args: dict | None = None) -> str:
    with pytest.raises(ToolError) as caught:
        call(name, args)
    return str(caught.value)


class TestToolAnnotations:
    def test_every_tool_declares_all_four_hints(self) -> None:
        """DK-C01: the defaults are pessimistic, so silence is the wrong answer."""
        for name, tool in _tools().items():
            wire = _wire(tool)
            for hint in ANNOTATION_HINTS:
                assert hint in wire, f"{name} omits {hint}; got {sorted(wire)}"

    def test_all_six_are_read_only_closed_world_and_idempotent(self) -> None:
        """DK-C02: one answer for all six, because one reason covers all six."""
        for name, tool in _tools().items():
            wire = _wire(tool)
            assert wire["readOnlyHint"] is True, name
            assert wire["destructiveHint"] is False, name
            assert wire["idempotentHint"] is True, name
            assert wire["openWorldHint"] is False, name


class TestOneBlockIsCorrectHere:
    """Sharing one block is only honest while the premise holds, so assert the premise."""

    def test_no_module_in_the_package_opens_a_socket(self) -> None:
        """DK-C10: `openWorldHint: false` on all six depends on this.

        DARC's two files are referenced by URL and SHA-256 in SOURCE.json, not fetched at
        runtime — the facts taken from them ship as data.
        """
        import pathlib

        src = pathlib.Path(server.__file__).parent
        offenders = [
            f"{py.name}:{i}: {line.strip()}"
            for py in src.rglob("*.py")
            for i, line in enumerate(py.read_text().splitlines(), 1)
            if any(t in line for t in ("urlopen", "http.client", "socket.",
                                       "requests.", "httpx."))
        ]
        assert not offenders, (
            "something here reaches the network, so openWorldHint: false is wrong:\n"
            + "\n".join(offenders)
        )

    def test_nothing_in_the_package_writes(self) -> None:
        """DK-C11: `readOnlyHint: true` on all six depends on this."""
        import pathlib

        src = pathlib.Path(server.__file__).parent
        offenders = [
            f"{py.name}:{i}: {line.strip()}"
            for py in src.rglob("*.py")
            for i, line in enumerate(py.read_text().splitlines(), 1)
            if any(t in line for t in ("write_text(", ".write(", "mkdir("))
        ]
        assert not offenders, (
            "something here writes, so readOnlyHint: true is wrong:\n" + "\n".join(offenders)
        )

    def test_both_of_darcs_documents_ship_in_the_wheel(self) -> None:
        """DK-C12: two source documents, so check the data for both is carried."""
        from darc_dok_mcp import reference

        assert reference.DATA.joinpath("SOURCE.json").is_file()
        published = reference.source()["published"]
        assert len(published) == 2, f"expected two DARC documents, got {sorted(published)}"


class TestBadInputIsFlagged:
    def test_every_validation_path_raises(self) -> None:
        """DK-C20: all six `_err` call sites, not a sample of them."""
        for name, args in (
            ("darc_dok_lookup", {"code": "A B; DROP"}),
            ("darc_dok_search", {"text": "x" * 101}),
            ("darc_dok_codes_for", {"dxcc": 5000}),
            ("darc_dok_codes_for", {"dxcc": 1, "subdivision": "TOOLONG"}),
            ("darc_dok_valid_on", {"code": "A B; DROP", "on_date": "2026-10-06"}),
            ("darc_dok_valid_on", {"code": "A01", "on_date": "06.10.2026"}),
        ):
            fails(name, args)

    def test_the_message_says_what_was_wrong(self) -> None:
        """DK-C21: a flagged error the caller cannot act on is only half the fix."""
        assert "1 to 100" in fails("darc_dok_search", {"text": "x" * 101})
        assert "YYYY-MM-DD" in fails(
            "darc_dok_valid_on", {"code": "A01", "on_date": "06.10.2026"})

    def test_no_error_payload_remains_in_the_source(self) -> None:
        """DK-C22: the conversion is complete, not partial.

        Reads the parse tree for a dict literal with an ``"error"`` key. A raw-line search
        matches ``_err``'s own docstring, which quotes the old shape; stripping string
        literals to fix that deletes the payload key as well, since the key *is* a string
        literal — a version that shipped in cq-zones-mcp 0.2.0 and could never fail.
        """
        import ast
        import pathlib

        src = pathlib.Path(server.__file__).parent
        offenders = [
            f"{py.name}:{node.lineno}"
            for py in src.rglob("*.py")
            for node in ast.walk(ast.parse(py.read_text()))
            if isinstance(node, ast.Dict)
            and any(isinstance(k, ast.Constant) and k.value == "error" for k in node.keys)
        ]
        assert not offenders, f"error payloads remain at: {offenders}"


class TestValidityIsRealHere:
    """Why `idempotentHint: true` needed thinking about rather than copying.

    itu-zones-mcp's `valid_on` exists only so every owner-list server answers the same
    questions: its chapter publishes no validity window, so every zone is always valid.
    DARC's special DOKs carry real windows, so the same code genuinely differs by date.
    """

    def test_a_special_dok_is_outside_its_window_on_some_date(self) -> None:
        """DK-C30: the data really does carry windows, not just a column for them."""
        from darc_dok_mcp import reference

        windowed = [
            r for ol in reference.lists().values() for r in ol.records
            if r.get("valid_from") or r.get("valid_to")
        ]
        assert windowed, "no record carries a validity window; DK-C31 would prove nothing"

    def test_the_same_call_differs_by_date_and_that_is_still_idempotent(self) -> None:
        """DK-C31: the argument changes, not the tool.

        `idempotentHint` is about the tool changing nothing, not about the answer being
        constant. Recorded as a test because it is exactly the kind of thing a later
        reader would "correct" to false after noticing two dates disagree.
        """
        from darc_dok_mcp import reference

        windowed = next(
            r for ol in reference.lists().values() for r in ol.records
            if r.get("valid_from") and r.get("valid_to")
        )
        code = windowed["code"]
        inside = call("darc_dok_valid_on", {"code": code, "on_date": windowed["valid_from"]})
        outside = call("darc_dok_valid_on", {"code": code, "on_date": "1970-01-01"})

        # `found` and `valid` are two different answers, and the tool keeps them apart:
        # `found` says DARC lists this code at all, `valid` answers the date. The first
        # version of this test asserted `found is False` outside the window and failed on
        # 01ALT — my error, not the code's. Collapsing them would make "no such DOK" and
        # "that DOK was not valid then" indistinguishable, which is a worse answer than
        # either. Pinned here because the simplification is tempting.
        assert inside["found"] is True and outside["found"] is True, "the code exists either way"
        assert inside["records"][0]["valid"] is True, f"{code} on its own valid_from"
        assert outside["records"][0]["valid"] is False, f"{code} in 1970"
        assert _wire(_tools()["darc_dok_valid_on"])["idempotentHint"] is True


class TestAttributionSurvives:
    """DARC's credit was in the error payload; dropping it must not lose it."""

    def test_every_data_answer_carries_the_credit(self) -> None:
        """DK-C40: checked per tool, not assumed from one."""
        for name, args in (
            ("darc_dok_lookup", {"code": "A01"}),
            ("darc_dok_search", {"text": "a"}),
            ("darc_dok_codes_for", {"dxcc": 230}),
            ("darc_dok_valid_on", {"code": "A01", "on_date": "2026-10-06"}),
        ):
            answer = call(name, args)
            assert "source" in answer, f"{name} returns data with no attribution"
            assert answer["source"].get("owner"), f"{name} credit has no owner"

    def test_an_unknown_code_still_carries_the_credit(self) -> None:
        """DK-C41: "not found" is an answer, so it is attributed too."""
        answer = call("darc_dok_lookup", {"code": "ZZZ999"})
        assert answer["found"] is False
        assert answer["source"].get("owner")

    def test_source_info_names_both_of_darcs_files(self) -> None:
        """DK-C42: two departments, two documents, and the answer says so."""
        info = call("darc_dok_source_info")
        assert len(info["published_files"]) == 2
        for name, meta in info["published_files"].items():
            assert meta["url"].startswith("https://"), name
            assert len(meta["sha256"]) == 64, name


class TestAnEmptyAnswerIsNotAnError:
    def test_unknown_code_is_a_successful_call(self) -> None:
        """DK-C50: the distinction the specification draws."""
        answer = call("darc_dok_lookup", {"code": "ZZZ999"})
        assert isinstance(answer, dict)
        assert answer["found"] is False


class TestVersionInfoShape:
    def test_it_matches_the_shape_the_fleet_returns(self) -> None:
        """DK-C60: the convention that drifted because nobody asserted it."""
        info = call("get_version_info")
        assert info["service_name"] == "darc-dok-mcp"
        assert info["service_version"]
        assert info["spec_version"]


class TestRegistration:
    def test_the_names_a_client_sees_are_prefixed(self) -> None:
        """DK-C70: issue #15 lists the function names, not these."""
        assert set(_tools()) == TOOLS

    def test_the_module_attribute_is_not_the_registered_name(self) -> None:
        """DK-C71: the trap that follows from prefixing, pinned."""
        assert not hasattr(server, "darc_dok_lookup")
        assert hasattr(server, "lookup")
