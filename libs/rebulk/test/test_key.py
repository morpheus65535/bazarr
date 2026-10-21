#!/usr/bin/env python
"""
Tests for typed Key retrieval (POC for type-safe value access).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, TypedDict

import pytest

from .. import debug
from ..key import Key
from ..match import Match, Matches
from ..rebulk import Rebulk

if TYPE_CHECKING:
    from typing_extensions import assert_type


def test_key_scalar_retrieval() -> None:
    year = Key("year", int)
    title = Key("title", str)

    bulk = Rebulk().regex(r"\d{4}", key=year).string("Big Buck Bunny", key=title)
    matches = bulk.matches("Big Buck Bunny 2008")

    assert matches[year] == 2008
    assert matches.all(year) == [2008]
    assert matches[title] == "Big Buck Bunny"


def test_key_converter_defaults_to_value_type() -> None:
    assert Key("year", int).converter is int
    fmt = date.fromisoformat
    assert Key("released", date, formatter=fmt).converter is fmt


def test_key_with_explicit_formatter() -> None:
    released = Key("released", date, formatter=date.fromisoformat)
    matches = Rebulk().regex(r"\d{4}-\d{2}-\d{2}", key=released).matches("on 2008-01-02 ...")

    assert matches[released] == date(2008, 1, 2)
    assert matches.all(released) == [date(2008, 1, 2)]


def test_key_rejects_structured_value_type() -> None:
    @dataclass
    class Movie:
        year: int
        title: str

    class MovieDict(TypedDict):
        year: int
        title: str

    with pytest.raises(TypeError, match=r"Matches\.to"):
        Key("movie", Movie)
    with pytest.raises(TypeError, match=r"Matches\.to"):
        Key("movie", MovieDict)


def test_key_missing_returns_none() -> None:
    year = Key("year", int)
    matches = Rebulk().regex(r"\d{4}", key=year).matches("no digits here")

    assert matches[year] is None
    assert matches.all(year) == []


def test_key_multiple_values() -> None:
    digit = Key("digit", int)
    matches = Rebulk().regex(r"\d", key=digit).matches("1 2 3")

    assert matches.all(digit) == [1, 2, 3]
    assert matches[digit] == 1


def test_keys_children_per_name_formatter() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    bulk = Rebulk().regex(r"S(?P<season>\d+)E(?P<episode>\d+)", key=[season, episode], children=True)
    matches = bulk.matches("Show.S03E07.mkv")

    assert matches[season] == 3
    assert matches[episode] == 7


def test_keys_multiple_children_values() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    bulk = Rebulk().regex(
        r"S(?P<season>\d+)(?:E(?P<episode>\d+))+",
        key=[season, episode],
        children=True,
    )
    matches = bulk.matches("Show.S03E07.mkv")

    assert matches[season] == 3
    assert matches.all(episode) == [7]


def test_keys_preserve_explicit_per_name_formatter() -> None:
    season = Key("season", int)
    episode = Key("episode", str)

    # An explicit per-name formatter wins over the key converter (variance preserved):
    # the key would apply plain str, the override upper-cases instead.
    bulk = Rebulk().regex(
        r"S(?P<season>\d+)E(?P<episode>\w+)",
        key=[season, episode],
        formatter={"episode": str.upper},
        children=True,
    )
    matches = bulk.matches("Show.S03Eab.mkv")

    assert matches[season] == 3
    assert matches[episode] == "AB"


def test_keys_rejects_single_formatter_callable() -> None:
    season = Key("season", int)

    with pytest.raises(TypeError, match=r"per-name formatter"):
        Rebulk().regex(r"(?P<season>\d+)", key=[season], formatter=int, children=True)


def test_keys_none_is_noop() -> None:
    year = Key("year", int)
    matches = Rebulk().regex(r"\d{4}", key=None).regex(r"\d{4}", key=year).matches("born in 1984")

    assert matches[year] == 1984


def test_keys_empty_sequence_is_noop() -> None:
    year = Key("year", int)
    matches = Rebulk().regex(r"\d{4}", key=[]).regex(r"\d{4}", key=year).matches("born in 1984")

    assert matches[year] == 1984


def test_declare_keys_inherited_per_name_formatter() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    bulk = Rebulk().declare_keys(season, episode)
    # No key=/formatter= on the pattern: the converters are inherited from the registry.
    bulk.regex(r"S(?P<season>\d+)E(?P<episode>\d+)", children=True)
    matches = bulk.matches("Show.S03E07.mkv")

    assert matches[season] == 3
    assert matches[episode] == 7


def test_declare_keys_inherited_on_named_parent() -> None:
    year = Key("year", int)

    bulk = Rebulk().declare_keys(year).regex(r"\d{4}", name="year")
    matches = bulk.matches("born in 1984")

    assert matches[year] == 1984


def test_declare_keys_explicit_formatter_overrides_registry() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    bulk = Rebulk().declare_keys(season, episode)
    # roman/CJK-like pattern: a per-pattern formatter for episode wins over the registry int.
    bulk.regex(
        r"S(?P<season>\d+)E(?P<episode>\w+)",
        formatter={"episode": lambda s: len(s)},
        children=True,
    )
    matches = bulk.matches("Show.S03Eabcd.mkv")

    assert matches[season] == 3
    assert matches.all(episode) == [4]


def test_declare_keys_bare_callable_formatter_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    # A single bare-callable formatter is the pattern's explicit choice and must
    # win over the registry converter (variance preserved, even without a dict).
    # This deliberately produces a str for an int key, so force the contract
    # check off (it stays runnable under REBULK_CHECK_DECLARED_KEYS=1).
    monkeypatch.setattr(debug, "CHECK_DECLARED_KEYS", False)
    year = Key("year", int)
    bulk = Rebulk().declare_keys(year).regex(r"\d{4}", name="year", formatter=lambda s: f"Y{s}")
    matches = bulk.matches("born in 1984")

    assert matches[0].value == "Y1984"


def test_declare_keys_does_not_mutate_shared_default_formatter() -> None:
    season = Key("season", int)
    shared = {"x": str.upper}
    bulk = Rebulk().declare_keys(season).defaults(formatter=shared)
    bulk.regex(r"(?P<season>\d+)", children=True)

    # The caller-owned dict and the stored default must stay pristine.
    assert shared == {"x": str.upper}
    assert "season" not in bulk._defaults["formatter"]


def test_keys_does_not_mutate_caller_formatter_dict() -> None:
    season = Key("season", int)
    episode = Key("episode", int)
    shared = {"episode": str.upper}
    Rebulk().regex(r"S(?P<season>\d+)E(?P<episode>\w+)", key=[season, episode], formatter=shared, children=True)

    # key= must not leak the season converter into the caller's dict.
    assert shared == {"episode": str.upper}


def test_declare_keys_returns_self_for_chaining() -> None:
    year = Key("year", int)
    bulk = Rebulk()
    assert bulk.declare_keys(year) is bulk


def test_declare_keys_inherited_in_chain() -> None:
    episode = Key("episode", int)
    version = Key("version", int)

    # The ticket's motivating example: declare_keys replaces the repeated
    # formatter={"episode": int, "version": int} on the chain.
    rebulk = (
        Rebulk()
        .declare_keys(episode, version)
        .regex_defaults(flags=re.IGNORECASE)
        .defaults(children=True)
        .chain()
        .regex(r"e(?P<episode>\d{1,4})")
        .repeater(1)
        .regex(r"v(?P<version>\d+)")
        .repeater("?")
        .regex(r"[ex-](?P<episode>\d{1,4})")
        .repeater("*")
        .close()
    )
    matches = rebulk.matches("This is E14v2-15-16-17")

    assert matches.all(episode) == [14, 15, 16, 17]
    assert matches[version] == 2


def test_declared_keys_carried_on_matches() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    matches = Rebulk().declare_keys(season, episode).matches("Show.S03E07.mkv")

    assert matches.declared_keys == {"season": season, "episode": episode}


def test_declared_keys_empty_without_declaration() -> None:
    # key= wires a pattern but does not populate the declared registry.
    year = Key("year", int)
    matches = Rebulk().regex(r"\d{4}", key=year).matches("1984")

    assert matches.declared_keys == {}


def test_effective_keys_merges_children() -> None:
    season = Key("season", int)
    episode = Key("episode", int)

    child = Rebulk().declare_keys(episode)
    parent = Rebulk().declare_keys(season).rebulk(child)

    assert parent.effective_keys() == {"season": season, "episode": episode}

    # Effective keys flow onto the produced Matches too.
    matches = parent.matches("nothing")
    assert matches.declared_keys == {"season": season, "episode": episode}


def test_effective_keys_parent_wins_over_child() -> None:
    parent_key = Key("dup", int)
    child_key = Key("dup", str)

    parent = Rebulk().declare_keys(parent_key).rebulk(Rebulk().declare_keys(child_key))

    assert parent.effective_keys() == {"dup": parent_key}


@pytest.fixture
def check_declared_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable the opt-in declared-key value_type contract check for a test."""
    monkeypatch.setattr(debug, "CHECK_DECLARED_KEYS", True)


def test_truthy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for raw, expected in [("1", True), ("true", True), ("YES", True), (" on ", True), ("0", False), ("", False)]:
        monkeypatch.setenv("REBULK_TEST_FLAG", raw)
        assert debug._truthy_env("REBULK_TEST_FLAG") is expected
    monkeypatch.delenv("REBULK_TEST_FLAG", raising=False)
    assert debug._truthy_env("REBULK_TEST_FLAG") is False


def test_check_declared_keys_disabled_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    # When the check is off, a contract violation is silent (no behaviour change).
    monkeypatch.setattr(debug, "CHECK_DECLARED_KEYS", False)
    season = Key("season", int)
    bulk = Rebulk().declare_keys(season).regex(r"S(?P<season>\d+)", formatter={"season": str}, children=True)
    matches = bulk.matches("S03")

    # str value despite the int declaration: the check is off, so it is not flagged.
    assert matches[0].value == "03"


def test_check_declared_keys_passes_on_matching_type(check_declared_keys: None) -> None:
    season = Key("season", int)
    episode = Key("episode", int)
    bulk = Rebulk().declare_keys(season, episode).regex(r"S(?P<season>\d+)E(?P<episode>\d+)", children=True)

    # Inherited int converters produce ints: the contract holds, no raise.
    matches = bulk.matches("S03E07")
    assert matches[season] == 3
    assert matches[episode] == 7


def test_check_declared_keys_raises_on_formatter_override_mismatch(check_declared_keys: None) -> None:
    season = Key("season", int)
    # A per-pattern override returns str while the key declares int.
    bulk = Rebulk().declare_keys(season).regex(r"S(?P<season>\d+)", formatter={"season": str}, children=True)

    with pytest.raises(TypeError, match=r"declared key 'season' value_type"):
        bulk.matches("S03")


def test_check_declared_keys_validates_each_match() -> None:
    # A name bound to several matches is validated value by value: the first
    # converts to int (ok), the second to str (mismatch) -> raise.
    episode = Key("episode", int)
    matches = Matches()
    matches.declared_keys = {"episode": episode}
    matches.append(Match(0, 1, name="episode", input_string="7 8", formatter=int))
    matches.append(Match(2, 3, name="episode", input_string="7 8", formatter=str))

    with pytest.raises(TypeError, match=r"declared key 'episode' value_type"):
        matches.check_declared_keys()


def test_check_declared_keys_skips_none_value() -> None:
    # A formatted value of None (e.g. a converter that returns None) is exempt
    # rather than flagged against the declared scalar type.
    year = Key("year", int)
    matches = Matches()
    matches.declared_keys = {"year": year}
    matches.append(Match(0, 4, name="year", input_string="1984", formatter=lambda _raw: None))

    matches.check_declared_keys()  # no raise


def test_check_declared_keys_skips_private_parent(check_declared_keys: None) -> None:
    # The private parent of a children pattern carries the raw matched substring
    # (only the children are formatted), so it is not an instance of the declared
    # value_type. Being internal/non-emitted, it must be skipped, not flagged.
    bonus = Key("bonus", int)
    bulk = Rebulk().declare_keys(bonus).regex(r"x(\d+)", name="bonus", children=True, private_parent=True)

    matches = bulk.matches("x264")  # private parent value "x264" (str) must not raise

    # only the emitted (non-private) child is validated, and it is the int value.
    assert [match.value for match in matches if not match.private] == [264]


def test_check_declared_keys_skips_value_mapped_literal() -> None:
    # A value=-mapped literal never goes through the converter; it is exempt
    # even when its type differs from the declared value_type.
    season = Key("season", int)
    matches = Matches()
    matches.declared_keys = {"season": season}
    matches.append(Match(0, 7, value="literal", name="season", input_string="literal"))

    matches.check_declared_keys()  # no raise


def test_check_declared_keys_runs_before_rules(check_declared_keys: None) -> None:
    from ..rules import RenameMatch, Rule

    season = Key("season", int)

    class RenameLabelToSeason(Rule):
        consequence = RenameMatch("season")

        def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
            return matches.named("label")

    bulk = Rebulk().declare_keys(season).regex(r"(?P<label>[a-z]+)", children=True).rules(RenameLabelToSeason)
    matches = bulk.matches("hello")

    # A rule renames a str match onto 'season' (declared int). The check runs
    # before rules, so this legitimate rule-driven rename is not flagged.
    assert matches[0].name == "season"
    assert matches[0].value == "hello"


def test_check_declared_keys_unnamed_and_undeclared_are_ignored() -> None:
    season = Key("season", int)
    matches = Matches()
    matches.declared_keys = {"season": season}
    # An unnamed match and a match with an undeclared name are both skipped.
    matches.append(Match(0, 3, value="x", input_string="x y z"))
    matches.append(Match(4, 5, name="other", input_string="x y z", formatter=str))

    matches.check_declared_keys()  # no raise


def test_check_keys_flags_typo() -> None:
    season = Key("season", int)
    typo = Key("seson", int)  # never produced by the pattern below
    rb = Rebulk().declare_keys(season, typo).regex(r"S(?P<season>\d+)", children=True)

    assert rb.check_keys() == ["seson"]


def test_check_keys_clean_when_all_match() -> None:
    season = Key("season", int)
    episode = Key("episode", int)
    rb = Rebulk().declare_keys(season, episode).regex(r"S(?P<season>\d+)E(?P<episode>\d+)", children=True)

    assert rb.check_keys() == []


def test_check_keys_matches_pattern_name_not_only_groups() -> None:
    # A key can target a pattern's name (string/functional/named regex), not only
    # a regex group name.
    year = Key("year", int)
    rb = Rebulk().declare_keys(year).regex(r"\d{4}", name="year")

    assert rb.check_keys() == []


def test_check_keys_no_declared_keys_is_empty() -> None:
    assert Rebulk().regex(r"\d{4}", name="year").check_keys() == []


def test_check_keys_allowlist_exempts_intentional_unused() -> None:
    season = Key("season", int)
    extra = Key("extra", str)  # intentionally declared without a producing pattern
    rb = Rebulk().declare_keys(season, extra).regex(r"S(?P<season>\d+)", children=True)

    assert rb.check_keys() == ["extra"]
    assert rb.check_keys(allowed_unused=["extra"]) == []
    # A bare string is treated as a single name (not iterated char by char).
    assert rb.check_keys(allowed_unused="extra") == []


def test_check_keys_honors_pattern_declared_properties() -> None:
    # A pattern (e.g. functional) that emits a name dynamically can declare it via
    # `properties`; check_keys honors that declaration.
    season = Key("season", int)
    rb = Rebulk().declare_keys(season).functional(lambda string: None, properties={"season": [None]})

    assert rb.check_keys() == []


def test_check_keys_rule_produced_name_needs_allowlist() -> None:
    # A name produced only by a rule (not a pattern) is not statically detectable,
    # so it is reported unless allowlisted — documents the known limitation.
    from ..rules import RenameMatch, Rule

    year = Key("year", int)

    class RenameRawToYear(Rule):
        consequence = RenameMatch("year")

        def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
            return matches.named("raw_year")

    rb = Rebulk().declare_keys(year).regex(r"(?P<raw_year>\d{4})", children=True).rules(RenameRawToYear)

    assert rb.check_keys() == ["year"]
    assert rb.check_keys(allowed_unused="year") == []


def test_check_keys_considers_children_rebulks() -> None:
    season = Key("season", int)
    episode = Key("episode", int)
    typo = Key("epsiode", int)

    child = Rebulk().regex(r"E(?P<episode>\d+)", children=True)
    parent = Rebulk().declare_keys(season, episode, typo).regex(r"S(?P<season>\d+)", children=True).rebulk(child)

    # 'episode' is produced by the child; only the typo 'epsiode' is unused.
    assert parent.check_keys() == ["epsiode"]


def test_check_keys_considers_disabled_patterns_full_set() -> None:
    # A key whose only producing pattern lives in a disabled child rebulk is NOT
    # flagged: the typo guard considers the full built pattern set, not the
    # config-gated effective one.
    season = Key("season", int)
    episode = Key("episode", int)

    disabled_child = Rebulk(disabled=lambda context: True).regex(r"E(?P<episode>\d+)", children=True)
    parent = Rebulk().declare_keys(season, episode).regex(r"S(?P<season>\d+)", children=True).rebulk(disabled_child)

    assert parent.check_keys() == []


def test_check_keys_in_chain() -> None:
    episode = Key("episode", int)
    version = Key("version", int)
    typo = Key("verison", int)

    rb = (
        Rebulk()
        .declare_keys(episode, version, typo)
        .defaults(children=True)
        .chain()
        .regex(r"e(?P<episode>\d{1,4})")
        .regex(r"v(?P<version>\d+)")
        .close()
    )

    assert rb.check_keys() == ["verison"]


if TYPE_CHECKING:

    def _reveal_types() -> None:
        # Type-checked only (never executed): the typed key drives precise types.
        year = Key("year", int)
        title = Key("title", str)
        matches = Rebulk().regex(r"\d{4}", key=year).string("x", key=title).matches("2008 x")

        assert_type(matches[year], "int | None")
        assert_type(matches.all(year), list[int])
        assert_type(matches[title], "str | None")
        # A formatter-based key keeps the precise value type.
        released = Key("released", date, formatter=date.fromisoformat)
        assert_type(matches[released], "date | None")
        # Existing integer / slice access stays intact.
        assert_type(matches[0], Match)
