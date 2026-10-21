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
from chardet.output_names import apply_compat_names, apply_preferred_superset
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


def __getattr__(name: str) -> object:
    """Resolve the deprecated ``chardet.equivalences`` submodule on demand.

    Before the 7.5 split, ``chardet/__init__.py`` imported that module for
    its own use, which as a side effect made ``chardet.equivalences`` work
    without an explicit ``import chardet.equivalences``.  This package now
    imports :mod:`chardet.output_names` instead, so the attribute is bound
    lazily here: importing the shim eagerly would fire its deprecation
    warning on every ``import chardet``.
    """
    if name == "equivalences":
        # ``from chardet import equivalences`` would re-enter this function:
        # the import machinery probes the parent package with ``hasattr``
        # first.  Kept local so the shim stays off the eager import path.
        import importlib  # noqa: PLC0415

        return importlib.import_module("chardet.equivalences")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


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
    :param prefer_superset: If ``True``, remap subset encodings in the result
        to their decode-safe Windows/CP superset equivalents (e.g.,
        ISO-8859-1 -> Windows-1252, EUC-KR -> CP949).  Recommended when the
        result will be used to decode: detection examines at most
        *max_bytes* of input, and only the superset is guaranteed to decode
        bytes beyond that window.  The remap is skipped when the superset
        cannot decode the examined window itself (the Windows code pages
        leave a few C1 positions undefined that the ISO subsets map), so
        the reported name always decodes what was examined.  If ``False``
        (default), the detected
        encoding is reported under its own name --- note this only skips
        the renaming step; it is not a promise of the *smallest* matching
        encoding, since detection may natively choose a superset that fits
        the data better.  The default will change to ``True`` in chardet
        8.0; pass ``False`` explicitly if you depend on subset names.
    :param compat_names: If ``True`` (default), return encoding names
        compatible with chardet 5.x/6.x.  If ``False``, return raw Python
        codec names.
    :param include_encodings: If given, restrict detection to only these
        encodings (names or aliases).
    :param exclude_encodings: If given, remove these encodings from the
        candidate set.
    :param no_match_encoding: Encoding to return when no candidate survives
        the pipeline.  Defaults to ``"cp1252"``.  It is returned as given,
        at confidence 0.10, and is the one answer that is not checked
        against the data: it is the caller's sentinel for "nothing fit".
    :param empty_input_encoding: Encoding to return for empty input.  Defaults
        to ``"utf-8"``.
    :returns: A dictionary with keys ``"encoding"``, ``"confidence"``,
        ``"language"``, and ``"mime_type"``.
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
    window = data[:max_bytes]
    if prefer_superset:
        apply_preferred_superset(
            result,
            window,
            include_encodings=include,
            exclude_encodings=exclude,
        )
    if compat_names:
        apply_compat_names(result, window)
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
    :param prefer_superset: If ``True``, remap subset encodings in the
        results to their decode-safe Windows/CP superset equivalents.
        If ``False`` (default), skip the renaming --- not a promise of the
        smallest matching encoding.  The default will change to ``True``
        in chardet 8.0.  See :func:`detect` for details.
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
    :returns: A list of dictionaries, sorted by descending confidence, one
        per encoding name.
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
        full_ranking=True,
    )
    dicts = [r.to_dict() for r in results]
    if not ignore_threshold:
        filtered = [d for d in dicts if d["confidence"] > MINIMUM_THRESHOLD]
        if filtered:
            dicts = filtered
    window = data[:max_bytes]
    for d in dicts:
        if prefer_superset:
            apply_preferred_superset(
                d, window, include_encodings=include, exclude_encodings=exclude
            )
        if compat_names:
            apply_compat_names(d, window)
    dicts.sort(key=lambda d: d["confidence"], reverse=True)
    # The superset remap can land two candidates on one name (ISO-8859-7
    # and Windows-1253 both become Windows-1253).  Keep the first, which
    # carries the higher confidence; the sort is stable, so ties keep the
    # pipeline's order.
    seen: set[str | None] = set()
    unique: list[DetectionDict] = []
    for d in dicts:
        if d["encoding"] not in seen:
            seen.add(d["encoding"])
            unique.append(d)
    return unique
