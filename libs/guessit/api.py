#!/usr/bin/env python
"""
API functions that can be used by external software
"""

from __future__ import annotations

import os
import traceback
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from rebulk.introspector import introspect

from .__version__ import __version__
from .options import load_config, merge_options, parse_options
from .rules import rebulk_builder
from .schema_builder import build_json_schema, overlay_config_enums
from .schema_generated import GUESSIT_SCHEMA

if TYPE_CHECKING:
    from collections.abc import Callable

    from rebulk import Rebulk


class GuessitException(Exception):
    """
    Exception raised when guessit fails to perform a guess because of an internal error.
    """

    def __init__(self, string: Any, options: Any) -> None:
        super().__init__(
            "An internal error has occurred in guessit.\n"
            "===================== Guessit Exception Report =====================\n"
            f"version={__version__}\n"
            f"string={string!s}\n"
            f"options={options!s}\n"
            "--------------------------------------------------------------------\n"
            f"{traceback.format_exc()}"
            "--------------------------------------------------------------------\n"
            "Please report at "
            "https://github.com/guessit-io/guessit/issues.\n"
            "===================================================================="
        )

        self.string = string
        self.options = options


def configure(options: Any = None, rules_builder: Callable[..., Rebulk] | None = None, force: bool = False) -> None:
    """
    Load configuration files and initialize rebulk rules if required.

    :param options:
    :type options: dict
    :param rules_builder:
    :type rules_builder:
    :param force:
    :type force: bool
    :return:
    """
    default_api.configure(options, rules_builder=rules_builder, force=force)


def reset() -> None:
    """
    Reset api internal state.
    """
    default_api.reset()


def guessit(string: str | Path | bytes, options: Any = None) -> dict[str, Any]:
    """
    Retrieves all matches from string as a dict
    :param string: the filename or release name
    :type string: str
    :param options:
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.guessit(string, options)


def properties(options: Any = None) -> dict[str, Any]:
    """
    Retrieves all properties with possible values that can be guessed
    :param options:
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.properties(options)


def schema(options: Any = None) -> dict[str, Any]:
    """
    Retrieve the property schema (type, cardinality and enums) for the effective configuration
    :param options:
    :type options: str|dict
    :return:
    :rtype: dict
    """
    return default_api.schema(options)


def json_schema(options: Any = None) -> dict[str, Any]:
    """
    Retrieve the draft-07 JSON Schema of the output for the effective configuration
    :param options:
    :type options: str|dict
    :return:
    :rtype: dict
    """
    return default_api.json_schema(options)


def suggested_expected(titles: Any, options: Any = None) -> list[Any]:
    """
    Return a list of suggested titles to be used as `expected_title` based on the list of titles
    :param titles: the filename or release name
    :type titles: list|set|dict
    :param options:
    :type options: str|dict
    :return:
    :rtype: list of str
    """
    return default_api.suggested_expected(titles, options)


def _complete_properties(ordered: dict[str, Any]) -> dict[str, Any]:
    """Make ``properties()`` code-complete against :data:`GUESSIT_SCHEMA`.

    Value-constrained properties advertise their full declared enum (unioned with
    whatever introspection found); every other schema property is guaranteed to be
    present, with ``[None]`` marking a free/computed value.
    """
    for name, spec in GUESSIT_SCHEMA.items():
        current = ordered.get(name) or []
        enum = spec.get("enum")
        if enum:
            # Union, deduplicating scalars while preserving any compound values
            # already present (e.g. edition's ['Ultimate', 'Collector']).
            merged = list(current)
            seen = {value for value in current if not isinstance(value, list)}
            for value in enum:
                if value not in seen:
                    merged.append(value)
                    seen.add(value)
            ordered[name] = sorted(merged, key=str)
        elif not current:
            ordered[name] = [None]
    # Newly added keys are appended; re-sort so the key order stays alphabetical
    # (the contract introspection already followed before completion).
    return dict(sorted(ordered.items(), key=lambda item: str(item[0])))


class GuessItApi:
    """
    An api class that can be configured with custom Rebulk configuration.
    """

    def __init__(self) -> None:
        """Default constructor."""
        self.rebulk: Rebulk | None = None
        self.config: dict[str, Any] | None = None
        self.load_config_options: Any = None
        self.advanced_config: Any = None
        self.effective_options: dict[str, Any] | None = None
        self.effective_options_input: Any = None

    def reset(self) -> None:
        """
        Reset api internal state.
        """
        self.__init__()  # type: ignore[misc]

    @classmethod
    def _fix_encoding(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [cls._fix_encoding(item) for item in value]
        if isinstance(value, dict):
            return {cls._fix_encoding(k): cls._fix_encoding(v) for k, v in value.items()}
        if isinstance(value, bytes):
            return value.decode("ascii")
        return value

    @classmethod
    def _has_same_properties(cls, dic1: dict[str, Any], dic2: dict[str, Any], values: list[str]) -> bool:
        return all(dic1.get(value) == dic2.get(value) for value in values)

    def configure(
        self,
        options: Any = None,
        rules_builder: Callable[..., Rebulk] | None = None,
        force: bool = False,
        sanitize_options: bool = True,
    ) -> dict[str, Any]:
        """
        Load configuration files and initialize rebulk rules if required.

        :param options:
        :type options: str|dict
        :param rules_builder:
        :type rules_builder:
        :param force:
        :type force: bool
        :param sanitize_options:
        :type force: bool
        :return:
        :rtype: dict
        """
        if not rules_builder:
            rules_builder = rebulk_builder

        if sanitize_options:
            options = parse_options(options, True)
            options = self._fix_encoding(options)

        config_reloaded = (
            self.config is None
            or self.load_config_options is None
            or force
            or not self._has_same_properties(
                self.load_config_options, options, ["config", "no_user_config", "no_default_config"]
            )
        )
        if config_reloaded:
            config = load_config(options)
            config = self._fix_encoding(config)
            self.load_config_options = options
        else:
            assert self.config is not None
            config = self.config

        # merge_options deep-copies advanced_config, and the effective options embed it again; both are
        # unchanged while nothing that feeds them changes, so reuse them across repeated calls.
        if (
            not force
            and not config_reloaded
            and self.rebulk is not None
            and self.effective_options is not None
            and self.effective_options_input == options
        ):
            return config

        advanced_config = merge_options(config.get("advanced_config"), options.get("advanced_config"))

        should_build_rebulk = (
            force or not self.rebulk or not self.advanced_config or self.advanced_config != advanced_config
        )

        if should_build_rebulk:
            self.advanced_config = deepcopy(advanced_config)
            self.rebulk = rules_builder(advanced_config)

        self.config = config
        self.effective_options = merge_options(config, options)
        self.effective_options_input = options
        return self.config

    def guessit(self, string: str | Path | bytes, options: Any = None) -> dict[str, Any]:
        """
        Retrieves all matches from string as a dict
        :param string: the filename or release name
        :type string: str|Path
        :param options:
        :type options: str|dict
        :return:
        :rtype:
        """
        if string is None:
            # A bare None is almost always an accidental call (e.g. a missing filename); fail with a
            # clear message instead of the cryptic internal error report wrapped by GuessitException.
            raise TypeError("guessit() requires a filename string, got None")
        if isinstance(string, Path):
            try:
                # Handle path-like object
                string = os.fspath(string)
            except AttributeError:
                string = str(string)

        try:
            options = parse_options(options, True)
            options = self._fix_encoding(options)
            self.configure(options, sanitize_options=False)
            assert self.effective_options is not None
            options = self.effective_options
            result_decode = False
            result_encode = False

            if isinstance(string, bytes):
                string = string.decode("ascii")
                result_encode = True

            assert self.rebulk is not None
            matches = self.rebulk.matches(string, options)
            if result_decode:
                for match in matches:
                    if isinstance(match.value, bytes):
                        match.value = match.value.decode("utf-8")
            if result_encode:
                for match in matches:
                    if isinstance(match.value, str):
                        match.value = match.value.encode("ascii")
            matches_dict = matches.to_dict(
                options.get("advanced", False), options.get("single_value", False), options.get("enforce_list", False)
            )
            output_input_string = options.get("output_input_string", False)
            if output_input_string:
                matches_dict["input_string"] = matches.input_string
            # rebulk 6 types MatchesDict keys as ``str | None``; every guessit
            # property (and ``input_string``) is named, so the keys are always ``str``.
            return cast("dict[str, Any]", matches_dict)
        except Exception as err:
            raise GuessitException(string, options) from err

    def properties(self, options: Any = None) -> dict[str, Any]:
        """
        Grab properties and values that can be generated.
        :param options:
        :type options:
        :return:
        :rtype:
        """
        options = parse_options(options, True)
        options = self._fix_encoding(options)
        self.configure(options, sanitize_options=False)
        assert self.effective_options is not None
        options = self.effective_options
        assert self.rebulk is not None
        unordered = introspect(self.rebulk, options).properties
        ordered = OrderedDict()
        for k in sorted(unordered.keys(), key=str):
            ordered[k] = sorted(unordered[k], key=str)
        if hasattr(self.rebulk, "customize_properties"):
            ordered = self.rebulk.customize_properties(ordered)
        return _complete_properties(ordered)

    def schema(self, options: Any = None) -> dict[str, Any]:
        """
        Grab the property schema (type, cardinality and enums) for the effective configuration.

        The type and cardinality of every property are configuration invariants, taken from the
        frozen :data:`GUESSIT_SCHEMA`; only the closed-vocabulary enums depend on the configuration
        and are overlaid from :meth:`properties`. With no options this returns a copy of
        :data:`GUESSIT_SCHEMA`.

        :param options:
        :type options: str|dict
        :return:
        :rtype: dict
        """
        if options is None:
            return deepcopy(GUESSIT_SCHEMA)
        return overlay_config_enums(GUESSIT_SCHEMA, self.properties(options))

    def json_schema(self, options: Any = None) -> dict[str, Any]:
        """
        Grab the draft-07 JSON Schema of the output for the effective configuration.

        With no options this equals the committed ``guessit/data/output-schema.json``.

        :param options:
        :type options: str|dict
        :return:
        :rtype: dict
        """
        return build_json_schema(self.schema(options))

    def suggested_expected(self, titles: Any, options: Any = None) -> list[Any]:
        """
        Return a list of suggested titles to be used as `expected_title` based on the list of titles
        :param titles: the filename or release name
        :type titles: list|set|dict
        :param options:
        :type options: str|dict
        :return:
        :rtype: list of str
        """
        suggested: list[Any] = []
        for title in titles:
            guess = self.guessit(title, options)
            if len(guess) != 2 or "title" not in guess:
                suggested.append(title)

        return suggested


default_api = GuessItApi()
