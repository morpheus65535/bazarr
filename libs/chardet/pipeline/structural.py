"""Stage 2b: Multi-byte structural probing.

Computes how well byte patterns in the data match the expected multi-byte
structure for a given encoding.  Used after byte-validity filtering (Stage 2a)
to further rank multi-byte encoding candidates.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from collections.abc import Callable

from chardet.pipeline import HIGH_BYTES, PipelineContext
from chardet.registry import EncodingInfo

# ---------------------------------------------------------------------------
# Per-encoding single-pass analyzers
#
# Each function walks the data once, computing three metrics simultaneously:
#   - pair_ratio: valid multi-byte pairs / lead bytes  (structural score)
#   - mb_bytes:   count of non-ASCII bytes in valid multi-byte sequences
#   - lead_diversity: count of distinct lead byte values in valid pairs
#
# These are kept as separate functions (rather than a single parameterized
# analyzer) so that mypyc can inline the byte-range constants into each
# function's tight loop.
# ---------------------------------------------------------------------------


def _analyze_shift_jis(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass Shift_JIS structural analysis.

    Lead bytes: 0x81-0x9F, 0xE0-0xEF
    Trail bytes: 0x40-0x7E, 0x80-0xFC

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF):
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (0x40 <= trail <= 0x7E) or (0x80 <= trail <= 0xFC):
                    valid_count += 1
                    leads.add(b)
                    # Lead is always > 0x7F; trail may or may not be
                    mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_cp932(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass CP932 structural analysis.

    Lead bytes: 0x81-0x9F, 0xE0-0xFC
    Trail bytes: 0x40-0x7E, 0x80-0xFC

    Extends Shift_JIS by raising the lead byte ceiling from 0xEF to 0xFC,
    covering IBM vendor-defined characters (NEC-selected, IBM extensions).

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC):
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (0x40 <= trail <= 0x7E) or (0x80 <= trail <= 0xFC):
                    valid_count += 1
                    leads.add(b)
                    # Lead is always > 0x7F; trail may or may not be
                    mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_euc_jp(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass EUC-JP structural analysis.

    Two-byte: Lead 0xA1-0xFE, Trail 0xA1-0xFE
    SS2 (half-width katakana): 0x8E + 0xA1-0xDF
    SS3 (JIS X 0212): 0x8F + 0xA1-0xFE + 0xA1-0xFE

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if b == 0x8E:
            # SS2 sequence
            lead_count += 1
            if i + 1 < length and 0xA1 <= data[i + 1] <= 0xDF:
                valid_count += 1
                leads.add(b)
                mb += 2
                i += 2
                continue
            i += 1
        elif b == 0x8F:
            # SS3 sequence
            lead_count += 1
            if (
                i + 2 < length
                and 0xA1 <= data[i + 1] <= 0xFE
                and 0xA1 <= data[i + 2] <= 0xFE
            ):
                valid_count += 1
                leads.add(b)
                mb += 3
                i += 3
                continue
            i += 1
        elif 0xA1 <= b <= 0xFE:
            lead_count += 1
            if i + 1 < length and 0xA1 <= data[i + 1] <= 0xFE:
                valid_count += 1
                leads.add(b)
                mb += 2
                i += 2
                continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_euc_kr(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass EUC-KR structural analysis.

    Lead 0xA1-0xFE; Trail 0xA1-0xFE

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if 0xA1 <= b <= 0xFE:
            lead_count += 1
            if i + 1 < length and 0xA1 <= data[i + 1] <= 0xFE:
                valid_count += 1
                leads.add(b)
                mb += 2
                i += 2
                continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_cp949(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass CP949 (Unified Hangul Code) structural analysis.

    Lead bytes: 0x81-0xC8, 0xCA-0xFD
    Trail bytes: 0x41-0x5A, 0x61-0x7A, 0x81-0xFE

    Extends EUC-KR by lowering the lead byte floor from 0xA1 to 0x81 and
    adding ASCII letter trail ranges plus 0x81-0xA0.  0xC9 is not a valid
    UHC lead byte.

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if (0x81 <= b <= 0xC8) or (0xCA <= b <= 0xFD):
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (
                    (0x41 <= trail <= 0x5A)
                    or (0x61 <= trail <= 0x7A)
                    or (0x81 <= trail <= 0xFE)
                ):
                    valid_count += 1
                    leads.add(b)
                    # Lead is always > 0x7F; trail may or may not be
                    mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_gb18030(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass GB18030 / GB2312 structural analysis.

    Only counts strict GB2312 2-byte pairs (lead 0xA1-0xF7, trail 0xA1-0xFE)
    and GB18030 4-byte sequences.  The broader GBK extension range
    (lead 0x81-0xFE, trail 0x40-0x7E / 0x80-0xFE) is intentionally excluded
    because it is so permissive that unrelated single-byte data (EBCDIC, DOS
    codepages, etc.) can score 1.0, leading to false positives.

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if 0x81 <= b <= 0xFE:
            lead_count += 1
            # Try 4-byte first (byte2 in 0x30-0x39 distinguishes from 2-byte)
            if (
                i + 3 < length
                and 0x30 <= data[i + 1] <= 0x39
                and 0x81 <= data[i + 2] <= 0xFE
                and 0x30 <= data[i + 3] <= 0x39
            ):
                valid_count += 1
                leads.add(b)
                mb += 2  # bytes 0 and 2 are non-ASCII
                i += 4
                continue
            # 2-byte GB2312: Lead 0xA1-0xF7, Trail 0xA1-0xFE
            if 0xA1 <= b <= 0xF7 and i + 1 < length and 0xA1 <= data[i + 1] <= 0xFE:
                valid_count += 1
                leads.add(b)
                mb += 2  # both bytes are > 0x7F
                i += 2
                continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_big5(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass Big5 structural analysis.

    Lead 0xA1-0xF9; Trail 0x40-0x7E, 0xA1-0xFE

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if 0xA1 <= b <= 0xF9:
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (0x40 <= trail <= 0x7E) or (0xA1 <= trail <= 0xFE):
                    valid_count += 1
                    leads.add(b)
                    # Lead is always > 0x7F; trail may or may not be
                    mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_big5hkscs(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass Big5-HKSCS structural analysis.

    Lead bytes: 0x87-0xFE
    Trail bytes: 0x40-0x7E, 0xA1-0xFE

    Extends Big5 by lowering the lead byte floor from 0xA1 to 0x87 and
    raising the ceiling from 0xF9 to 0xFE.  0x7F and 0x80-0xA0 are not
    valid Big5/HKSCS trail bytes.

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if 0x87 <= b <= 0xFE:
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (0x40 <= trail <= 0x7E) or (0xA1 <= trail <= 0xFE):
                    valid_count += 1
                    leads.add(b)
                    # Lead is always > 0x7F; trail may or may not be
                    mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


def _analyze_johab(
    data: bytes,
) -> tuple[float, int, int]:
    """Single-pass Johab structural analysis.

    Lead: 0x84-0xD3, 0xD8-0xDE, 0xE0-0xF9
    Trail: 0x31-0x7E, 0x91-0xFE

    Returns (pair_ratio, mb_bytes, lead_diversity).
    """
    lead_count = 0
    valid_count = 0
    mb = 0
    leads: set[int] = set()
    i = 0
    length = len(data)
    while i < length:
        b = data[i]
        if (0x84 <= b <= 0xD3) or (0xD8 <= b <= 0xDE) or (0xE0 <= b <= 0xF9):
            lead_count += 1
            if i + 1 < length:
                trail = data[i + 1]
                if (0x31 <= trail <= 0x7E) or (0x91 <= trail <= 0xFE):
                    valid_count += 1
                    leads.add(b)
                    if b > 0x7F:
                        mb += 1
                    if trail > 0x7F:
                        mb += 1
                    i += 2
                    continue
            i += 1
        else:
            i += 1
    ratio = valid_count / lead_count if lead_count > 0 else 0.0
    return ratio, mb, len(leads)


# ---------------------------------------------------------------------------
# Dispatch table: encoding name -> analyzer function
# ---------------------------------------------------------------------------

_ANALYZERS: dict[str, Callable[[bytes], tuple[float, int, int]]] = {
    "shift_jis_2004": _analyze_shift_jis,
    "cp932": _analyze_cp932,
    "euc_jis_2004": _analyze_euc_jp,
    "euc_kr": _analyze_euc_kr,
    "cp949": _analyze_cp949,
    "gb18030": _analyze_gb18030,
    "big5hkscs": _analyze_big5hkscs,
    "johab": _analyze_johab,
}


def _get_analysis(
    data: bytes, name: str, ctx: PipelineContext
) -> tuple[float, int, int] | None:
    """Return cached analysis or compute and cache it."""
    cached = ctx.analysis_cache.get(name)
    if cached is not None:
        return cached
    analyzer = _ANALYZERS.get(name)
    if analyzer is None:
        return None
    result = analyzer(data)
    ctx.analysis_cache[name] = result
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_structural_score(
    data: bytes, encoding_info: EncodingInfo, ctx: PipelineContext
) -> float:
    """Return 0.0--1.0 indicating how well *data* matches the encoding's structure.

    For single-byte encodings, always returns 0.0.  For empty data, always
    returns 0.0.

    :param data: The raw byte data to analyze.
    :param encoding_info: Metadata for the encoding to probe.
    :param ctx: Pipeline context for caching analysis results.
    :returns: A structural fit score between 0.0 and 1.0.
    """
    if not data or not encoding_info.is_multibyte:
        return 0.0

    result = _get_analysis(data, encoding_info.name, ctx)
    if result is None:
        return 0.0

    return result[0]  # pair_ratio


def compute_multibyte_byte_coverage(
    data: bytes,
    encoding_info: EncodingInfo,
    ctx: PipelineContext,
    non_ascii_count: int | None = None,
) -> float:
    """Ratio of non-ASCII bytes that participate in valid multi-byte sequences.

    Genuine CJK text has nearly all non-ASCII bytes paired into valid
    multi-byte sequences (coverage close to 1.0), while Latin text with
    scattered high bytes has many orphan bytes (coverage well below 1.0).

    :param data: The raw byte data to analyze.
    :param encoding_info: Metadata for the encoding to probe.
    :param ctx: Pipeline context for caching analysis results.
    :param non_ascii_count: Pre-computed count of non-ASCII bytes, or ``None``
        to compute from *data*.
    :returns: A coverage ratio between 0.0 and 1.0.
    """
    if not data or not encoding_info.is_multibyte:
        return 0.0

    result = _get_analysis(data, encoding_info.name, ctx)
    if result is None:
        return 0.0

    mb_bytes = result[1]

    non_ascii = (
        non_ascii_count
        if non_ascii_count is not None
        else len(data) - len(data.translate(None, HIGH_BYTES))
    )
    if non_ascii == 0:
        return 0.0

    return mb_bytes / non_ascii


def compute_lead_byte_diversity(
    data: bytes, encoding_info: EncodingInfo, ctx: PipelineContext
) -> int:
    """Count distinct lead byte values in valid multi-byte pairs.

    Genuine CJK text uses lead bytes from across the encoding's full
    repertoire.  European text falsely matching a CJK structural scorer
    clusters lead bytes in a narrow band.

    :param data: The raw byte data to analyze.
    :param encoding_info: Metadata for the encoding to probe.
    :param ctx: Pipeline context for caching analysis results.
    :returns: The number of distinct lead byte values found.
    """
    if not data or not encoding_info.is_multibyte:
        return 0
    result = _get_analysis(data, encoding_info.name, ctx)
    if result is None:
        return 256  # Unknown encoding -- don't gate
    return result[2]  # lead_diversity
