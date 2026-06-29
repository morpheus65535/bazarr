"""Universal character encoding detector — 0BSD-licensed rewrite."""

from __future__ import annotations

from collections.abc import Iterable

from chardet._utils import (
    _DEFAULT_CHUNK_SIZE,
    DEFAULT_MAX_BYTES,
    MINIMUM_THRESHOLD,
    _resolve_prefer_superset,
    _validate_max_bytes,
    _warn_deprecated_chunk_size,
)
from chardet._version import __version__
from chardet.detector import UniversalDetector
from chardet.enums import EncodingEra, LanguageFilter
from chardet.equivalences import apply_compat_names, apply_preferred_superset
from chardet.pipeline import DetectionDict, DetectionResult
from chardet.pipeline.orchestrator import run_pipeline
from chardet.registry import _validate_encoding, normalize_encodings

__all__ = [
    "DEFAULT_MAX_BYTES",
    "MINIMUM_THRESHOLD",
    "DetectionDict",
    "DetectionResult",
    "EncodingEra",
    "LanguageFilter",
    "UniversalDetector",
    "__version__",
    "detect",
    "detect_all",
]


def detect(  # noqa: PLR0913
    byte_str: bytes | bytearray,
    should_rename_legacy: bool = False,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    prefer_superset: bool = False,
    compat_names: bool = True,
    include_encodings: Iterable[str] | None = None,
    exclude_encodings: Iterable[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
) -> DetectionDict:
    """Detect the encoding of the given byte string.

    :param byte_str: The byte sequence to detect encoding for.
    :param should_rename_legacy: Deprecated alias for *prefer_superset*.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param chunk_size: Deprecated -- accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :param prefer_superset: If ``True``, remap ISO subset encodings to their
        Windows/CP superset equivalents (e.g., ISO-8859-1 -> Windows-1252).
    :param compat_names: If ``True`` (default), return encoding names
        compatible with chardet 5.x/6.x.  If ``False``, return raw Python
        codec names.
    :param include_encodings: If given, restrict detection to only these
        encodings (names or aliases).
    :param exclude_encodings: If given, remove these encodings from the
        candidate set.
    :param no_match_encoding: Encoding to return when no candidate survives
        the pipeline.  Defaults to ``"cp1252"``.
    :param empty_input_encoding: Encoding to return for empty input.  Defaults
        to ``"utf-8"``.
    :returns: A dictionary with keys ``"encoding"``, ``"confidence"``, and
        ``"language"``.
    """
    _warn_deprecated_chunk_size(chunk_size)
    _validate_max_bytes(max_bytes)
    prefer_superset = _resolve_prefer_superset(should_rename_legacy, prefer_superset)
    include = normalize_encodings(include_encodings, "include_encodings")
    exclude = normalize_encodings(exclude_encodings, "exclude_encodings")
    no_match = _validate_encoding(no_match_encoding, "no_match_encoding")
    empty = _validate_encoding(empty_input_encoding, "empty_input_encoding")
    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    results = run_pipeline(
        data,
        encoding_era,
        max_bytes=max_bytes,
        include_encodings=include,
        exclude_encodings=exclude,
        no_match_encoding=no_match,
        empty_input_encoding=empty,
    )
    result = results[0].to_dict()
    if prefer_superset:
        apply_preferred_superset(result)
    if compat_names:
        apply_compat_names(result)
    return result


def detect_all(  # noqa: PLR0913
    byte_str: bytes | bytearray,
    ignore_threshold: bool = False,
    should_rename_legacy: bool = False,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    prefer_superset: bool = False,
    compat_names: bool = True,
    include_encodings: Iterable[str] | None = None,
    exclude_encodings: Iterable[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
) -> list[DetectionDict]:
    """Detect all possible encodings of the given byte string.

    When *ignore_threshold* is False (the default), results with confidence
    <= MINIMUM_THRESHOLD (0.20) are filtered out.  If all results are below
    the threshold, the full unfiltered list is returned as a fallback so the
    caller always receives at least one result.

    :param byte_str: The byte sequence to detect encoding for.
    :param ignore_threshold: If ``True``, return all candidate encodings
        regardless of confidence score.
    :param should_rename_legacy: Deprecated alias for *prefer_superset*.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param chunk_size: Deprecated -- accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :param prefer_superset: If ``True``, remap ISO subset encodings to their
        Windows/CP superset equivalents.
    :param compat_names: If ``True`` (default), return encoding names
        compatible with chardet 5.x/6.x.  If ``False``, return raw Python
        codec names.
    :param include_encodings: If given, restrict detection to only these
        encodings (names or aliases).
    :param exclude_encodings: If given, remove these encodings from the
        candidate set.
    :param no_match_encoding: Encoding to return when no candidate survives
        the pipeline.  Defaults to ``"cp1252"``.
    :param empty_input_encoding: Encoding to return for empty input.  Defaults
        to ``"utf-8"``.
    :returns: A list of dictionaries, sorted by descending confidence.
    """
    _warn_deprecated_chunk_size(chunk_size)
    _validate_max_bytes(max_bytes)
    prefer_superset = _resolve_prefer_superset(should_rename_legacy, prefer_superset)
    include = normalize_encodings(include_encodings, "include_encodings")
    exclude = normalize_encodings(exclude_encodings, "exclude_encodings")
    no_match = _validate_encoding(no_match_encoding, "no_match_encoding")
    empty = _validate_encoding(empty_input_encoding, "empty_input_encoding")
    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    results = run_pipeline(
        data,
        encoding_era,
        max_bytes=max_bytes,
        include_encodings=include,
        exclude_encodings=exclude,
        no_match_encoding=no_match,
        empty_input_encoding=empty,
    )
    dicts = [r.to_dict() for r in results]
    if not ignore_threshold:
        filtered = [d for d in dicts if d["confidence"] > MINIMUM_THRESHOLD]
        if filtered:
            dicts = filtered
    for d in dicts:
        if prefer_superset:
            apply_preferred_superset(d)
        if compat_names:
            apply_compat_names(d)
    return sorted(dicts, key=lambda d: d["confidence"], reverse=True)
