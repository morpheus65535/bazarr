"""Early detection of escape-sequence-based encodings (ISO-2022, HZ-GB-2312, UTF-7).

These encodings use ESC (0x1B), tilde (~), or plus (+) sequences to switch
character sets.  They must be detected before binary detection (ESC is a control
byte) and before ASCII detection (HZ-GB-2312 and UTF-7 use only printable ASCII
bytes plus their respective shift markers).

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet._utils import EVIDENCE_CAP_BYTES, count_deleted, decodes_without_error
from chardet.pipeline import DETERMINISTIC_CONFIDENCE, DetectionResult

# Byte values legal inside an HZ-GB-2312 ``~{...~}`` region.
_HZ_GB_BYTES: bytes = bytes(range(0x21, 0x7F))


def _has_valid_hz_regions(data: bytes, max_start: int, max_end: int) -> bool:
    """Check that at least one ~{...~} region contains valid GB2312 byte pairs.

    In HZ-GB-2312 GB mode, characters are encoded as pairs of bytes in the
    0x21-0x7E range.  We require at least one region with a non-empty, even-
    length run of such bytes.

    *max_start* bounds where a region may open and *max_end* where it may
    close.  Keeping them separate is what lets a region that opens inside
    the evidence window close beyond it: bounding both at the same offset
    would cut a straddling region and hide the only escape evidence a
    document has (ADR-0006).
    """
    start = 0
    while True:
        begin = data.find(b"~{", start)
        if begin == -1 or begin >= max_start:
            return False
        end = data.find(b"~}", begin + 2, max_end)
        if end == -1:
            return False
        region = data[begin + 2 : end]
        # Must be non-empty, even length, and all bytes in GB2312 range.
        # The range test is a C-level scan rather than a Python loop: a
        # region may now run past the evidence window, and per-byte Python
        # work proportional to it is exactly what the window exists to
        # prevent.
        if (
            len(region) >= 2
            and len(region) % 2 == 0
            and count_deleted(region, _HZ_GB_BYTES) == len(region)
        ):
            return True
        start = end + 2


# Base64 alphabet used inside UTF-7 shifted sequences (+<Base64>-)
_B64_CHARS: bytes = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_UTF7_BASE64: frozenset[int] = frozenset(_B64_CHARS)

# Uppercase ASCII letters (A-Z), used by Guard C in _has_valid_utf7_sequences.
_B64_UPPERCASE: frozenset[int] = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Lookup table mapping each Base64 byte to its 6-bit value (0-63).
_B64_DECODE: dict[int, int] = {c: i for i, c in enumerate(_B64_CHARS)}

# Consecutive base64 characters before a '+' that mark it as part of a
# base64 stream rather than a UTF-7 shift.
_EMBEDDED_B64_RUN: int = 4


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

    The walk stops at the fourth character rather than running to the start
    of the run.  Only the ``>= 4`` verdict is used, and newlines are
    skipped rather than ending the walk, so without the early exit a
    line-wrapped base64 blob — a PEM file, a MIME attachment, exactly what
    this guard exists to recognize — makes each ``+`` rescan everything
    before it, and the caller quadratic in the size of the blob.
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
            if count >= _EMBEDDED_B64_RUN:
                return True
            i -= 1
        else:
            break
    return False


def _single_unit(b64_data: bytes) -> int:
    """Decode the first (only) UTF-16 code unit of a single-unit block."""
    return (
        (_B64_DECODE[b64_data[0]] << 12)
        | (_B64_DECODE[b64_data[1]] << 6)
        | _B64_DECODE[b64_data[2]]
    ) >> 2


def _plausible_lone_unit(unit: int) -> bool:
    """Script ranges where a lone shifted character plausibly occurs."""
    return (
        0x0080 <= unit <= 0x07FF  # Latin supp. .. Arabic
        or 0x0E00 <= unit <= 0x0FFF  # Thai, Lao, Tibetan
        or 0x2000 <= unit <= 0x2BFF  # punctuation .. arrows (em dash, euro)
        or 0x3000 <= unit <= 0x30FF  # CJK punctuation, kana
        or 0x4E00 <= unit <= 0x9FFF  # CJK unified
        or 0xAC00 <= unit <= 0xD7A3  # Hangul
        or 0xFF00 <= unit <= 0xFFEF  # fullwidth forms
    )


def _has_valid_utf7_sequences(data: bytes, max_start: int, max_end: int) -> bool:
    """Check that *data* contains at least one valid UTF-7 shifted sequence.

    A valid shifted sequence is ``+<base64 chars>`` terminated by either an
    explicit ``-`` or any non-Base64 character (per RFC 2152).  The base64
    portion must decode to valid UTF-16BE with correct zero-padding bits.
    The sequence ``+-`` is a literal plus sign and is **not** counted.

    *max_start* bounds where a shift may occur and *max_end* how far its
    base64 run may reach, so a run that begins inside the evidence window
    can finish beyond it (ADR-0006).  A run that outruns *max_end* is
    skipped rather than judged on the part that fits: the padding and
    surrogate checks read a cut run as a different run, and accepting on
    evidence we did not see is the one direction this must never fail in.
    """
    start = 0
    limit = min(len(data), max_end)
    while True:
        shift_pos = data.find(ord("+"), start)
        if shift_pos == -1 or shift_pos >= max_start:
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
        while i < limit and data[i] in _UTF7_BASE64:
            i += 1
        if i == limit and limit < len(data) and data[i] in _UTF7_BASE64:
            # The run outruns the bound — skip it (see the docstring).
            start = i
            continue
        b64_len = i - pos
        b64_data = data[pos:i]
        # Guard C: reject base64 blocks with no uppercase letters.
        # UTF-7 encodes UTF-16BE code points, and the high byte for virtually
        # every script (Latin Extended, Cyrillic, Arabic, CJK, …) produces
        # uppercase base64 characters.  Sequences without any uppercase like
        # "row", "foo", "pos" (variable names / English words) or "100", "99"
        # (digit runs) are almost always ASCII text that accidentally follows a
        # '+'.  Out of 71,510 real UTF-7 base64 blocks in the test corpus, only
        # 4 lack uppercase letters (0.006%).
        #
        # NOTE: this must test for the *absence of uppercase letters*, not
        # ``bytes.islower()``.  ``b"100".islower()`` is ``False`` (there are no
        # cased characters at all), so an all-digit run like ``+100`` would slip
        # through an ``islower()`` guard and be misdetected as UTF-7 (issue #371).
        if b64_len >= 3 and not any(b in _B64_UPPERCASE for b in b64_data):
            start = i
            continue
        # Accept if base64 content is valid UTF-16BE (padding bits check
        # prevents false positives).  Terminator can be '-', any non-Base64
        # byte, or end of data — all per RFC 2152.
        if b64_len >= 3 and _is_valid_utf7_b64(b64_data):
            # Guard D: a block encoding a *single* code unit — with or
            # without a dash terminator — must decode into a script range
            # where a lone shifted character plausibly occurs.  The corpus's
            # single-unit blocks live in Latin/Greek/Cyrillic/Hebrew/Arabic
            # supplements, Thai, general punctuation through arrows (em
            # dashes and ellipses dominate), CJK, kana, Hangul, and
            # fullwidth forms.  An accidental uppercase run like "+LAY"
            # (issue #371) decodes to U+2C06, Glagolitic — no genuine lone
            # block in 149 corpus files lands in such a range.  Multi-unit
            # blocks are untouched: accidental ASCII does not survive the
            # padding and surrogate checks for long runs.
            if (b64_len * 6) // 16 == 1:
                unit = _single_unit(b64_data)
                if not _plausible_lone_unit(unit):
                    start = i
                    continue
            return True
        start = max(pos, i)


def _iso2022_variant(data: bytes) -> tuple[str, str] | None:
    """Name the ISO-2022 variant whose designations appear in *data*.

    :returns: ``(encoding, language)`` or ``None`` when no designation is
        present.
    """
    # ISO-2022-JP-2004: JIS X 0213 designations are unique to this variant.
    # Python's codec reads the 2004 plane-1 (Q) and plane-2 (P) designations
    # but not the 2000 plane-1 one (O), so an O stream fails the decode gate
    # below and the other stages answer; naming it here would hand the
    # caller an encoding that raises.
    if b"\x1b$(O" in data or b"\x1b$(P" in data or b"\x1b$(Q" in data:
        return "iso2022_jp_2004", "ja"

    # ISO-2022-JP-EXT: JIS X 0201 Kana designation is unique to this variant.
    if b"\x1b(I" in data:
        return "iso2022_jp_ext", "ja"

    # ISO-2022-JP base: JIS X 0208/0201/0212 designations.
    if (
        b"\x1b$B" in data
        or b"\x1b$@" in data
        or b"\x1b(J" in data
        or b"\x1b$(D" in data  # JIS X 0212-1990 (JP-1/JP-2/JP-EXT)
    ):
        # SI/SO (0x0E / 0x0F) shift controls -> JP-EXT
        if b"\x0e" in data and b"\x0f" in data:
            return "iso2022_jp_ext", "ja"
        # Default to JP-2: a strict superset of JP and JP-1 that
        # decodes all base sequences correctly.
        return "iso2022_jp_2", "ja"

    # ISO-2022-KR: ESC sequence for KS C 5601
    if b"\x1b$)C" in data:
        return "iso2022_kr", "ko"

    return None


def detect_escape_encoding(data: bytes) -> DetectionResult | None:
    """Detect ISO-2022, HZ-GB-2312, and UTF-7 from escape/tilde/plus sequences.

    Every answer this stage returns decodes the whole window: a designation
    is three bytes that ordinary text can contain (``log: ESC $ B is the
    escape``), and a genuine ISO-2022 or HZ stream can still carry a bad
    byte past the header.  The gate costs one decode per hit only.

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` if an escape encoding is found, or ``None``.
    """
    has_esc = b"\x1b" in data
    has_tilde = b"~" in data
    has_plus = b"+" in data

    if not has_esc and not has_tilde and not has_plus:
        return None

    if has_esc:
        variant = _iso2022_variant(data)
        if variant is not None and decodes_without_error(data, variant[0]):
            return DetectionResult(
                encoding=variant[0],
                confidence=DETERMINISTIC_CONFIDENCE,
                language=variant[1],
            )

    # Bounds for the deep validators below.  They walk candidate sites in
    # Python loops whose pathological case is *rejection* — a large tilde-
    # or plus-heavy file that is neither HZ nor UTF-7 — so where a sequence
    # may *begin* converges on the evidence cap (ADR-0006).  Where it may
    # *end* is a separate bound, one further window on, so a sequence that
    # opens just inside the evidence window is judged whole rather than cut
    # by the boundary and read as malformed.  Nothing plausible sits
    # between the two: a single escape run a quarter of a megabyte long is
    # not text.  Gates that decide whether an answer is *true* stay
    # exhaustive over the window.
    max_start = min(len(data), EVIDENCE_CAP_BYTES)
    max_end = min(len(data), 2 * EVIDENCE_CAP_BYTES)

    # HZ-GB-2312: tilde escapes for GB2312
    # Require valid GB2312 byte pairs (0x21-0x7E range) between ~{ and ~}
    # markers.
    if (
        has_tilde
        and b"~{" in data
        and b"~}" in data
        and _has_valid_hz_regions(data, max_start, max_end)
        and decodes_without_error(data, "hz")
    ):
        return DetectionResult(
            encoding="hz",
            confidence=DETERMINISTIC_CONFIDENCE,
            language="zh",
        )

    # UTF-7: plus-sign shifts into Base64-encoded Unicode.
    # UTF-7 is a 7-bit encoding (RFC 2152): every byte must be in 0x00-0x7F,
    # checked over the whole window (isascii is exactly that predicate, at C
    # scan speed).  The buffer must also *decode* as UTF-7: tabular ASCII
    # like "|16847+|" contains "+|", which is illegal (a shift must be
    # followed by base64 or "-"), so the decode gate kills the
    # delimited-data false-positive class outright while genuine UTF-7 —
    # which real encoders emit as valid streams — always passes.  The
    # decoder fails fast on the first bad sequence.
    #
    # The decode gate keeps the *whole* window: it is what makes a utf-7
    # answer true, and this stage returns it at deterministic confidence.
    # Capping it would let an illegal shift past the cap pass as utf-7 that
    # the caller's own ``decode`` then rejects.
    #
    # It runs *after* the bounded sequence validator, which is the reverse
    # of the obvious order.  A decode gate normally fails fast, but plain
    # ASCII is valid UTF-7, so on the common case — a large ASCII file
    # containing a '+' anywhere — it succeeds over every byte instead, at
    # about a second per 272 MiB.  The validator settles the same files
    # from bounded evidence, leaving the full decode for data that already
    # looks like UTF-7.  Both are pure predicates, so the order changes
    # only cost.
    if (
        has_plus
        and data.isascii()
        and _has_valid_utf7_sequences(data, max_start, max_end)
        and decodes_without_error(data, "utf-7")
    ):
        return DetectionResult(
            encoding="utf-7",
            confidence=DETERMINISTIC_CONFIDENCE,
            language=None,
        )

    return None
