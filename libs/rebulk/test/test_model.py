#!/usr/bin/env python
"""
Tests for typed result models via Matches.to(dataclass) (v5 POC).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional, TypedDict

import pytest

from ..key import Key
from ..match import _contradicts
from ..rebulk import Rebulk

if TYPE_CHECKING:
    from typing_extensions import assert_type


@dataclass
class Movie:
    year: int
    title: str
    tags: list[str] = field(default_factory=list)
    resolution: str | None = None


class MovieDict(TypedDict):
    year: int
    title: str
    tags: list[str]


def test_to_model() -> None:
    year = Key("year", int)
    title = Key("title", str)
    tag = Key("tags", str)

    bulk = (
        Rebulk()
        .regex(r"\d{4}", key=year)
        .string("Big Buck Bunny", key=title)
        .string("HD", key=tag)
        .string("BluRay", key=tag)
    )
    movie = bulk.matches("Big Buck Bunny 2008 HD BluRay").to(Movie)

    assert movie == Movie(year=2008, title="Big Buck Bunny", tags=["HD", "BluRay"], resolution=None)


def test_to_model_defaults_when_unmatched() -> None:
    year = Key("year", int)
    title = Key("title", str)

    movie = Rebulk().regex(r"\d{4}", key=year).string("Title", key=title).matches("Title 1999").to(Movie)

    assert movie.tags == []  # list field -> empty
    assert movie.resolution is None  # optional scalar -> default


def test_to_typeddict() -> None:
    year = Key("year", int)
    title = Key("title", str)
    tag = Key("tags", str)

    bulk = (
        Rebulk()
        .regex(r"\d{4}", key=year)
        .string("Big Buck Bunny", key=title)
        .string("HD", key=tag)
        .string("BluRay", key=tag)
    )
    movie = bulk.matches("Big Buck Bunny 2008 HD BluRay").to(MovieDict)

    assert movie == {"year": 2008, "title": "Big Buck Bunny", "tags": ["HD", "BluRay"]}


def test_to_typeddict_omits_unmatched() -> None:
    year = Key("year", int)
    movie = Rebulk().regex(r"\d{4}", key=year).matches("1999").to(MovieDict)

    assert movie == {"year": 1999, "tags": []}  # unmatched scalar key omitted, list key kept


def test_to_primitive() -> None:
    year = Key("year", int)
    value = Rebulk().regex(r"\d{4}", key=year).matches("born 1984").to(int)

    assert value == 1984


def test_to_list() -> None:
    digit = Key("digit", int)
    values = Rebulk().regex(r"\d", key=digit).matches("1 2 3").to(list[int])

    assert values == [1, 2, 3]


def test_to_list_of_structured_rejected() -> None:
    matches = Rebulk().regex(r"\d{4}", key=Key("year", int)).matches("1984 2008")
    with pytest.raises(TypeError, match="no record grouping"):
        matches.to(list[Movie])
    with pytest.raises(TypeError, match="no record grouping"):
        matches.to(list[MovieDict])


def test_to_primitive_empty_raises() -> None:
    year = Key("year", int)
    matches = Rebulk().regex(r"\d{4}", key=year).matches("no digits")

    with pytest.raises(LookupError):
        matches.to(int)


def test_to_rejects_non_type() -> None:
    matches = Rebulk().string("x").matches("x")
    with pytest.raises(TypeError, match="not a dataclass"):
        matches.to(42)  # type: ignore[arg-type]


def test_to_model_contradicting_declared_key_raises() -> None:
    @dataclass
    class Wrong:
        year: str  # declared key types year as int

    year = Key("year", int)
    matches = Rebulk().declare_keys(year).regex(r"\d{4}", name="year").matches("1984")
    with pytest.raises(TypeError, match="contradicts declared key"):
        matches.to(Wrong)


def test_to_typeddict_contradicting_declared_key_raises() -> None:
    class Wrong(TypedDict):
        year: str

    year = Key("year", int)
    matches = Rebulk().declare_keys(year).regex(r"\d{4}", name="year").matches("1984")
    with pytest.raises(TypeError, match="contradicts declared key"):
        matches.to(Wrong)


def test_to_model_declared_key_list_element_checked() -> None:
    @dataclass
    class Good:
        digit: list[int] = field(default_factory=list)

    @dataclass
    class Bad:
        digit: list[str] = field(default_factory=list)

    digit = Key("digit", int)
    matches = Rebulk().declare_keys(digit).regex(r"\d", name="digit").matches("1 2 3")

    assert matches.to(Good).digit == [1, 2, 3]  # element type agrees
    with pytest.raises(TypeError, match="contradicts declared key"):
        matches.to(Bad)


def test_to_model_declared_key_optional_element_checked() -> None:
    @dataclass
    class Good:
        year: int | None = None  # PEP 604 union (types.UnionType)

    @dataclass
    class Bad:
        year: Optional[str] = None  # noqa: UP045  # legacy typing.Union form

    year = Key("year", int)
    matches = Rebulk().declare_keys(year).regex(r"\d{4}", name="year").matches("1984")

    assert matches.to(Good).year == 1984
    with pytest.raises(TypeError, match="contradicts declared key"):
        matches.to(Bad)


def test_to_model_declared_key_subclass_is_compatible() -> None:
    @dataclass
    class Release:
        released: datetime

    # date key, datetime field: related by subclassing, so no contradiction.
    released = Key("released", date, formatter=lambda s: datetime.fromisoformat(s))
    matches = Rebulk().declare_keys(released).regex(r"\S+", name="released").matches("2008-01-02T10:00:00")

    assert matches.to(Release).released == datetime(2008, 1, 2, 10, 0, 0)


def test_to_model_unresolvable_field_type_never_contradicts() -> None:
    @dataclass
    class Loose:
        year: Any = None

    year = Key("year", int)
    matches = Rebulk().declare_keys(year).regex(r"\d{4}", name="year").matches("1984")

    # An ``Any`` (or otherwise unresolvable) field type is always compatible.
    assert matches.to(Loose).year == 1984


def test_contradicts_bare_container_is_unresolved() -> None:
    # A bare, unparameterized container carries no element type, so it never
    # contradicts a declared scalar key (no spurious TypeError in to()).
    for container in (list, tuple, set, frozenset, dict):
        assert _contradicts(container, str) is False
        assert _contradicts(container, int) is False
    # A parameterized container is still checked against its element type.
    assert _contradicts(list[int], str) is True
    assert _contradicts(list[int], int) is False


def test_to_model_disabled_rebulk_does_not_carry_declared_keys() -> None:
    @dataclass
    class Wrong:
        year: str = "n/a"  # would contradict the int key if it were carried

    year = Key("year", int)
    rb = Rebulk(disabled=lambda context: True).declare_keys(year).regex(r"\d{4}", name="year")
    matches = rb.matches("1984")

    # Patterns never ran (disabled), so no declared keys are carried and the
    # cross-check stays silent rather than rejecting a model with no values.
    assert matches.declared_keys == {}
    assert matches.to(Wrong) == Wrong()


def test_to_model_field_without_declared_key_is_untouched() -> None:
    # A model field with no matching declared key is never cross-checked.
    year = Key("year", int)
    matches = Rebulk().declare_keys(year).regex(r"\d{4}", key=year).string("Title", name="title").matches("Title 1999")

    assert matches.to(Movie) == Movie(year=1999, title="Title")


if TYPE_CHECKING:

    def _reveal_types() -> None:
        movie = Rebulk().matches("").to(Movie)
        assert_type(movie, Movie)
        movie_dict = Rebulk().matches("").to(MovieDict)
        assert_type(movie_dict, MovieDict)
        assert_type(Rebulk().matches("").to(int), int)
        assert_type(Rebulk().matches("").to(list[int]), list[int])
