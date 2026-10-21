#!/usr/bin/env python
import json
import os
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from .. import api
from ..api import GuessitException, default_api, guessit, properties, suggested_expected

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_default() -> None:
    ret = guessit("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret


def test_forced_unicode() -> None:
    ret = guessit("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret
    assert isinstance(ret["title"], str)


def test_forced_binary() -> None:
    ret = guessit(b"Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret
    assert isinstance(ret["title"], bytes)


def test_pathlike_object() -> None:
    path = Path("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    ret = guessit(path)
    assert ret
    assert "title" in ret


def test_none_input() -> None:
    with pytest.raises(TypeError) as excinfo:
        guessit(None)  # type: ignore[arg-type]
    assert "None" in str(excinfo.value)


def test_unicode_japanese() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi")
    assert ret
    assert "title" in ret


def test_unicode_japanese_options() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret
    assert "title" in ret
    assert ret["title"] == "阿维达"


def test_forced_unicode_japanese_options() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret
    assert "title" in ret
    assert ret["title"] == "阿维达"


def test_properties() -> None:
    props = properties()
    assert "video_codec" in props


def test_public_api_is_exported_from_the_package() -> None:
    import guessit as pkg

    expected = {
        "GUESSIT_SCHEMA",
        "ConfigurationException",
        "GuessItApi",
        "Size",
        "guessit",
        "properties",
        "suggested_expected",
    }
    assert expected <= set(pkg.__all__)
    for name in expected:
        assert hasattr(pkg, name), f"guessit.{name} is not exported"


def test_list_value_not_mutated_between_guesses() -> None:
    # Regression for #822: a config pattern with a list value (compound edition)
    # used to be aliased into the result and mutated in place, leaking state into
    # later guesses. Parsing a variant that adds another edition must not pollute
    # the shared value.
    assert guessit("ultimate collector edition")["edition"] == ["Ultimate", "Collector"]
    assert guessit("ultimate collectors edition dc")["edition"] == ["Ultimate", "Collector", "Director's Cut"]
    assert guessit("ultimate collector edition")["edition"] == ["Ultimate", "Collector"]


def test_title_rule_tags_not_mutated_between_guesses() -> None:
    """
    The tags TitleFromPosition puts on the title hole must be a copy of the rule's own list.

    The rule instance lives in the cached rebulk and is shared by every guessit() call. When the
    hole aliases ``match_tags`` instead of copying it, ``PreferTitleWithYear`` (which appends
    ``equivalent-ignore`` to the title matches it demotes) extends that shared list in place, so
    it grows at every parse and every later title is born already tagged ``equivalent-ignore`` --
    a tag the processors act upon. A yaml corpus entry cannot catch this: each entry parses a
    single string, while the leak only shows up on the parses that follow.
    """
    from ..rules.properties.title import TitleFromPosition

    api.reset()
    options = {"excludes": ["alternative_title"]}
    for _ in range(3):
        assert guessit("Movies/Foo (2019)/Foo.2019.1080p.BluRay.x264-GRP.mkv", options)["title"] == "Foo"

    assert default_api.rebulk is not None
    title_rule = next(
        rule
        for rule in default_api.rebulk.effective_rules(default_api.effective_options)
        if isinstance(rule, TitleFromPosition)
    )
    assert title_rule.match_tags == ["title"]
    api.reset()


def test_exception() -> None:
    with pytest.raises(GuessitException) as excinfo:
        guessit(object())  # type: ignore[arg-type]
    assert "An internal error has occurred in guessit" in str(excinfo.value)
    assert "Guessit Exception Report" in str(excinfo.value)
    assert "Please report at https://github.com/guessit-io/guessit/issues" in str(excinfo.value)


def test_suggested_expected() -> None:
    with open(os.path.join(__location__, "suggested.json"), encoding="utf-8") as f:
        content = json.load(f)
    actual = suggested_expected(content["titles"])
    assert actual == content["suggested"]


def test_should_rebuild_rebulk_on_advanced_config_change(mocker: MockerFixture) -> None:
    api.reset()
    rebulk_builder_spy = mocker.spy(api, "rebulk_builder")

    string = "some.movie.trfr.mkv"

    result1 = default_api.guessit(string)

    assert result1.get("title") == "some movie trfr"
    assert "subtitle_language" not in result1

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()

    result2 = default_api.guessit(string, {"advanced_config": {"language": {"subtitle_prefixes": ["tr"]}}})

    assert result2.get("title") == "some movie"
    assert str(result2.get("subtitle_language")) == "fr"

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()


def test_should_not_rebuild_rebulk_on_same_advanced_config(mocker: MockerFixture) -> None:
    api.reset()
    rebulk_builder_spy = mocker.spy(api, "rebulk_builder")

    string = "some.movie.subfr.mkv"

    result1 = default_api.guessit(string)

    assert result1.get("title") == "some movie"
    assert str(result1.get("subtitle_language")) == "fr"

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()

    result2 = default_api.guessit(string)

    assert result2.get("title") == "some movie"
    assert str(result2.get("subtitle_language")) == "fr"

    assert rebulk_builder_spy.call_count == 0
    rebulk_builder_spy.reset_mock()


def test_split_words_backward_compatible() -> None:
    from ..rules.properties.episodes import _split_words

    # A flat list of strings stays valid: every word is word-first, none number-first.
    assert _split_words(["season", "saison"]) == (["season", "saison"], [])

    # Object entries carry an optional numfirst flag.
    words, numfirst = _split_words([{"value": "temporada", "numfirst": True}, {"value": "season"}])
    assert words == ["temporada", "season"]
    assert numfirst == ["temporada"]

    # Mixed list, as produced when a user's string list is merged into the default objects.
    words, numfirst = _split_words([{"value": "сезон", "numfirst": True}, "kausi"])
    assert words == ["сезон", "kausi"]
    assert numfirst == ["сезон"]


def test_episode_words_accept_legacy_string_list() -> None:
    api.reset()
    # A user config may still provide season_words as a plain list of strings; it is
    # merged into the object-based default config and must keep working end to end.
    config = {"advanced_config": {"episodes": {"season_words": ["kausi"]}}}
    assert guessit("Sarja Kausi 2", config).get("season") == 2
    assert guessit("Vikings 3 Temporada 720p", config).get("season") == 3
    api.reset()


def test_title_articles_overridable() -> None:
    api.reset()
    # A lone-article title swallows the following property word only for words in
    # advanced_config.title.articles. "das" is not a default article, so adding it
    # via config must make it behave like "the".
    assert guessit("Das.Collector.2009.mkv").get("title") == "Das"
    config = {"advanced_config": {"title": {"articles": ["das"]}}}
    assert guessit("Das.Collector.2009.mkv", config).get("title") == "Das Collector"
    api.reset()


def test_title_stop_words_overridable() -> None:
    api.reset()
    # A trailing Title-Case country is kept in the title when cropping it would leave
    # the title ending on a stop-word. "beyond" is not a default stop-word, so the
    # country is dropped by default and kept once it is added via config.
    default = guessit("Life.Beyond.Us.1080p.mkv")
    assert default.get("title") == "Life Beyond"
    assert str(default.get("country")) == "US"
    config = {"advanced_config": {"title": {"title_stop_words": ["beyond"]}}}
    overridden = guessit("Life.Beyond.Us.1080p.mkv", config)
    assert overridden.get("title") == "Life Beyond Us"
    assert overridden.get("country") is None
    api.reset()


def test_other_art_keywords_overridable() -> None:
    api.reset()
    # An artwork keyword filename is reclassified as `other` only for the keywords in
    # advanced_config.other.art. "myart" is not a default keyword, so it stays a title
    # until it is added via config.
    assert guessit("Show/myart.jpg").get("other") is None
    config = {"advanced_config": {"other": {"art": {"myart": "Poster"}}}}
    assert guessit("Show/myart.jpg", config).get("other") == "Poster"
    api.reset()
