"""UniversalDetector — streaming encoding detection."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from types import MappingProxyType
from typing import ClassVar

from chardet import _utils
from chardet._utils import (
    DEFAULT_MAX_BYTES,
    _resolve_prefer_superset,
    _validate_max_bytes,
)
from chardet.enums import EncodingEra, LanguageFilter
from chardet.equivalences import (
    PREFERRED_SUPERSET,
    apply_compat_names,
    apply_preferred_superset,
)
from chardet.pipeline import _NONE_RESULT, DetectionDict, DetectionResult
from chardet.pipeline.orchestrator import run_pipeline
from chardet.registry import _validate_encoding, normalize_encodings


class UniversalDetector:
    """Streaming character encoding detector.

    Implements a feed/close pattern for incremental detection of character
    encoding from byte streams.  Compatible with the chardet 6.x API.

    All detection is performed by the same pipeline used by
    :func:`chardet.detect` and :func:`chardet.detect_all`, ensuring
    consistent results regardless of which API is used.

    .. note::

        This class is **not** thread-safe.  Each thread should create its own
        :class:`UniversalDetector` instance.
    """

    MINIMUM_THRESHOLD = _utils.MINIMUM_THRESHOLD
    # Exposed for backward compatibility with chardet 6.x callers that
    # reference UniversalDetector.LEGACY_MAP directly.
    LEGACY_MAP: ClassVar[MappingProxyType[str, str]] = MappingProxyType(
        PREFERRED_SUPERSET
    )

    def __init__(  # noqa: PLR0913
        self,
        lang_filter: LanguageFilter = LanguageFilter.ALL,
        should_rename_legacy: bool = False,
        encoding_era: EncodingEra = EncodingEra.ALL,
        max_bytes: int = DEFAULT_MAX_BYTES,
        *,
        prefer_superset: bool = False,
        compat_names: bool = True,
        include_encodings: Iterable[str] | None = None,
        exclude_encodings: Iterable[str] | None = None,
        no_match_encoding: str = "cp1252",
        empty_input_encoding: str = "utf-8",
    ) -> None:
        """Initialize the detector.

        :param lang_filter: Deprecated -- accepted for backward compatibility
            but has no effect.  A warning is emitted when set to anything
            other than :attr:`LanguageFilter.ALL`.
        :param should_rename_legacy: Deprecated alias for *prefer_superset*.
        :param encoding_era: Restrict candidate encodings to the given era.
        :param max_bytes: Maximum number of bytes to buffer from
            :meth:`feed` calls before stopping accumulation.
        :param prefer_superset: If ``True``, remap ISO subset encodings to
            their Windows/CP superset equivalents (e.g., ISO-8859-1 ->
            Windows-1252).
        :param compat_names: If ``True`` (default), return encoding names
            compatible with chardet 5.x/6.x.  If ``False``, return raw Python
            codec names.
        :param include_encodings: If given, restrict detection to only these
            encodings (names or aliases).
        :param exclude_encodings: If given, remove these encodings from the
            candidate set.
        :param no_match_encoding: Encoding to return when no candidate
            survives the pipeline.  Defaults to ``"cp1252"``.
        :param empty_input_encoding: Encoding to return for empty input.
            Defaults to ``"utf-8"``.
        """
        if lang_filter != LanguageFilter.ALL:
            warnings.warn(
                "lang_filter is not implemented in this version of chardet "
                "and will be ignored",
                DeprecationWarning,
                stacklevel=2,
            )
        prefer_superset = _resolve_prefer_superset(
            should_rename_legacy, prefer_superset
        )
        self._prefer_superset = prefer_superset
        self._compat_names = compat_names
        _validate_max_bytes(max_bytes)
        self._encoding_era = encoding_era
        self._max_bytes = max_bytes
        self._include_encodings = normalize_encodings(
            include_encodings, "include_encodings"
        )
        self._exclude_encodings = normalize_encodings(
            exclude_encodings, "exclude_encodings"
        )
        self._no_match_encoding = _validate_encoding(
            no_match_encoding, "no_match_encoding"
        )
        self._empty_input_encoding = _validate_encoding(
            empty_input_encoding, "empty_input_encoding"
        )
        self._buffer = bytearray()
        self._done = False
        self._closed = False
        self._result: DetectionResult | None = None

    def feed(self, byte_str: bytes | bytearray) -> None:
        """Feed a chunk of bytes to the detector.

        Data is accumulated in an internal buffer.  Once *max_bytes* have
        been buffered, :attr:`done` is set to ``True`` and further data is
        ignored until :meth:`reset` is called.

        :param byte_str: The next chunk of bytes to examine.
        :raises ValueError: If called after :meth:`close` without a
            :meth:`reset`.
        """
        if self._closed:
            msg = "feed() called after close() without reset()"
            raise ValueError(msg)
        if self._done:
            return
        remaining = self._max_bytes - len(self._buffer)
        if remaining > 0:
            self._buffer.extend(byte_str[:remaining])
        if len(self._buffer) >= self._max_bytes:
            self._done = True

    def close(self) -> DetectionDict:
        """Finalize detection and return the best result.

        Runs the full detection pipeline on the buffered data.

        :returns: A dictionary with keys ``"encoding"``, ``"confidence"``,
            and ``"language"``.
        """
        if not self._closed:
            self._closed = True
            data = bytes(self._buffer)
            results = run_pipeline(
                data,
                self._encoding_era,
                max_bytes=self._max_bytes,
                include_encodings=self._include_encodings,
                exclude_encodings=self._exclude_encodings,
                no_match_encoding=self._no_match_encoding,
                empty_input_encoding=self._empty_input_encoding,
            )
            self._result = results[0]
            self._done = True
        return self.result

    def reset(self) -> None:
        """Reset the detector to its initial state for reuse."""
        self._buffer = bytearray()
        self._done = False
        self._closed = False
        self._result = None

    @property
    def done(self) -> bool:
        """Whether detection is complete and no more data is needed."""
        return self._done

    @property
    def result(self) -> DetectionDict:
        """The current best detection result."""
        if self._result is not None:
            d = self._result.to_dict()
            if self._prefer_superset:
                apply_preferred_superset(d)
            if self._compat_names:
                apply_compat_names(d)
            return d
        return _NONE_RESULT.to_dict()
