"""Stage 1a+: UTF-16/UTF-32 detection for data without BOM.

This stage runs after BOM detection but before binary detection.
UTF-16 and UTF-32 encoded text contains characteristic null-byte patterns
that would otherwise cause binary detection to reject the data.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import unicodedata

from chardet.pipeline import ASCII_TEXT_BYTES, DETERMINISTIC_CONFIDENCE, DetectionResult

# How many bytes to sample for pattern analysis
_SAMPLE_SIZE = 4096

# Minimum bytes needed for reliable pattern detection
_MIN_BYTES_UTF32 = 16  # 4 full code units
_MIN_BYTES_UTF16 = 10  # 5 full code units

# Minimum fraction of null bytes in the expected position for UTF-16.
# CJK-heavy UTF-16 text (Chinese, Japanese, Korean) can have as few as
# ~4.5% null bytes in the expected position, since CJK codepoints have
# non-zero high bytes.  The validation step (decode + text quality check)
# prevents false positives from binary files at this lower threshold.
_UTF16_MIN_NULL_FRACTION = 0.03

# Minimum text-quality score to accept a UTF-16 candidate when both
# endiannesses show null-byte patterns.  A score of 0.5 corresponds to
# roughly 50% letters with no ASCII bonus (or ~40% with whitespace
# present) — sufficient to distinguish real text from coincidental byte
# patterns.
_MIN_TEXT_QUALITY = 0.5

# Minimum fraction of printable characters for a decoded sample to be
# considered text rather than binary data.
_MIN_PRINTABLE_FRACTION = 0.7

# Maximum null fraction (in the candidate null-byte position) below which
# the data is checked for a null-separator pattern.  If the null fraction
# is below this AND all non-null bytes are printable ASCII, the candidate
# is rejected as a null-separator false positive rather than real UTF-16.
# Real Latin UTF-16 has ~50% nulls; CJK UTF-16 has fewer but non-ASCII
# non-null bytes.  15% is generous — separator data is typically 1-5%.
_NULL_SEPARATOR_MAX_FRACTION = 0.15

# ASCII_TEXT_BYTES plus the null byte — used by the null-separator guard
# to check whether non-null bytes are all printable ASCII.
_NULL_SEPARATOR_ALLOWED: bytes = b"\x00" + ASCII_TEXT_BYTES


def _is_null_separator_pattern(data: bytes, null_frac: float) -> bool:
    """Return True if the data looks like ASCII with null byte separators.

    :param data: The raw byte sample to examine.
    :param null_frac: The positional null fraction for this UTF-16 candidate
        (i.e. fraction of null bytes in even positions for BE, or odd positions
        for LE) — not the total null fraction across all bytes.

    Checks two conditions:
    1. The positional null fraction is below ``_NULL_SEPARATOR_MAX_FRACTION``
    2. Every non-null byte is printable ASCII or common whitespace

    When both conditions are met, the nulls are likely field separators
    (e.g. ``find -print0``), not UTF-16 encoding artifacts.
    """
    if null_frac >= _NULL_SEPARATOR_MAX_FRACTION:
        return False
    return not data.translate(None, _NULL_SEPARATOR_ALLOWED)


def detect_utf1632_patterns(data: bytes) -> DetectionResult | None:
    """Detect UTF-32 or UTF-16 encoding from null-byte patterns.

    UTF-32 is checked before UTF-16 since UTF-32 patterns are more specific.

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` if a strong pattern is found, or ``None``.
    """
    sample = data[:_SAMPLE_SIZE]

    if len(sample) < _MIN_BYTES_UTF16:
        return None

    # Check UTF-32 first (more specific pattern)
    result = _check_utf32(sample)
    if result is not None:
        return result

    # Then check UTF-16
    return _check_utf16(sample)


def _check_utf32(data: bytes) -> DetectionResult | None:
    """Check for UTF-32 encoding based on 4-byte unit structure.

    For valid Unicode (U+0000 to U+10FFFF = 0x0010FFFF):
    - UTF-32-BE: the first byte of each 4-byte unit is always 0x00
    - UTF-32-LE: the last byte of each 4-byte unit is always 0x00

    For BMP characters (U+0000 to U+FFFF), additionally:
    - UTF-32-BE: the second byte is also 0x00
    - UTF-32-LE: the third byte is also 0x00
    """
    # Trim to a multiple of 4 bytes (like _check_utf16 trims to even length)
    trimmed_len = len(data) - (len(data) % 4)
    if trimmed_len < _MIN_BYTES_UTF32:
        return None
    data = data[:trimmed_len]

    num_units = trimmed_len // 4

    # UTF-32-BE: first byte of each 4-byte unit must be 0x00
    be_first_null = sum(1 for i in range(0, len(data), 4) if data[i] == 0)
    # Second byte is 0x00 for BMP characters (the vast majority of text)
    be_second_null = sum(1 for i in range(0, len(data), 4) if data[i + 1] == 0)

    if be_first_null == num_units and be_second_null / num_units > 0.5:
        try:
            text = data.decode("utf-32-be")
            if _looks_like_text(text):
                return DetectionResult(
                    encoding="utf-32-be",
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                )
        except UnicodeDecodeError:
            pass

    # UTF-32-LE: last byte of each 4-byte unit must be 0x00
    le_last_null = sum(1 for i in range(3, len(data), 4) if data[i] == 0)
    # Third byte is 0x00 for BMP characters
    le_third_null = sum(1 for i in range(2, len(data), 4) if data[i] == 0)

    if le_last_null == num_units and le_third_null / num_units > 0.5:
        try:
            text = data.decode("utf-32-le")
            if _looks_like_text(text):
                return DetectionResult(
                    encoding="utf-32-le",
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                )
        except UnicodeDecodeError:
            pass

    return None


def _check_utf16(data: bytes) -> DetectionResult | None:
    """Check for UTF-16 via null-byte patterns in alternating positions.

    UTF-16 encodes each BMP character as two bytes.  For characters whose
    code-point high byte is 0x00 (Latin, digits, basic punctuation, many
    control structures), one of the two bytes in each unit will be a null.
    Even for non-Latin scripts (Arabic, CJK, Cyrillic, etc.) a significant
    fraction of code units still contain at least one null byte.

    Non-UTF-16 single-byte encodings never contain null bytes, so even a
    small null-byte fraction in alternating positions is a strong signal.

    When both endiannesses show null-byte patterns (e.g., Latin text where
    every other byte is null), we disambiguate by decoding both ways and
    comparing text-quality scores.
    """
    sample_len = min(len(data), _SAMPLE_SIZE)
    sample_len -= sample_len % 2
    if sample_len < _MIN_BYTES_UTF16:  # pragma: no cover - caller checks length
        return None

    num_units = sample_len // 2

    # Count null bytes in even positions (UTF-16-BE high byte for ASCII)
    be_null_count = sum(1 for i in range(0, sample_len, 2) if data[i] == 0)
    # Count null bytes in odd positions (UTF-16-LE high byte for ASCII)
    le_null_count = sum(1 for i in range(1, sample_len, 2) if data[i] == 0)

    be_frac = be_null_count / num_units
    le_frac = le_null_count / num_units

    candidates: list[tuple[str, float]] = []
    if le_frac >= _UTF16_MIN_NULL_FRACTION and not _is_null_separator_pattern(
        data[:sample_len], le_frac
    ):
        candidates.append(("utf-16-le", le_frac))
    if be_frac >= _UTF16_MIN_NULL_FRACTION and not _is_null_separator_pattern(
        data[:sample_len], be_frac
    ):
        candidates.append(("utf-16-be", be_frac))

    if not candidates:
        return None

    # If only one candidate, validate and return
    if len(candidates) == 1:
        encoding = candidates[0][0]
        try:
            text = data[:sample_len].decode(encoding)
            if _looks_like_text(text):
                return DetectionResult(
                    encoding=encoding,
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                )
        except UnicodeDecodeError:
            pass
        return None

    # Both candidates matched (common for Latin-heavy text where every other
    # byte is null).  Decode both and pick the one with higher text quality.
    best_encoding: str | None = None
    best_quality = -1.0

    for encoding, _ in candidates:
        try:
            text = data[:sample_len].decode(encoding)
        except UnicodeDecodeError:
            continue
        quality = _text_quality(text)
        if quality > best_quality:
            best_quality = quality
            best_encoding = encoding

    if best_encoding is not None and best_quality >= _MIN_TEXT_QUALITY:
        return DetectionResult(
            encoding=best_encoding,
            confidence=DETERMINISTIC_CONFIDENCE,
            language=None,
        )

    return None


def _looks_like_text(text: str) -> bool:
    """Quick check: is decoded text mostly printable characters."""
    if not text:
        return False
    sample = text[:500]
    printable = sum(1 for c in sample if c.isprintable() or c in "\n\r\t")
    return printable / len(sample) > _MIN_PRINTABLE_FRACTION


def _text_quality(text: str, limit: int = 500) -> float:
    """Score how much *text* looks like real human-readable content.

    Returns a score in the range [-1.0, ~1.6).  Higher values indicate
    more natural text.  The practical maximum is 1.5 for all-ASCII-letter
    input (1.6 approaches as sample size grows with all ASCII letters plus
    whitespace).  A score of -1.0 means the content is almost certainly not
    valid text (too many control characters or combining marks).

    Scoring factors:

    * Base score: ratio of Unicode letters (category ``L*``) to sample length.
    * ASCII bonus: additional 0.5x weight for ASCII letters.  This is the
      primary signal for disambiguating endianness — correct decoding of
      Latin-heavy text produces ASCII letters, wrong decoding produces CJK.
    * Space bonus: +0.1 when the sample contains at least one whitespace
      character and is longer than 20 characters.
    * Rejection: returns -1.0 if >10% control characters or >20% combining
      marks (category ``M*``).
    """
    sample = text[:limit]
    n = len(sample)
    if n == 0:  # pragma: no cover - callers always pass non-empty text
        return -1.0

    letters = 0
    marks = 0
    spaces = 0
    controls = 0
    ascii_letters = 0

    for c in sample:
        cat = unicodedata.category(c)
        if cat[0] == "L":
            letters += 1
            if ord(c) < 128:
                ascii_letters += 1
        elif cat[0] == "M":
            marks += 1
        elif cat == "Zs" or c in "\n\r\t":
            spaces += 1
        elif cat[0] == "C":
            controls += 1

    # Reject data with many control characters or combining marks
    if controls / n > 0.1:
        return -1.0
    if marks / n > 0.2:
        return -1.0

    score = letters / n
    # ASCII letters strongly indicate correct endianness
    score += (ascii_letters / n) * 0.5
    # Real text usually contains some whitespace
    if n > 20 and spaces > 0:
        score += 0.1

    return score
