#!/usr/bin/env python
"""Cross-parser tests (opt-in), one test per external parser.

Thousands of (release_name -> expected field) assertions derived from the test
fixtures of other, permissively-licensed release-name parsers. Each parser gets
its own test:

* ``ptt``     — dreulavelle/PTT (MIT)
* ``anitomy`` — erengy/anitomy (MPL-2.0, anime)
* ``thcolin`` — thcolin/scene-release-parser-php (MIT)
* ``ptn``     — divijbindlish/parse-torrent-name (MIT)
* ``go-ptn``  — razsteinmetz/go-ptn (MIT)

See ``scripts/import_cross_parser_tests.py`` for how the datasets are imported and
mapped into the guessit vocabulary, and ``guessit/test/cross_parser/NOTICE.md``
for attribution.

These tests are **excluded from the default run** (marked ``cross_parser``;
``pyproject.toml`` adds ``-m 'not cross_parser'``). Run them explicitly with::

    uv run pytest -m cross_parser

Independent parsers legitimately disagree (and guessit is sometimes the more
correct one), so these tests do **not** try to make guessit match every external
label. Every field guessit does not currently satisfy is recorded in
``cross_parser/baseline.json``; a parser's test passes as long as no *new*
divergence appears. It therefore catches regressions without requiring any of the
existing divergences to be fixed. After an intentional behaviour change,
regenerate the baseline with ``python scripts/import_cross_parser_tests.py``.
"""

from __future__ import annotations

import collections

import pytest

from .. import guessit
from ._cross_parser import field_matches, iter_cases, load_baseline

# Group the vendored entries by parser once, at import time.
_BY_PARSER: dict[str, list[tuple[str, dict[str, object]]]] = collections.defaultdict(list)
for _parser, _name, _expected in iter_cases():
    _BY_PARSER[_parser].append((_name, _expected))

_BASELINE = load_baseline()


@pytest.mark.cross_parser
@pytest.mark.parametrize("parser", sorted(_BY_PARSER))
def test_cross_parser(parser: str) -> None:
    """Run guessit over every case of one parser; fail only on new divergences."""
    regressions: list[str] = []
    for name, expected in _BY_PARSER[parser]:
        try:
            result = guessit(name)
        except Exception as exc:  # a crash on any name is itself a finding
            # `regenerate_baseline` records crashes as the "<exception>" field, so
            # tolerate them the same way and only flag a *new* crash as a regression.
            if (parser, name, "<exception>") not in _BASELINE:
                regressions.append(f"  {name}\n    <exception>: {exc!r}")
            continue
        for field, value in expected.items():
            if field_matches(result, field, value):
                continue
            if (parser, name, field) in _BASELINE:
                continue  # known divergence, tracked in baseline.json — tolerated
            regressions.append(f"  {name}\n    {field}: expected {value!r}, got {result.get(field)!r}")

    assert not regressions, (
        f"{len(regressions)} new divergence(s) vs {parser} not in cross_parser/baseline.json "
        f"(regenerate with `python scripts/import_cross_parser_tests.py` if intentional):\n"
        + "\n".join(regressions[:50])
    )
