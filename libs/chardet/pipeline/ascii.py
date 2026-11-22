"""Stage 1c: Pure ASCII detection (with null-separator tolerance).

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet._utils import count_deleted
from chardet.pipeline import ASCII_TEXT_BYTES, DetectionResult

# Maximum fraction of null bytes to still classify data as ASCII.
# Null-separated CLI output (find -print0, git ls-tree -z) typically has
# 1-3.5% nulls.  5% covers all realistic cases.  The UTF-16 stage runs
# first and its null-separator guard rejects any all-ASCII data with
# fewer nulls than real UTF-16 carries, so nothing accepted here can
# have been claimed as UTF-16.
_MAX_NULL_FRACTION = 0.05


def detect_ascii(data: bytes) -> DetectionResult | None:
    r"""Return an ASCII result if all bytes are printable ASCII plus common whitespace.

    Tolerates sparse null bytes (``\x00``) up to ``_MAX_NULL_FRACTION`` of
    the data, returning confidence 0.99 instead of 1.0 to distinguish from
    pure ASCII.

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` for ASCII, or ``None``.
    """
    if not data:
        return None
    # Non-ASCII data can never pass: the disallowed set includes every high
    # byte.  ``isascii`` answers that in one allocation-free C scan, so
    # large non-ASCII inputs skip the counting pass entirely.
    if not data.isascii():
        return None
    # Count rather than materialize the remainder: on a large all-ASCII
    # window the deletion translate would allocate an input-sized buffer
    # just to hand back an empty result.
    # ASCII_TEXT_BYTES is the *allowed* set, so what the deletion leaves is
    # the disallowed bytes: count them as the complement.
    disallowed = len(data) - count_deleted(data, ASCII_TEXT_BYTES)
    if disallowed == 0:
        return DetectionResult(encoding="ascii", confidence=1.0, language=None)
    null_count = data.count(0)
    # Any disallowed byte that is not a null disqualifies the data.
    if disallowed != null_count:
        return None
    # All non-allowed bytes are nulls — accept if sparse enough
    null_fraction = null_count / len(data)
    if null_fraction <= _MAX_NULL_FRACTION:
        return DetectionResult(encoding="ascii", confidence=0.99, language=None)
    return None
