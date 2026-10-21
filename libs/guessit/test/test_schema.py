#!/usr/bin/env python
"""Tests for the machine-readable property schema."""

from __future__ import annotations

import functools
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from guessit import api
from guessit.schema_builder import overlay_config_enums
from guessit.schema_generated import GUESSIT_SCHEMA
from guessit.yamlutils import OrderedDictYAMLLoader

ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DIR = ROOT / "guessit" / "test"
OUTPUT_SCHEMA_JSON = ROOT / "guessit" / "data" / "output-schema.json"
PROPERTIES_DOC = ROOT / "docs" / "properties.md"


def _corpus_inputs() -> list[str]:
    """Every input string from the YAML corpus, token prefixes stripped."""
    token_prefix = re.compile(r"^[ +-]+")
    inputs: list[str] = []
    for path in sorted(TEST_DIR.rglob("*.yml")) + sorted(TEST_DIR.rglob("*.yaml")):
        with open(path, encoding="utf-8") as stream:
            data = yaml.load(stream, OrderedDictYAMLLoader)
        if not isinstance(data, dict):
            continue
        for key in data:
            text = key if isinstance(key, str) else str(key)
            inputs.append(token_prefix.sub("", text))
    return inputs


@functools.lru_cache(maxsize=1)
def _load_generator() -> Any:
    """Import scripts/gen_schema.py (a standalone script, not an installed module)."""
    spec = importlib.util.spec_from_file_location("gen_schema", ROOT / "scripts" / "gen_schema.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@functools.lru_cache(maxsize=1)
def _corpus_guesses() -> tuple[tuple[str, dict[str, Any]], ...]:
    """Guess every corpus input once; reused across the corpus-sweep tests."""
    results: list[tuple[str, dict[str, Any]]] = []
    for string in _corpus_inputs():
        try:
            results.append((string, api.guessit(string)))
        except Exception:  # a single bad input must not abort the sweep
            continue
    return tuple(results)


@functools.lru_cache(maxsize=1)
def _built_schema() -> Any:
    """Run the generator once; reused across the drift tests."""
    return _load_generator().build_schema()


def test_properties_advertises_every_schema_property() -> None:
    props = api.properties()
    for name in GUESSIT_SCHEMA:
        assert name in props, f"properties() missing {name}"
    assert len(props) == len(GUESSIT_SCHEMA)


def test_properties_doc_documents_every_schema_property() -> None:
    """docs/properties.md must carry an entry for every schema property."""
    doc = PROPERTIES_DOC.read_text(encoding="utf-8")
    documented = {match.replace("\\", "") for match in re.findall(r"\*\*([^*]+)\*\*", doc)}
    missing = [name for name in GUESSIT_SCHEMA if name not in documented]
    assert not missing, f"docs/properties.md missing entries for: {sorted(missing)}"


def test_value_constrained_properties_expose_a_non_empty_enum() -> None:
    assert "Blu-ray" in GUESSIT_SCHEMA["source"]["enum"]
    assert GUESSIT_SCHEMA["type"]["enum"] == ["episode", "movie"]
    assert "H.264" in GUESSIT_SCHEMA["video_codec"]["enum"]
    assert "Web" in api.properties()["source"]


def test_enums_are_code_complete() -> None:
    # These source values are declared in the rules but absent from the corpus;
    # the enum must still list them (introspection-driven completeness).
    for value in ["Workprint", "Telecine", "Telesync", "Pay-per-view", "Video on Demand"]:
        assert value in GUESSIT_SCHEMA["source"]["enum"], f"source enum missing {value}"


def test_every_emitted_property_is_in_the_schema() -> None:
    unknown: set[str] = set()
    for _string, guess in _corpus_guesses():
        unknown.update(key for key in guess if key not in GUESSIT_SCHEMA)
    assert not unknown, f"emitted properties absent from schema: {sorted(unknown)}"


def test_every_emitted_enum_value_is_allowed() -> None:
    violations: list[str] = []
    for string, guess in _corpus_guesses():
        for key, value in guess.items():
            spec = GUESSIT_SCHEMA.get(key)
            enum = spec.get("enum") if spec else None
            if not enum:
                continue
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, str | int) and not isinstance(item, bool) and item not in enum:
                    violations.append(f"{key}={item!r} ({string[:60]})")
    assert not violations, f"emitted values not in schema enum: {violations[:10]}"


def test_output_schema_json_is_draft07_describing_all_properties() -> None:
    with open(OUTPUT_SCHEMA_JSON, encoding="utf-8") as stream:
        output_schema = json.load(stream)
    assert "draft-07" in output_schema["$schema"]
    for name in GUESSIT_SCHEMA:
        assert name in output_schema["properties"], f"JSON schema missing {name}"


def test_guessit_schema_constant_is_deprecated() -> None:
    """The public ``guessit.GUESSIT_SCHEMA`` still works but warns; ``schema()`` replaces it."""
    import guessit

    with pytest.warns(DeprecationWarning, match="GUESSIT_SCHEMA"):
        deprecated = guessit.GUESSIT_SCHEMA
    assert deprecated == GUESSIT_SCHEMA


def test_schema_accessor_without_options_matches_frozen_schema() -> None:
    result = api.schema()
    assert result == GUESSIT_SCHEMA
    assert result is not GUESSIT_SCHEMA  # a copy, never the shared constant


def test_json_schema_accessor_without_options_matches_committed_file() -> None:
    with open(OUTPUT_SCHEMA_JSON, encoding="utf-8") as stream:
        committed = json.load(stream)
    assert api.json_schema() == committed


def test_schema_accessor_is_configuration_aware() -> None:
    """A custom advanced_config vocabulary is overlaid onto the enums, defaults kept."""
    options = {"advanced_config": {"streaming_service": {"MyOwnTV": "myowntv"}}}

    enum = api.schema(options)["streaming_service"]["enum"]
    assert "MyOwnTV" in enum
    assert "Netflix" in enum  # a default value is never dropped

    json_enum = api.json_schema(options)["properties"]["streaming_service"]["enum"]
    assert "MyOwnTV" in json_enum

    # Type and cardinality are configuration invariants.
    assert api.schema(options)["streaming_service"]["array"] == GUESSIT_SCHEMA["streaming_service"]["array"]
    assert "MyOwnTV" not in GUESSIT_SCHEMA["streaming_service"]["enum"]  # the constant stays untouched


def test_overlay_adds_property_absent_from_the_base() -> None:
    """A property surfaced by a custom rules_builder (absent from the frozen base) is added
    with an inferred type; free-form values yield no enum."""
    base = {"title": {"type": ["string"], "array": False, "scalar": True}}
    properties = {"title": [None], "custom_index": [1, 2, 3], "custom_free": [None]}

    result = overlay_config_enums(base, properties)

    assert result["custom_index"] == {"type": ["number"], "array": False, "scalar": True, "enum": [1, 2, 3]}
    assert result["custom_free"] == {"type": ["string"], "array": False, "scalar": True}
    assert list(result) == sorted(result)  # keys stay alphabetically ordered


def test_schema_py_is_not_stale() -> None:
    """guessit/schema_generated.py must match what scripts/gen_schema.py produces."""
    assert _built_schema() == GUESSIT_SCHEMA


def test_output_schema_json_is_not_stale() -> None:
    """guessit/data/output-schema.json must match the generator output."""
    expected = _load_generator().build_json_schema(_built_schema())
    with open(OUTPUT_SCHEMA_JSON, encoding="utf-8") as stream:
        committed = json.load(stream)
    assert committed == expected
