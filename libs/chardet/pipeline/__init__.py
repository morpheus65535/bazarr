"""Detection pipeline stages and shared types."""

from __future__ import annotations

import dataclasses
from dataclasses import field
from typing import TypedDict

#: Confidence for deterministic (non-BOM) detection stages.
#: Used by escape, markup, and utf1632 stages (and by the orchestrator for
#: the binary-detection result).
DETERMINISTIC_CONFIDENCE: float = 0.95

#: Byte table for fast non-ASCII counting (C-speed via bytes.translate).
#: Deleting all bytes >= 0x80 and comparing lengths gives the non-ASCII count.
HIGH_BYTES: bytes = bytes(range(0x80, 0x100))

#: Bytes considered valid in ASCII text: tab (0x09), newline (0x0A),
#: carriage return (0x0D), and printable ASCII (0x20-0x7E).
#: Used by ``ascii.py`` directly and by ``utf1632.py`` (with null added).
ASCII_TEXT_BYTES: bytes = bytes([0x09, 0x0A, 0x0D, *range(0x20, 0x7F)])


class DetectionDict(TypedDict):
    """Dictionary representation of a detection result.

    Returned by :func:`chardet.detect`, :func:`chardet.detect_all`,
    and :attr:`chardet.UniversalDetector.result`.
    """

    encoding: str | None
    confidence: float
    language: str | None
    mime_type: str | None


@dataclasses.dataclass(frozen=True, slots=True)
class DetectionResult:
    """A single encoding detection result.

    Frozen dataclass holding the encoding name, confidence score, and
    optional language identifier returned by the detection pipeline.
    """

    encoding: str | None
    confidence: float
    language: str | None
    mime_type: str | None = None

    def to_dict(self) -> DetectionDict:
        """Convert this result to a plain dict.

        :returns: A dict with ``'encoding'``, ``'confidence'``, ``'language'``, and ``'mime_type'`` keys.
        """
        return {
            "encoding": self.encoding,
            "confidence": self.confidence,
            "language": self.language,
            "mime_type": self.mime_type,
        }


#: Sentinel result for "no detection" — used by the orchestrator for
#: filtered-out fallbacks and by UniversalDetector before close().
_NONE_RESULT = DetectionResult(encoding=None, confidence=0.0, language=None)


@dataclasses.dataclass(slots=True)
class PipelineContext:
    """Per-run mutable state for a single pipeline invocation.

    Created once at the start of ``run_pipeline()`` and threaded through
    the call chain via function parameters.  Each concurrent ``detect()``
    call gets its own context, eliminating the need for module-level
    mutable caches.
    """

    analysis_cache: dict[str, tuple[float, int, int]] = field(default_factory=dict)
    non_ascii_count: int | None = None
    mb_scores: dict[str, float] = field(default_factory=dict)
    mb_coverage: dict[str, float] = field(default_factory=dict)
