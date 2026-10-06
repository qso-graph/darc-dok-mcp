"""DARC DOKs and special DOKs as DARC publishes them, with validity windows."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

try:
    _pkg_version = version("darc-dok-mcp")
except PackageNotFoundError:  # local dev / editable installs without dist metadata
    _pkg_version = "0.0.0-dev"

__version__: Final[str] = _pkg_version

# The owner's edition this package serves (data/SOURCE.json). Reported by get_version_info.
__spec_version__: Final[str] = "darc-dok-2016-12-26"
