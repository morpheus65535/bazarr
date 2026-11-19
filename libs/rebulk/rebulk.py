#!/usr/bin/env python
"""
Entry point functions and classes for Rebulk
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, cast

from . import debug
from .builder import Builder
from .chain import Chain
from .match import Matches
from .pattern import Pattern, RePattern
from .processors import ConflictSolver, PrivateRemover
from .rules import CustomRule, Rules
from .utils import extend_safe

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from typing_extensions import Self

    from .key import Key

log = getLogger(__name__).log


def _producible_names(pattern: Pattern) -> set[str]:
    """
    Names a pattern can emit: any name it declares via ``properties``, its own
    ``name``, every regex group name, and — for a :class:`~rebulk.chain.Chain` —
    the names of its parts. Private/marker names are included so a key targeting
    one is not flagged as unused.

    This mirrors the name extraction in :class:`~rebulk.introspector.PatternDescription`
    but is intentionally *inclusive* (it keeps private/marker names), whereas
    introspection filters them out for its public-properties view.
    """
    names: set[str] = set(pattern.properties)
    if pattern.name:
        names.add(pattern.name)
    if isinstance(pattern, RePattern):
        for compiled in pattern.patterns:
            names.update(compiled.groupindex)
    elif isinstance(pattern, Chain):
        for part in pattern.parts:
            names |= _producible_names(part.pattern)
    return names


class Rebulk(Builder):
    r"""
    Regular expression, string and function based patterns are declared in a ``Rebulk`` object. It use a fluent API to
    chain ``string``, ``regex``, and ``functional`` methods to define various patterns types.

    .. code-block:: python

        >>> from rebulk import Rebulk
        >>> bulk = Rebulk().string('brown').regex(r'qu\w+').functional(lambda s: (20, 25))

    When ``Rebulk`` object is fully configured, you can call ``matches`` method with an input string to retrieve all
    ``Match`` objects found by registered pattern.

    .. code-block:: python

        >>> bulk.matches("The quick brown fox jumps over the lazy dog")
        [<brown:(10, 15)>, <quick:(4, 9)>, <jumps:(20, 25)>]

    If multiple ``Match`` objects are found at the same position, only the longer one is kept.

    .. code-block:: python

        >>> bulk = Rebulk().string('lakers').string('la')
        >>> bulk.matches("the lakers are from la")
        [<lakers:(4, 10)>, <la:(20, 22)>]
    """

    def __init__(
        self,
        disabled: bool | Callable[[dict[str, Any] | None], bool] = lambda context: False,
        default_rules: bool = True,
    ) -> None:
        """
        Creates a new Rebulk object.
        :param disabled: if True, this pattern is disabled. Can also be a function(context).
        :type disabled: bool|function
        :param default_rules: use default rules
        :type default_rules:
        :return:
        :rtype:
        """
        super().__init__()
        self.disabled: Callable[[dict[str, Any] | None], bool]
        if not callable(disabled):
            self.disabled = lambda context: disabled
        else:
            self.disabled = disabled
        self._patterns: list[Pattern] = []
        self._rules = Rules()
        if default_rules:
            self.rules(ConflictSolver, PrivateRemover)
        self._rebulks: list[Rebulk] = []

    def pattern(self, *pattern: Pattern) -> Self:
        """
        Add patterns objects

        :param pattern:
        :type pattern: rebulk.pattern.Pattern
        :return: self
        :rtype: Rebulk
        """
        self._patterns.extend(pattern)
        return self

    def rules(self, *rules: CustomRule | type[CustomRule] | Any) -> Self:
        """
        Add rules as a module, class or instance.
        :param rules:
        :type rules: list[Rule]
        :return:
        """
        self._rules.load(*rules)
        return self

    def rebulk(self, *rebulks: Rebulk) -> Self:
        """
        Add a children rebulk object
        :param rebulks:
        :type rebulks: Rebulk
        :return:
        """
        self._rebulks.extend(rebulks)
        return self

    def matches(self, string: str, context: dict[str, Any] | None = None) -> Matches:
        """
        Search for all matches with current configuration against input_string
        :param string: string to search into
        :type string: str
        :param context: context to use
        :type context: dict
        :return: A custom list of matches
        :rtype: Matches
        """
        matches = Matches(input_string=string)
        if context is None:
            context = {}

        if not self.disabled(context):
            matches.declared_keys = self.effective_keys(context)

        self._matches_patterns(matches, context)

        # Validate formatter output against declared Key.value_type *before* rules
        # run: the contract is about the value a pattern's formatter produced, not
        # about matches that a rule later renames/relocates onto a declared name.
        if debug.CHECK_DECLARED_KEYS:
            matches.check_declared_keys()

        self._execute_rules(matches, context)

        return matches

    def effective_rules(self, context: dict[str, Any] | None = None) -> Rules:
        """
        Get effective rules for this rebulk object and its children.
        :param context:
        :type context:
        :return:
        :rtype:
        """
        rules = Rules()
        rules.extend(self._rules)
        for rebulk in self._rebulks:
            if not rebulk.disabled(context):
                extend_safe(rules, rebulk._rules)
        return rules

    def effective_keys(self, context: dict[str, Any] | None = None) -> dict[str, Key[Any]]:
        """
        Get effective declared keys for this rebulk object and its children.

        Keys declared on a child rebulk are merged in (without overriding the
        parent's), so the returned registry mirrors the patterns actually run.
        :param context:
        :type context:
        :return:
        :rtype:
        """
        keys: dict[str, Key[Any]] = dict(self._keys)
        for rebulk in self._rebulks:
            if not rebulk.disabled(context):
                for name, key in rebulk._keys.items():
                    keys.setdefault(name, key)
        return keys

    def check_keys(self, *, allowed_unused: str | Iterable[str] = ()) -> list[str]:
        """
        Return declared key names that no built pattern can produce (typo guard).

        A declared :class:`~rebulk.key.Key` binds its converter/type to a match
        name (see :meth:`~rebulk.builder.PatternFactory.declare_keys`); a typo or
        a name kept after its pattern was removed silently no-ops. This compares
        every declared key name against the names every pattern *can* emit — its
        ``name`` plus regex group names, across this rebulk and its children —
        and returns the declared names matched by none, sorted.

        The full pattern set is considered regardless of ``disabled`` (a key
        whose patterns are all disabled by config is still legitimately declared),
        so the result is deterministic and config-independent: ideal to assert in
        a test (``assert not rb.check_keys()``) so a typo fails fast in CI rather
        than silently doing nothing.

        Only names a *pattern* can emit are considered (its ``name``, regex group
        names, and declared ``properties``). A name produced solely by a rule
        (e.g. ``RenameMatch``/``AppendMatch``) or dynamically by a functional
        pattern is not detectable statically; pass such names — and any other
        intentionally pattern-less key — via ``allowed_unused`` (a single name or
        an iterable of names) to exempt them.
        """
        declared: dict[str, Key[Any]] = dict(self._keys)
        patterns: list[Pattern] = list(self._patterns)
        for rebulk in self._rebulks:
            for name, key in rebulk._keys.items():
                declared.setdefault(name, key)
            patterns.extend(rebulk._patterns)
        if not declared:
            return []
        produced: set[str] = set()
        for pattern in patterns:
            produced |= _producible_names(pattern)
        allowed = {allowed_unused} if isinstance(allowed_unused, str) else set(allowed_unused)
        return sorted(name for name in declared if name not in produced and name not in allowed)

    def _execute_rules(self, matches: Matches, context: dict[str, Any]) -> None:
        """
        Execute rules for this rebulk and children.
        :param matches:
        :type matches:
        :param context:
        :type context:
        :return:
        :rtype:
        """
        if not self.disabled(context):
            rules = self.effective_rules(context)
            rules.execute_all_rules(matches, context)

    def effective_patterns(self, context: dict[str, Any] | None = None) -> list[Pattern]:
        """
        Get effective patterns for this rebulk object and its children.
        :param context:
        :type context:
        :return:
        :rtype:
        """
        patterns = list(self._patterns)
        for rebulk in self._rebulks:
            if not rebulk.disabled(context):
                extend_safe(patterns, rebulk._patterns)
        return patterns

    def _matches_patterns(self, matches: Matches, context: dict[str, Any]) -> None:
        """
        Search for all matches with current paterns agains input_string
        :param matches: matches list
        :type matches: Matches
        :param context: context to use
        :type context: dict
        :return:
        :rtype:
        """
        if not self.disabled(context):
            patterns = self.effective_patterns(context)
            for pattern in patterns:
                if not pattern.disabled(context):
                    pattern_matches = pattern.matches(cast("str", matches.input_string), context)
                    if pattern_matches:
                        log(pattern.log_level, "Pattern has %s match(es). (%s)", len(pattern_matches), pattern)
                    for match in pattern_matches:
                        if match.marker:
                            log(pattern.log_level, "Marker found. (%s)", match)
                            matches.markers.append(match)
                        else:
                            log(pattern.log_level, "Match found. (%s)", match)
                            matches.append(match)
                else:
                    log(pattern.log_level, "Pattern is disabled. (%s)", pattern)
