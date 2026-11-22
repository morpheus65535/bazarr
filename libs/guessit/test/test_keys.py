#!/usr/bin/env python
"""Tests for the typed Key registry (guessit.rules.common.keys)."""

from typing import Any, TypedDict

import pytest
from rebulk import Key

from ..api import default_api, guessit
from ..rules.common import keys as keys_module
from ..schema_generated import GUESSIT_SCHEMA

#: Registry key names that are internal match names, renamed/aggregated before
#: output and therefore absent from GUESSIT_SCHEMA. ``count`` becomes
#: ``episode_count`` / ``season_count`` (see the episode rules).
_INTERNAL_NAMES = {"count"}


def _registry() -> list[Key[Any]]:
    return [value for value in vars(keys_module).values() if isinstance(value, Key)]


def test_registry_keys_are_well_formed() -> None:
    registry = _registry()
    assert registry, "the Key registry should not be empty"
    for key in registry:
        assert key.name, f"{key!r} has an empty name"
        assert isinstance(key.value_type, type), f"{key.name} value_type must be a type"
        assert callable(key.converter), f"{key.name} converter must be callable"


def test_registry_key_names_are_unique() -> None:
    names = [key.name for key in _registry()]
    assert len(names) == len(set(names)), f"duplicate key names: {names}"


def test_emitted_key_names_exist_in_schema() -> None:
    for key in _registry():
        if key.name in _INTERNAL_NAMES:
            continue
        assert key.name in GUESSIT_SCHEMA, f"key {key.name!r} is not an emitted property"


def test_registry_formatter_applies_end_to_end() -> None:
    # A config-driven property whose formatter now comes from the declared Key
    # (film -> int) must still yield the typed value.
    assert guessit("James_Bond-f21-Casino_Royale.mkv").get("film") == 21


def test_check_keys_has_no_typo_or_dead_declaration() -> None:
    # Every key passed to declare_keys must be produced by some pattern, so a
    # typo'd or stale declaration fails fast here (Toilal/rebulk#73).
    default_api.configure({})
    assert default_api.rebulk is not None
    assert default_api.rebulk.check_keys() == []


class _SeasonEpisode(TypedDict, total=False):
    season: int
    episode: int


class _SeasonAsStr(TypedDict, total=False):
    season: str


def test_to_projection_uses_declared_key_types() -> None:
    # Typed projection (Toilal/rebulk#71): declared keys carry the value type.
    default_api.configure({})
    assert default_api.rebulk is not None
    matches = default_api.rebulk.matches("Show.S03E07.1080p.mkv", {})
    assert matches.to(_SeasonEpisode) == {"season": 3, "episode": 7}


def test_to_projection_rejects_type_contradicting_declared_key() -> None:
    # season is declared int; a model typing it str must be rejected (#71).
    default_api.configure({})
    assert default_api.rebulk is not None
    matches = default_api.rebulk.matches("Show.S03E07.mkv", {})
    with pytest.raises(TypeError):
        matches.to(_SeasonAsStr)
