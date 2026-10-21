#!/usr/bin/env python
"""
Base builder classes for Rebulk
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from copy import deepcopy
from logging import getLogger
from typing import TYPE_CHECKING, Any, TypeVar

from .chain import Chain, ChainPart
from .formatters import default_formatter
from .key import Key
from .loose import set_defaults
from .pattern import FunctionalPattern, Pattern, RePattern, StringPattern

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from typing_extensions import Self

log = getLogger(__name__).log

_P = TypeVar("_P", bound=Pattern)


def _apply_key(key: Key[Any] | Sequence[Key[Any]] | None, kwargs: dict[str, Any]) -> dict[str, Any]:
    r"""
    Inject one or several typed :class:`~rebulk.key.Key` into pattern kwargs,
    without overriding explicit values.

    A single ``Key`` sets the match ``name`` and the ``formatter`` (its explicit
    ``formatter`` or its ``value_type``). A sequence of keys instead builds a
    per-name ``formatter`` dict, composing with ``children=True`` patterns that
    expose several named groups (e.g. ``(?P<season>\d+)(?P<episode>\d+)``): each
    key's converter is registered under its ``name``, and explicit per-name
    entries already present in ``formatter`` are preserved (a per-pattern
    formatter still wins over the key's converter).
    """
    if key is None:
        return kwargs
    if isinstance(key, Key):
        kwargs.setdefault("name", key.name)
        kwargs.setdefault("formatter", key.converter)
        return kwargs
    if not key:
        return kwargs
    formatter = kwargs.get("formatter")
    if formatter is None:
        formatter = {}
    elif isinstance(formatter, dict):
        formatter = dict(formatter)  # copy: never mutate the caller's dict
    else:
        raise TypeError(
            "a sequence of keys builds a per-name formatter dict and cannot be combined with a "
            "single formatter callable; pass a per-name formatter dict or drop the explicit formatter"
        )
    for single_key in key:
        formatter.setdefault(single_key.name, single_key.converter)
    kwargs["formatter"] = formatter
    return kwargs


@contextmanager
def overrides(kwargs: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """
    Implements override kwarg to restore initial kwarg arguments from overrides list after set_defaults calls.
    :param kwargs:
    :return:
    """
    override_keys = kwargs.pop("overrides", None)
    backup: dict[str, Any] = {}
    if override_keys:
        for override_key in override_keys:
            backup[override_key] = kwargs[override_key]

    yield backup

    kwargs.update(backup)


class PatternFactory:
    """
    Holds default keyword arguments and builds Pattern objects from them.

    Shared by :class:`Builder` (the fluent pattern-registration API) and
    :class:`ChainBuilder` (the fluent chain-assembly API).
    """

    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._regex_defaults: dict[str, Any] = {}
        self._string_defaults: dict[str, Any] = {}
        self._functional_defaults: dict[str, Any] = {}
        self._chain_defaults: dict[str, Any] = {}
        self._keys: dict[str, Key[Any]] = {}

    def declare_keys(self, *keys: Key[Any]) -> Self:
        """
        Declare typed :class:`~rebulk.key.Key` once for this builder.

        Every pattern built afterwards inherits each key's converter as a
        per-name formatter for the matching group name, unless it defines its
        own formatter for that name (an explicit per-pattern formatter still
        wins). This gives a single source of truth for the common conversion of
        named groups exposed by ``children=True`` patterns, while per-pattern
        overrides preserve formatter variance across patterns.
        """
        for key in keys:
            self._keys[key.name] = key
        return self

    def _inherit_keys(self, pattern: _P) -> _P:
        """
        Enrich a freshly built pattern with the declared keys' converters as
        per-name formatters, without overriding any formatter it already defines.

        A pattern that supplies its own formatter for a name keeps it: explicit
        per-name entries take precedence, and a single bare-callable formatter
        (whose ``_default_formatter`` differs from the library default) is left
        untouched entirely. Enrichment writes to a fresh dict so the shared
        ``defaults(formatter=...)`` / caller-owned dict is never mutated in place.
        """
        if not self._keys or pattern._default_formatter is not default_formatter:
            return pattern
        missing = {key.name: key.converter for key in self._keys.values() if key.name not in pattern.formatters}
        if missing:
            pattern.formatters = {**pattern.formatters, **missing}
        return pattern

    def defaults(self, **kwargs: Any) -> Self:
        """
        Define default keyword arguments for all patterns
        """
        set_defaults(kwargs, self._defaults, override=True)
        return self

    def regex_defaults(self, **kwargs: Any) -> Self:
        """
        Define default keyword arguments for regular expression patterns.
        """
        set_defaults(kwargs, self._regex_defaults, override=True)
        return self

    def string_defaults(self, **kwargs: Any) -> Self:
        """
        Define default keyword arguments for string patterns.
        """
        set_defaults(kwargs, self._string_defaults, override=True)
        return self

    def functional_defaults(self, **kwargs: Any) -> Self:
        """
        Define default keyword arguments for functional patterns.
        """
        set_defaults(kwargs, self._functional_defaults, override=True)
        return self

    def chain_defaults(self, **kwargs: Any) -> Self:
        """
        Define default keyword arguments for patterns chain.
        """
        set_defaults(kwargs, self._chain_defaults, override=True)
        return self

    def build_re(self, *pattern: Any, **kwargs: Any) -> RePattern:
        """
        Builds a new regular expression pattern
        """
        with overrides(kwargs):
            set_defaults(self._regex_defaults, kwargs)
            set_defaults(self._defaults, kwargs)

        return self._inherit_keys(RePattern(*pattern, **kwargs))

    def build_string(self, *pattern: Any, **kwargs: Any) -> StringPattern:
        """
        Builds a new string pattern
        """
        with overrides(kwargs):
            set_defaults(self._string_defaults, kwargs)
            set_defaults(self._defaults, kwargs)

        return self._inherit_keys(StringPattern(*pattern, **kwargs))

    def build_functional(self, *pattern: Any, **kwargs: Any) -> FunctionalPattern:
        """
        Builds a new functional pattern
        """
        with overrides(kwargs):
            set_defaults(self._functional_defaults, kwargs)
            set_defaults(self._defaults, kwargs)

        return self._inherit_keys(FunctionalPattern(*pattern, **kwargs))

    def build_chain(self, **kwargs: Any) -> Chain:
        """
        Builds a new (unregistered) patterns chain.
        """
        with overrides(kwargs):
            set_defaults(self._chain_defaults, kwargs)
            set_defaults(self._defaults, kwargs)

        return self._inherit_keys(Chain(**kwargs))


class Builder(PatternFactory, metaclass=ABCMeta):
    """
    Base fluent builder: registers patterns via :meth:`pattern` and exposes the
    ``string`` / ``regex`` / ``functional`` / ``chain`` methods.
    """

    def reset(self) -> None:
        """
        Reset all defaults.
        """
        self.__init__()  # type: ignore[misc]

    @abstractmethod
    def pattern(self, *pattern: Any) -> Self:
        """
        Register a list of Pattern instance
        :param pattern:
        :return:
        """

    def regex(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> Self:
        """
        Add re pattern

        :param key: optional typed key(s). A single :class:`~rebulk.key.Key`
            wires up the match name and value type; a sequence of keys wires up a
            per-name formatter dict, for ``children=True`` patterns exposing
            several named groups.
        :return: self
        """
        return self.pattern(self.build_re(*pattern, **_apply_key(key, kwargs)))

    def string(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> Self:
        """
        Add string pattern

        :param key: optional typed key(s). A single :class:`~rebulk.key.Key`
            wires up the match name and value type; a sequence of keys wires up a
            per-name formatter dict, for ``children=True`` patterns exposing
            several named groups.
        :return: self
        """
        return self.pattern(self.build_string(*pattern, **_apply_key(key, kwargs)))

    def functional(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> Self:
        """
        Add functional pattern

        :param key: optional typed key(s). A single :class:`~rebulk.key.Key`
            wires up the match name and value type; a sequence of keys wires up a
            per-name formatter dict, for ``children=True`` patterns exposing
            several named groups.
        :return: self
        """
        return self.pattern(self.build_functional(*pattern, **_apply_key(key, kwargs)))

    def chain(self, **kwargs: Any) -> ChainBuilder:
        """
        Add a patterns chain, using configuration of this builder.

        Returns a :class:`ChainBuilder` to assemble the chain parts; call
        ``.close()`` to get back to this builder.
        """
        chain = self.build_chain(**kwargs)
        self.pattern(chain)
        builder = ChainBuilder(self, chain)
        builder._inherit_defaults(self)
        return builder


class ChainBuilder(PatternFactory):
    """
    Fluent builder for the parts of a :class:`~rebulk.chain.Chain`.

    Each ``string`` / ``regex`` / ``functional`` call appends a
    :class:`~rebulk.chain.ChainPart` (on which ``repeater`` can be called);
    ``chain`` nests another chain and ``close`` returns the owning builder.
    """

    def __init__(self, parent: Builder | ChainBuilder, chain: Chain) -> None:
        super().__init__()
        self._parent = parent
        self._chain = chain

    def _inherit_defaults(self, source: PatternFactory) -> None:
        self._defaults = deepcopy(source._defaults)
        self._regex_defaults = deepcopy(source._regex_defaults)
        self._functional_defaults = deepcopy(source._functional_defaults)
        self._string_defaults = deepcopy(source._string_defaults)
        self._chain_defaults = deepcopy(source._chain_defaults)
        self._keys = dict(source._keys)

    def _add(self, pattern: Any) -> ChainPart:
        part = ChainPart(self, pattern)
        self._chain.parts.append(part)
        return part

    def regex(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> ChainPart:
        """
        Add a re pattern to the chain.
        """
        return self._add(self.build_re(*pattern, **_apply_key(key, kwargs)))

    def string(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> ChainPart:
        """
        Add a string pattern to the chain.
        """
        return self._add(self.build_string(*pattern, **_apply_key(key, kwargs)))

    def functional(self, *pattern: Any, key: Key[Any] | Sequence[Key[Any]] | None = None, **kwargs: Any) -> ChainPart:
        """
        Add a functional pattern to the chain.
        """
        return self._add(self.build_functional(*pattern, **_apply_key(key, kwargs)))

    def chain(self, **kwargs: Any) -> ChainBuilder:
        """
        Nest another chain as a part of this chain.
        """
        chain = self.build_chain(**kwargs)
        self._add(chain)
        nested = ChainBuilder(self, chain)
        nested._inherit_defaults(self)
        return nested

    def close(self) -> Any:
        """
        Close the chain and return the owning (non-chain) builder.
        """
        parent = self._parent
        while isinstance(parent, ChainBuilder):
            parent = parent._parent
        return parent
