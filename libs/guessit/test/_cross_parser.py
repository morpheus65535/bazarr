#!/usr/bin/env python
"""Shared helpers for the cross-parser tests (``test_cross_parser.py``).

The vendored datasets under ``guessit/test/cross_parser/*.json`` hold
(release_name -> expected guessit fields) pairs derived from other release-name
parsers (see ``scripts/import_cross_parser_tests.py``). Both the importer (when
it computes the ``baseline.json`` manifest of current disagreements) and the test
itself compare guessit's output against those expectations — they MUST use the
exact same comparison, otherwise a field could be baselined yet read as a
regression. That single comparison lives here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "cross_parser"
BASELINE_PATH = DATA_DIR / "baseline.json"

# ``\W`` is Unicode-aware for ``str``, so accented, Cyrillic, CJK… letters are
# kept (only punctuation/spacing is collapsed) — an ASCII-only class would erase
# whole non-Latin titles to "" and make every such comparison vacuously equal.
_TITLE_NON_WORD = re.compile(r"\W+")
_WS = re.compile(r"\s+")


def normalize_title(value: Any) -> str:
    """Case/punctuation-insensitive title key, so ``Mr. Robot`` == ``Mr Robot``."""
    text = _TITLE_NON_WORD.sub(" ", str(value).casefold())
    return _WS.sub(" ", text).strip()


def field_matches(result: dict[str, Any], field: str, expected: Any) -> bool:
    """Whether guessit's ``result`` satisfies one expected (field, value) pair."""
    got = result.get(field)
    if field == "title":
        return got is not None and normalize_title(got) == normalize_title(expected)
    if field == "year" and got is None:
        # guessit folds a full air date into `date` (no separate `year`); other
        # parsers only keep the year, so accept the date's year as a match.
        date = result.get("date")
        return date is not None and str(getattr(date, "year", None)) == str(expected)
    if field in ("season", "episode") and (isinstance(expected, list) or isinstance(got, list)):
        # compare as sets so a scalar and its single-element list are equal both ways
        got_set = set(got) if isinstance(got, list) else {got}
        expected_set = set(expected) if isinstance(expected, list) else {expected}
        return got_set == expected_set
    return str(got) == str(expected)


def iter_cases() -> list[tuple[str, str, dict[str, Any]]]:
    """Yield ``(source, release_name, expected)`` for every vendored entry."""
    out: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name == "baseline.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        source = doc.get("_source", path.stem)
        for entry in doc["entries"]:
            out.append((source, entry["release_name"], entry["expected"]))
    return out


def load_baseline() -> set[tuple[str, str, str]]:
    """Load the ``{parser: {release_name: [field, ...]}}`` manifest as a key set."""
    if not BASELINE_PATH.exists():
        return set()
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {
        (parser, name, field)
        for parser, by_name in data.items()
        for name, fields in by_name.items()
        for field in fields
    }
