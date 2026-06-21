"""Stage 1d: UTF-8 structural validation.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.pipeline import DetectionResult

# Confidence curve parameters for UTF-8 detection.
# Even a small fraction of valid multi-byte sequences is strong evidence.
_BASE_CONFIDENCE = 0.80
_MAX_CONFIDENCE = 0.99
# Scale factor for the multi-byte byte ratio: mb_ratio * 6 saturates the
# confidence ramp at ~17% multi-byte content.
_MB_RATIO_SCALE = 6


def detect_utf8(data: bytes) -> DetectionResult | None:
    """Validate UTF-8 byte structure.

    Returns a result only if multi-byte sequences are found (pure ASCII
    is handled by the ASCII stage).

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` for UTF-8, or ``None``.
    """
    if not data:
        return None

    i = 0
    length = len(data)
    multibyte_sequences = 0
    multibyte_bytes = 0

    while i < length:
        byte = data[i]

        if byte < 0x80:
            i += 1
            continue

        # Determine expected sequence length from leading byte.
        # 0xC0-0xC1 are overlong 2-byte encodings of ASCII, so we start at 0xC2.
        if 0xC2 <= byte <= 0xDF:
            seq_len = 2
        elif 0xE0 <= byte <= 0xEF:
            seq_len = 3
        elif 0xF0 <= byte <= 0xF4:
            seq_len = 4
        else:
            # Invalid start byte (0x80-0xC1, 0xF5-0xFF)
            return None

        # Truncated final sequence (e.g. from max_bytes slicing) — treat as
        # valid since the bytes seen so far are structurally correct.
        if i + seq_len > length:
            break

        # Validate continuation bytes (must be 0x80-0xBF)
        for j in range(1, seq_len):
            if not (0x80 <= data[i + j] <= 0xBF):
                return None

        # Reject overlong encodings and surrogates
        if seq_len == 3:
            # 0xE0: second byte must be >= 0xA0 (prevents overlong 3-byte)
            if byte == 0xE0 and data[i + 1] < 0xA0:
                return None
            # 0xED: second byte must be <= 0x9F (prevents UTF-16 surrogates U+D800-U+DFFF)
            if byte == 0xED and data[i + 1] > 0x9F:
                return None
        elif seq_len == 4:
            # 0xF0: second byte must be >= 0x90 (prevents overlong 4-byte)
            if byte == 0xF0 and data[i + 1] < 0x90:
                return None
            # 0xF4: second byte must be <= 0x8F (prevents codepoints above U+10FFFF)
            if byte == 0xF4 and data[i + 1] > 0x8F:
                return None

        multibyte_sequences += 1
        multibyte_bytes += seq_len
        i += seq_len

    # Pure ASCII — let the ASCII detector handle it
    if multibyte_sequences == 0:
        return None

    # Confidence scales with the proportion of multi-byte bytes in the data.
    # Even a small amount of valid multi-byte UTF-8 is strong evidence.
    mb_ratio = multibyte_bytes / length
    confidence_range = _MAX_CONFIDENCE - _BASE_CONFIDENCE
    confidence = min(
        _MAX_CONFIDENCE,
        _BASE_CONFIDENCE + confidence_range * min(mb_ratio * _MB_RATIO_SCALE, 1.0),
    )
    return DetectionResult(encoding="utf-8", confidence=confidence, language=None)
