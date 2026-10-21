#!/usr/bin/env python
"""
Extracts as much information as possible from a video file.
"""

import warnings
from typing import Any

from . import monkeypatch as _monkeypatch
from .__version__ import __version__
from .api import GuessItApi, guessit, json_schema, properties, schema, suggested_expected
from .options import ConfigurationException
from .rules.common.quantity import Size

__all__ = [
    "GUESSIT_SCHEMA",
    "ConfigurationException",
    "GuessItApi",
    "Size",
    "__version__",
    "guessit",
    "json_schema",
    "properties",
    "schema",
    "suggested_expected",
]


def __getattr__(name: str) -> Any:
    if name == "GUESSIT_SCHEMA":
        # Deprecated: kept for backward compatibility, scheduled for removal in a future
        # major release. It is the default-configuration snapshot; use schema() to obtain a
        # configuration-aware schema (schema() with no options returns the same mapping).
        from .schema_generated import GUESSIT_SCHEMA as _guessit_schema

        warnings.warn(
            "guessit.GUESSIT_SCHEMA is deprecated and will be removed in a future major release; "
            "use guessit.schema() instead (guessit.schema() with no options returns the same mapping).",
            DeprecationWarning,
            stacklevel=2,
        )
        return _guessit_schema
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_monkeypatch.monkeypatch_rebulk()
