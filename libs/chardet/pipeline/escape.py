"""Early detection of escape-sequence-based encodings (ISO-2022, HZ-GB-2312, UTF-7).

These encodings use ESC (0x1B), tilde (~), or plus (+) sequences to switch
character sets.  They must be detected before binary detection (ESC is a control
byte) and before ASCII detection (HZ-GB-2312 and UTF-7 use only printable ASCII
bytes plus their respective shift markers).

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.pipeline import DETERMINISTIC_CONFIDENCE, DetectionResult


def _has_valid_hz_regions(data: bytes) -> bool:
    """Check that at least one ~{...~} region contains valid GB2312 byte pairs.

    In HZ-GB-2312 GB mode, characters are encoded as pairs of bytes in the
    0x21-0x7E range.  We require at least one region with a non-empty, even-
    length run of such bytes.
    """
    start = 0
    while True:
        begin = data.find(b"~{", start)
        if begin == -1:
            return False
        end = data.find(b"~}", begin + 2)
        if end == -1:
            return False
        region = data[begin + 2 : end]
        # Must be non-empty, even length, and all bytes in GB2312 range
        if (
            len(region) >= 2
            and len(region) % 2 == 0
            and all(0x21 <= b <= 0x7E for b in region)
        ):
            return True
        start = end + 2


# Base64 alphabet used inside UTF-7 shifted sequences (+<Base64>-)
_B64_CHARS: bytes = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_UTF7_BASE64: frozenset[int] = frozenset(_B64_CHARS)

# Lookup table mapping each Base64 byte to its 6-bit value (0-63).
_B64_DECODE: dict[int, int] = {c: i for i, c in enumerate(_B64_CHARS)}


def _is_valid_utf7_b64(b64_bytes: bytes) -> bool:
    """Check if base64 bytes decode to valid UTF-16BE with correct padding.

    A valid UTF-7 shifted sequence must:
    1. Contain at least 3 Base64 characters (18 bits, enough for one 16-bit
       UTF-16 code unit).
    2. Have zero-valued trailing padding bits (the unused low bits of the last
       Base64 sextet after the last complete 16-bit code unit).
    3. Decode to valid UTF-16BE — no lone surrogates.

    This rejects accidental ``+<alphanum>-`` patterns found in URLs, MIME
    boundaries, hex-encoded hashes (e.g. SHA-1 git refs), and other ASCII data.

    The caller (``_has_valid_utf7_sequences``) already checks ``b64_len >= 3``
    before calling this function, so *b64_bytes* is always at least 3 bytes.
    """
    n = len(b64_bytes)
    total_bits = n * 6
    # Check that padding bits (trailing bits after last complete code unit)
    # are zero.
    padding_bits = total_bits % 16
    if padding_bits > 0:
        last_val = _B64_DECODE[b64_bytes[-1]]
        # The low `padding_bits` of the last sextet must be zero
        mask = (1 << padding_bits) - 1
        if last_val & mask:
            return False
    # Decode the base64 to raw bytes and validate as UTF-16BE.
    # Lone surrogates (unpaired 0xD800-0xDFFF code units) are illegal in
    # well-formed UTF-16 and cannot appear in real UTF-7 text.  This catches
    # hex-encoded hashes and other accidental base64-like sequences.
    num_bytes = total_bits // 8
    raw = bytearray(num_bytes)
    bit_buf = 0
    bit_count = 0
    out_idx = 0
    for c in b64_bytes:
        bit_buf = (bit_buf << 6) | _B64_DECODE[c]
        bit_count += 6
        if bit_count >= 8:
            bit_count -= 8
            raw[out_idx] = (bit_buf >> bit_count) & 0xFF
            out_idx += 1
    prev_high = False
    for i in range(0, num_bytes - 1, 2):
        code_unit = (raw[i] << 8) | raw[i + 1]
        if 0xD800 <= code_unit <= 0xDBFF:  # high surrogate
            if prev_high:
                return False  # consecutive high surrogates
            prev_high = True
        elif 0xDC00 <= code_unit <= 0xDFFF:  # low surrogate
            if not prev_high:
                return False  # lone low surrogate
            prev_high = False
        else:
            if prev_high:
                return False  # high surrogate not followed by low surrogate
            prev_high = False
    return not prev_high


def _is_embedded_in_base64(data: bytes, pos: int) -> bool:
    """Return True if the ``+`` at *pos* is embedded in a base64 stream.

    Walks backward from *pos*, skipping CR/LF, and counts consecutive base64
    characters (including ``=`` for padding).  If 4 or more are found, the
    ``+`` is likely part of a PEM certificate, email attachment, or similar
    base64 blob rather than a real UTF-7 shift character.
    """
    b64_with_pad: frozenset[int] = _UTF7_BASE64 | frozenset(b"=")
    count = 0
    i = pos - 1
    while i >= 0:
        b = data[i]
        if b in {0x0A, 0x0D}:  # skip newlines
            i -= 1
            continue
        if b in b64_with_pad:
            count += 1
            i -= 1
        else:
            break
    return count >= 4


def _has_valid_utf7_sequences(data: bytes) -> bool:
    """Check that *data* contains at least one valid UTF-7 shifted sequence.

    A valid shifted sequence is ``+<base64 chars>`` terminated by either an
    explicit ``-`` or any non-Base64 character (per RFC 2152).  The base64
    portion must decode to valid UTF-16BE with correct zero-padding bits.
    The sequence ``+-`` is a literal plus sign and is **not** counted.
    """
    start = 0
    while True:
        shift_pos = data.find(ord("+"), start)
        if shift_pos == -1:
            return False
        pos = shift_pos + 1  # skip the '+'
        # +- is a literal plus, not a shifted sequence
        if pos < len(data) and data[pos] == ord("-"):
            start = pos + 1
            continue
        # Guard A: '+' as the first base64 character encodes PUA code points
        # (U+F800-U+FBFC) which never appear in real text.  This catches
        # patterns like "C++20" and "++row".  Skip past ALL consecutive '+'
        # characters so the next '+' in a run like ``++`` or ``+++`` is not
        # re-examined as a new shift character.
        if pos < len(data) and data[pos] == ord("+"):
            while pos < len(data) and data[pos] == ord("+"):
                pos += 1
            start = pos
            continue
        # Guard B: if the '+' is embedded in a base64 stream (PEM, email
        # attachment, etc.), it's not a real UTF-7 shift character.
        if _is_embedded_in_base64(data, shift_pos):
            start = pos
            continue
        # Collect consecutive Base64 characters
        i = pos
        while i < len(data) and data[i] in _UTF7_BASE64:
            i += 1
        b64_len = i - pos
        b64_data = data[pos:i]
        # Guard C: reject base64 blocks with no uppercase letters.
        # UTF-7 encodes UTF-16BE code points, and the high byte for virtually
        # every script (Latin Extended, Cyrillic, Arabic, CJK, …) produces
        # uppercase base64 characters.  Sequences without any uppercase like
        # "row", "foo", "pos" are almost always variable names or English
        # words that accidentally follow a '+'.  (bytes.islower() returns
        # True when there are no uppercase letters, even if digits or '/'
        # are present, which is the desired behavior here.)  Out of 71,510
        # real UTF-7 base64 blocks in the test corpus, only 4 lack uppercase
        # letters (0.006%).
        if b64_len >= 3 and b64_data.islower():
            start = i
            continue
        # Accept if base64 content is valid UTF-16BE (padding bits check
        # prevents false positives).  Terminator can be '-', any non-Base64
        # byte, or end of data — all per RFC 2152.
        if b64_len >= 3 and _is_valid_utf7_b64(b64_data):
            return True
        start = max(pos, i)


def detect_escape_encoding(data: bytes) -> DetectionResult | None:
    """Detect ISO-2022, HZ-GB-2312, and UTF-7 from escape/tilde/plus sequences.

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` if an escape encoding is found, or ``None``.
    """
    has_esc = b"\x1b" in data
    has_tilde = b"~" in data
    has_plus = b"+" in data

    if not has_esc and not has_tilde and not has_plus:
        return None

    if has_esc:
        # ISO-2022-JP-2004: JIS X 0213 designations are unique to this variant.
        if b"\x1b$(O" in data or b"\x1b$(P" in data or b"\x1b$(Q" in data:
            return DetectionResult(
                encoding="iso2022_jp_2004",
                confidence=DETERMINISTIC_CONFIDENCE,
                language="ja",
            )

        # ISO-2022-JP-EXT: JIS X 0201 Kana designation is unique to this variant.
        if b"\x1b(I" in data:
            return DetectionResult(
                encoding="iso2022_jp_ext",
                confidence=DETERMINISTIC_CONFIDENCE,
                language="ja",
            )

        # ISO-2022-JP base: JIS X 0208/0201/0212 designations.
        if (
            b"\x1b$B" in data
            or b"\x1b$@" in data
            or b"\x1b(J" in data
            or b"\x1b$(D" in data  # JIS X 0212-1990 (JP-1/JP-2/JP-EXT)
        ):
            # SI/SO (0x0E / 0x0F) shift controls -> JP-EXT
            if b"\x0e" in data and b"\x0f" in data:
                return DetectionResult(
                    encoding="iso2022_jp_ext",
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language="ja",
                )
            # Default to JP-2: a strict superset of JP and JP-1 that
            # decodes all base sequences correctly.
            return DetectionResult(
                encoding="iso2022_jp_2",
                confidence=DETERMINISTIC_CONFIDENCE,
                language="ja",
            )

        # ISO-2022-KR: ESC sequence for KS C 5601
        if b"\x1b$)C" in data:
            return DetectionResult(
                encoding="iso2022_kr",
                confidence=DETERMINISTIC_CONFIDENCE,
                language="ko",
            )

    # HZ-GB-2312: tilde escapes for GB2312
    # Require valid GB2312 byte pairs (0x21-0x7E range) between ~{ and ~} markers.
    if has_tilde and b"~{" in data and b"~}" in data and _has_valid_hz_regions(data):
        return DetectionResult(
            encoding="hz",
            confidence=DETERMINISTIC_CONFIDENCE,
            language="zh",
        )

    # UTF-7: plus-sign shifts into Base64-encoded Unicode.
    # UTF-7 is a 7-bit encoding (RFC 2152): every byte must be in 0x00-0x7F.
    # Data with any byte > 0x7F cannot be UTF-7.
    if has_plus and max(data) < 0x80 and _has_valid_utf7_sequences(data):
        return DetectionResult(
            encoding="utf-7",
            confidence=DETERMINISTIC_CONFIDENCE,
            language=None,
        )

    return None
