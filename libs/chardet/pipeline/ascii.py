"""Stage 1c: Pure ASCII detection (with null-separator tolerance).

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.pipeline import ASCII_TEXT_BYTES, DetectionResult

# Maximum fraction of null bytes to still classify data as ASCII.
# Null-separated CLI output (find -print0, git ls-tree -z) typically has
# 1-3.5% nulls.  5% covers all realistic cases while staying well below
# the UTF-16 guard threshold (15%).
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
    remainder = data.translate(None, ASCII_TEXT_BYTES)
    if not remainder:
        return DetectionResult(encoding="ascii", confidence=1.0, language=None)
    # Check if the only non-allowed bytes are null separators
    if remainder.replace(b"\x00", b""):
        return None  # Non-null, non-ASCII bytes present
    # All non-allowed bytes are nulls — accept if sparse enough
    null_fraction = len(remainder) / len(data)
    if null_fraction <= _MAX_NULL_FRACTION:
        return DetectionResult(encoding="ascii", confidence=0.99, language=None)
    return None
