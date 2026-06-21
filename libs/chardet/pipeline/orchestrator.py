"""Pipeline orchestrator — runs all detection stages in sequence.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import warnings

from chardet._utils import DEFAULT_MAX_BYTES
from chardet.enums import EncodingEra
from chardet.models import (
    BigramProfile,
    has_model_variants,
    infer_language,
    score_best_language,
)
from chardet.pipeline import (
    _NONE_RESULT,
    DETERMINISTIC_CONFIDENCE,
    HIGH_BYTES,
    DetectionResult,
    PipelineContext,
)
from chardet.pipeline.ascii import detect_ascii
from chardet.pipeline.binary import is_binary
from chardet.pipeline.bom import detect_bom
from chardet.pipeline.confusion import resolve_confusion_groups
from chardet.pipeline.escape import detect_escape_encoding
from chardet.pipeline.magic import detect_magic
from chardet.pipeline.markup import detect_markup_charset
from chardet.pipeline.statistical import score_candidates
from chardet.pipeline.structural import (
    compute_lead_byte_diversity,
    compute_multibyte_byte_coverage,
    compute_structural_score,
)
from chardet.pipeline.utf8 import detect_utf8
from chardet.pipeline.utf1632 import detect_utf1632_patterns
from chardet.pipeline.validity import filter_by_validity
from chardet.registry import REGISTRY, EncodingInfo, get_candidates

_BINARY_RESULT = DetectionResult(
    encoding=None,
    confidence=DETERMINISTIC_CONFIDENCE,
    language=None,
    mime_type="application/octet-stream",
)
# Threshold at which a CJK structural score is confident enough to trigger
# combined structural+statistical ranking rather than purely statistical.
_STRUCTURAL_CONFIDENCE_THRESHOLD = 0.85

# Maximum bytes used for statistical bigram scoring.  Bigram models
# converge quickly — 16 KB is sufficient for discrimination across all
# language models (single-byte and multi-byte alike) while avoiding
# unnecessary work on large files.  Experimentally verified: 0 real
# accuracy losses across 835 test files at this threshold.
_STAT_SCORE_MAX_BYTES = 16384

# Common Western Latin encodings that share the iso-8859-1 character
# repertoire for the byte values where iso-8859-10 is indistinguishable.
# Used as swap targets when demoting iso-8859-10 — we prefer these over
# iso-8859-10, but do not want to accidentally promote an unrelated encoding
# (e.g. windows-1254).
_COMMON_LATIN_ENCODINGS: frozenset[str] = frozenset(
    {
        "iso8859-1",
        "iso8859-15",
        "cp1252",
    }
)

# Bytes where iso-8859-10 decodes to a different character than iso-8859-1.
# Computed programmatically via:
#   {b for b in range(0x80, 0x100)
#    if bytes([b]).decode('iso-8859-10') != bytes([b]).decode('iso-8859-1')}
_ISO_8859_10_DISTINGUISHING: frozenset[int] = frozenset(
    {
        0xA1,
        0xA2,
        0xA3,
        0xA4,
        0xA5,
        0xA6,
        0xA8,
        0xA9,
        0xAA,
        0xAB,
        0xAC,
        0xAE,
        0xAF,
        0xB1,
        0xB2,
        0xB3,
        0xB4,
        0xB5,
        0xB6,
        0xB8,
        0xB9,
        0xBA,
        0xBB,
        0xBC,
        0xBD,
        0xBE,
        0xBF,
        0xC0,
        0xC7,
        0xC8,
        0xCA,
        0xCC,
        0xD1,
        0xD2,
        0xD7,
        0xD9,
        0xE0,
        0xE7,
        0xE8,
        0xEA,
        0xEC,
        0xF1,
        0xF2,
        0xF7,
        0xF9,
        0xFF,
    }
)

# Bytes where iso-8859-14 decodes to a different character than iso-8859-1.
# Computed programmatically via:
#   {b for b in range(0x80, 0x100)
#    if bytes([b]).decode('iso-8859-14') != bytes([b]).decode('iso-8859-1')}
_ISO_8859_14_DISTINGUISHING: frozenset[int] = frozenset(
    {
        0xA1,
        0xA2,
        0xA4,
        0xA5,
        0xA6,
        0xA8,
        0xAA,
        0xAB,
        0xAC,
        0xAF,
        0xB0,
        0xB1,
        0xB2,
        0xB3,
        0xB4,
        0xB5,
        0xB7,
        0xB8,
        0xB9,
        0xBA,
        0xBB,
        0xBC,
        0xBD,
        0xBE,
        0xBF,
        0xD0,
        0xD7,
        0xDE,
        0xF0,
        0xF7,
        0xFE,
    }
)

# Bytes where windows-1254 has Turkish-specific characters that differ from
# windows-1252.  Windows-1254 differs from windows-1252 at 8 byte positions.
# Two (0x8E, 0x9E) are undefined in Windows-1254 but defined in Windows-1252;
# these are excluded here because undefined bytes are not useful for
# identifying Turkish text.  The remaining six positions map to
# Turkish-specific letters and are the primary distinguishing signal.
_WINDOWS_1254_DISTINGUISHING: frozenset[int] = frozenset(
    {0xD0, 0xDD, 0xDE, 0xF0, 0xFD, 0xFE}
)

# Encodings that are often false positives when their distinguishing bytes
# are absent.  Keyed by encoding name -> frozenset of byte values where
# that encoding differs from iso-8859-1 (or windows-1252 in the case of
# windows-1254).
# Bytes where HP-Roman8 maps to lowercase accented letters but ISO-8859-1
# maps to uppercase letters.  Real HP-Roman8 text (from HP-UX terminals)
# contains these bytes; data misdetected as HP-Roman8 typically does not.
#   {b for b in range(0x80, 0x100)
#    if (unicodedata.category(bytes([b]).decode('hp-roman8')) == 'Ll'
#        and unicodedata.category(bytes([b]).decode('iso-8859-1')) == 'Lu')}
_HP_ROMAN8_DISTINGUISHING: frozenset[int] = frozenset(
    {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC4,
        0xC5,
        0xC6,
        0xC7,
        0xC8,
        0xC9,
        0xCA,
        0xCB,
        0xCC,
        0xCD,
        0xCE,
        0xCF,
        0xD1,
        0xD4,
        0xD5,
        0xD6,
        0xD9,
        0xDD,
        0xDE,
    }
)

_DEMOTION_CANDIDATES: dict[str, frozenset[int]] = {
    "iso8859-10": _ISO_8859_10_DISTINGUISHING,
    "iso8859-14": _ISO_8859_14_DISTINGUISHING,
    "cp1254": _WINDOWS_1254_DISTINGUISHING,
    "hp-roman8": _HP_ROMAN8_DISTINGUISHING,
}

# Bytes where KOI8-T maps to Tajik-specific Cyrillic letters but KOI8-R
# maps to box-drawing characters.  Presence of any of these bytes is strong
# evidence for KOI8-T over KOI8-R.
_KOI8_T_DISTINGUISHING: frozenset[int] = frozenset(
    {0x80, 0x81, 0x83, 0x8A, 0x8C, 0x8D, 0x8E, 0x90, 0xA1, 0xA2, 0xA5, 0xB5}
)


# Markup charset declarations that commonly refer to a Windows superset
# encoding rather than the strict standard encoding.  Japanese web content
# almost universally declares "Shift_JIS" but actually uses CP932 extensions;
# similarly, Korean web content declares "EUC-KR" but uses CP949/UHC.
# When the declared encoding resolves to the base (left), we check whether
# the superset (right) is a better structural match.
_MARKUP_SUPERSET_PROMOTIONS: dict[str, str] = {
    "shift_jis_2004": "cp932",
    "euc_kr": "cp949",
}


def _try_promote_markup_superset(
    data: bytes,
    markup_result: DetectionResult,
    allowed: frozenset[str],
) -> DetectionResult:
    """Promote a markup-declared encoding to its superset when structural evidence supports it.

    If the declared encoding has a known superset, the superset validates the
    data, and the superset's structural score is materially better, return a
    new result using the superset encoding.  Otherwise return the original.
    """
    if markup_result.encoding is None:
        return markup_result
    superset_name = _MARKUP_SUPERSET_PROMOTIONS.get(markup_result.encoding)
    if superset_name is None or superset_name not in allowed:
        return markup_result
    superset_info = REGISTRY[superset_name]
    # Validate: superset must be able to decode the data
    try:
        data.decode(superset_name, errors="strict")
    except (UnicodeDecodeError, LookupError):
        return markup_result
    # Compare structural scores
    ctx = PipelineContext()
    base_score = compute_structural_score(data, REGISTRY[markup_result.encoding], ctx)
    superset_score = compute_structural_score(data, superset_info, ctx)
    if superset_score > base_score:
        return DetectionResult(
            superset_name,
            markup_result.confidence,
            markup_result.language,
            markup_result.mime_type,
        )
    return markup_result


def _make_fallback_or_none(
    encoding: str,
    allowed: frozenset[str],
    param_name: str,
) -> list[DetectionResult]:
    """Return a low-confidence result for *encoding*, or ``encoding=None`` if filtered out.

    ``stacklevel=5`` targets the public caller:
    detect() -> run_pipeline() -> _run_pipeline_core() -> _make_fallback_or_none().
    """
    if encoding not in allowed:
        warnings.warn(
            f"{param_name} {encoding!r} is excluded by "
            f"include_encodings/exclude_encodings; returning encoding=None",
            UserWarning,
            stacklevel=5,
        )
        return [_NONE_RESULT]
    return [DetectionResult(encoding=encoding, confidence=0.10, language=None)]


def _should_demote(encoding: str, data: bytes) -> bool:
    """Return True if encoding is a demotion candidate with no distinguishing bytes.

    Checks whether any non-ASCII byte in *data* falls in the set of byte
    values that decode differently under the given encoding vs iso-8859-1.
    If none do, the data is equally valid under both encodings and there is
    no byte-level evidence for preferring the candidate encoding.
    """
    distinguishing = _DEMOTION_CANDIDATES.get(encoding)
    if distinguishing is None:
        return False
    return not any(b in distinguishing for b in data if b > 0x7F)


# Minimum structural score (valid multi-byte sequences / lead bytes) required
# to keep a CJK multi-byte candidate.  Below this threshold the encoding is
# eliminated as a false positive (e.g. Shift_JIS matching Latin data where
# scattered high bytes look like lead bytes but rarely form valid pairs).
_CJK_MIN_MB_RATIO = 0.05
# Minimum number of non-ASCII bytes required for a CJK candidate to survive
# gating.  Very short inputs are validated by the other gates (structural
# pair ratio, byte coverage) and by coverage-aware boosting in statistical
# scoring — so we keep this threshold low to let even 1-character CJK
# inputs compete.
_CJK_MIN_NON_ASCII = 2
# Minimum ratio of non-ASCII bytes that must participate in valid multi-byte
# sequences for a CJK candidate to survive gating.  Genuine CJK text has
# nearly all non-ASCII bytes in valid pairs (coverage >= 0.95); Latin text
# with scattered high bytes has many orphan bytes (coverage often < 0.5).
# The lowest true-positive coverage in the test suite is ~0.39 (a CP932 HTML
# file with many half-width katakana).
_CJK_MIN_BYTE_COVERAGE = 0.35
# Minimum number of distinct lead byte values for a CJK candidate to
# survive gating.  Genuine CJK text uses a wide range of lead bytes;
# European false positives cluster in a narrow band.  Only applied when
# there are enough non-ASCII bytes to expect diversity (see
# _CJK_DIVERSITY_MIN_NON_ASCII).
_CJK_MIN_LEAD_DIVERSITY = 4
# Minimum non-ASCII byte count before applying the lead diversity gate.
# Very small files (e.g. 8 non-ASCII bytes) may genuinely have low
# diversity even for real CJK text (e.g. repeated katakana).
_CJK_DIVERSITY_MIN_NON_ASCII = 16


def _gate_cjk_candidates(
    data: bytes,
    valid_candidates: tuple[EncodingInfo, ...],
    ctx: PipelineContext,
) -> tuple[EncodingInfo, ...]:
    """Eliminate CJK multi-byte candidates that lack genuine multi-byte structure.

    Four checks are applied in order to each multi-byte candidate:

    1. **Structural pair ratio** (valid_pairs / lead_bytes) must be
       >= ``_CJK_MIN_MB_RATIO``.  Catches files with many orphan lead bytes.

    2. **Minimum non-ASCII byte count**: the data must contain at least
       ``_CJK_MIN_NON_ASCII`` bytes > 0x7F.  Tiny files with 1-5 high bytes
       can accidentally form perfect pairs and score 1.0 structurally.

    3. **Byte coverage** (non-ASCII bytes in valid multi-byte sequences /
       total non-ASCII bytes) must be >= ``_CJK_MIN_BYTE_COVERAGE``.  Latin
       text has many high bytes that are NOT consumed by multi-byte pairs;
       genuine CJK text has nearly all high bytes accounted for.

    4. **Lead byte diversity**: the number of distinct lead byte values in
       valid pairs must be >= ``_CJK_MIN_LEAD_DIVERSITY``.  Genuine CJK text
       draws from a wide repertoire of lead bytes; European false positives
       cluster in a narrow band (e.g. 0xC0-0xDF for accented Latin).

    Returns the filtered candidate list.  Structural scores are cached in
    ``ctx.mb_scores`` for reuse in Stage 2b.
    """
    gated: list[EncodingInfo] = []
    for enc in valid_candidates:
        if enc.is_multibyte:
            mb_score = compute_structural_score(data, enc, ctx)
            ctx.mb_scores[enc.name] = mb_score
            if mb_score < _CJK_MIN_MB_RATIO:
                continue  # No multi-byte structure -> eliminate
            if ctx.non_ascii_count is None:
                ctx.non_ascii_count = len(data) - len(data.translate(None, HIGH_BYTES))
            if ctx.non_ascii_count < _CJK_MIN_NON_ASCII:
                continue  # Too few high bytes to trust the score
            byte_coverage = compute_multibyte_byte_coverage(
                data, enc, ctx, non_ascii_count=ctx.non_ascii_count
            )
            ctx.mb_coverage[enc.name] = byte_coverage
            if byte_coverage < _CJK_MIN_BYTE_COVERAGE:
                continue  # Most high bytes are orphans -> not CJK
            if ctx.non_ascii_count >= _CJK_DIVERSITY_MIN_NON_ASCII:
                lead_diversity = compute_lead_byte_diversity(data, enc, ctx)
                if lead_diversity < _CJK_MIN_LEAD_DIVERSITY:
                    continue  # Too few distinct lead bytes -> not CJK
        gated.append(enc)
    return tuple(gated)


def _score_structural_candidates(
    data: bytes,
    structural_scores: list[tuple[str, float]],
    valid_candidates: tuple[EncodingInfo, ...],
    ctx: PipelineContext,
) -> list[DetectionResult]:
    """Score structurally-valid CJK candidates using statistical bigrams.

    When multiple CJK encodings score equally high structurally, statistical
    scoring differentiates them (e.g. euc-jp vs big5 for Japanese data).
    Single-byte candidates are also scored and included so that the caller
    can compare CJK vs single-byte confidence.

    Multi-byte candidates with high byte coverage (>= 0.95) receive a
    confidence boost proportional to coverage.  When nearly all non-ASCII
    bytes form valid multi-byte pairs, the structural evidence is strong
    and should increase the candidate's ranking relative to single-byte
    alternatives whose bigram models may score higher on small samples.

    Note: boosted confidence values may exceed 1.0 and are used only for
    relative ranking among candidates.  ``run_pipeline`` clamps all
    confidence values to [0.0, 1.0] before returning to callers.
    """
    enc_lookup: dict[str, EncodingInfo] = {
        e.name: e for e in valid_candidates if e.is_multibyte
    }
    valid_mb = tuple(
        enc_lookup[name] for name, _sc in structural_scores if name in enc_lookup
    )
    single_byte = tuple(e for e in valid_candidates if not e.is_multibyte)
    results = list(
        score_candidates(data[:_STAT_SCORE_MAX_BYTES], (*valid_mb, *single_byte))
    )

    # Boost multi-byte candidates with high byte coverage.
    boosted: list[DetectionResult] = []
    for r in results:
        coverage = ctx.mb_coverage.get(r.encoding, 0.0) if r.encoding else 0.0
        if coverage >= 0.95:
            boosted.append(
                DetectionResult(
                    r.encoding, r.confidence * (1 + coverage), r.language, r.mime_type
                )
            )
        else:
            boosted.append(r)
    boosted.sort(key=lambda x: x.confidence, reverse=True)
    return boosted


def _demote_niche_latin(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Demote niche Latin encodings when no distinguishing bytes are present.

    Some bigram models (e.g. iso-8859-10, iso-8859-14, windows-1254) can win
    on data that contains only bytes shared with common Western Latin
    encodings.  When there is no byte-level evidence for the winning
    encoding, promote the first common Western Latin candidate to the top and
    push the demoted encoding to last.
    """
    if (
        len(results) > 1
        and results[0].encoding is not None
        and _should_demote(results[0].encoding, data)
    ):
        demoted_encoding = results[0].encoding
        top_conf = results[0].confidence
        for r in results[1:]:
            if r.encoding in _COMMON_LATIN_ENCODINGS:
                promoted = DetectionResult(
                    r.encoding, top_conf, r.language, r.mime_type
                )
                others = [
                    x for x in results if x.encoding != demoted_encoding and x is not r
                ]
                demoted_entries = [x for x in results if x.encoding == demoted_encoding]
                return [promoted, *others, *demoted_entries]
    return results


def _promote_koi8t(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Promote KOI8-T over KOI8-R when Tajik-specific bytes are present.

    KOI8-T and KOI8-R share the entire 0xC0-0xFF Cyrillic letter block,
    making statistical discrimination difficult.  However, KOI8-T maps 12
    bytes in 0x80-0xBF to Tajik-specific Cyrillic letters where KOI8-R has
    box-drawing characters.  If any of these bytes appear, KOI8-T is the
    better match.
    """
    if not results or results[0].encoding != "koi8-r":
        return results
    # Check if KOI8-T is anywhere in the results
    koi8t_idx = next((i for i, r in enumerate(results) if r.encoding == "koi8-t"), None)
    if koi8t_idx is None:
        return results
    # Check for Tajik-specific bytes
    if any(b in _KOI8_T_DISTINGUISHING for b in data if b > 0x7F):
        koi8t_result = results[koi8t_idx]
        top_conf = results[0].confidence
        promoted = DetectionResult(
            koi8t_result.encoding,
            top_conf,
            koi8t_result.language,
            koi8t_result.mime_type,
        )
        others = [r for i, r in enumerate(results) if i != koi8t_idx]
        return [promoted, *others]
    return results


# Maximum bytes of data used for language scoring in _fill_language.
# Language bigrams converge quickly — 2 KB is sufficient for discrimination
# across all language models while keeping Tier 3 (language-model scoring) fast.
_LANG_SCORE_MAX_BYTES = 2048


def _to_utf8(data: bytes, encoding: str) -> bytes | None:
    """Decode data from encoding and re-encode as UTF-8 for language scoring.

    Returns None if the encoding is unknown. For UTF-8, returns data as-is.
    Uses ``errors="ignore"`` because the data already passed byte-validity
    filtering for the detected encoding; any residual invalid bytes are
    irrelevant for language scoring.
    """
    if encoding == "utf-8":
        return data
    try:
        return data.decode(encoding, errors="ignore").encode(
            "utf-8", errors="surrogatepass"
        )
    except (LookupError, TypeError, ValueError):
        return None


def _fill_metadata(
    data: bytes, results: list[DetectionResult]
) -> list[DetectionResult]:
    """Fill in language and mime_type for results missing them.

    **Language** (only for text results where ``encoding is not None``):

    Tier 1: single-language encodings via hardcoded map (instant).
    Tier 2: multi-language encodings via statistical bigram scoring (lazy).
    Tier 3: decode to UTF-8, score against UTF-8 language models (universal fallback).

    **MIME type**: text results default to ``"text/plain"``, binary results
    (``encoding is None``) default to ``"application/octet-stream"``.
    """
    filled: list[DetectionResult] = []
    profile: BigramProfile | None = None
    utf8_profile: BigramProfile | None = None
    for result in results:
        lang = result.language
        if lang is None and result.encoding is not None:
            # Tier 1: single-language encoding
            lang = infer_language(result.encoding)
            # Tier 2: statistical scoring for multi-language encodings
            if lang is None and data and has_model_variants(result.encoding):
                if profile is None:
                    profile = BigramProfile(data)
                _, lang = score_best_language(data, result.encoding, profile=profile)
            # Tier 3: decode to UTF-8, score against UTF-8 language models
            if lang is None and data and has_model_variants("utf-8"):
                utf8_data = _to_utf8(data, result.encoding)
                if utf8_data:
                    if utf8_profile is None or result.encoding != "utf-8":
                        utf8_profile = BigramProfile(utf8_data)
                    _, lang = score_best_language(
                        utf8_data, "utf-8", profile=utf8_profile
                    )

        mime = result.mime_type
        if mime is None:
            mime = (
                "text/plain"
                if result.encoding is not None
                else "application/octet-stream"
            )

        if lang != result.language or mime != result.mime_type:
            filled.append(
                DetectionResult(result.encoding, result.confidence, lang, mime)
            )
        else:
            filled.append(result)
    return filled


def _postprocess_results(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Apply confusion resolution, niche Latin demotion, and KOI8-T promotion."""
    results = resolve_confusion_groups(data, results)
    results = _demote_niche_latin(data, results)
    return _promote_koi8t(data, results)


def _run_pipeline_core(  # noqa: PLR0913
    data: bytes,
    encoding_era: EncodingEra,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
) -> list[DetectionResult]:
    """Core pipeline logic. Returns list of results sorted by confidence."""
    ctx = PipelineContext()
    data = data[:max_bytes]

    # Build candidate set once — used for both early-exit gating and
    # statistical scoring.  The set incorporates encoding_era, include, and
    # exclude filters so all pipeline stages are gated consistently.
    candidates = get_candidates(encoding_era, include_encodings, exclude_encodings)
    allowed: frozenset[str] = frozenset(enc.name for enc in candidates)

    if not data:
        return _make_fallback_or_none(
            empty_input_encoding, allowed, "empty_input_encoding"
        )

    # Stage 1a: BOM detection (runs first — BOMs are definitive and
    # UTF-16/32 data looks binary due to null bytes)
    bom_result = detect_bom(data)
    if bom_result is not None and bom_result.encoding in allowed:
        return [bom_result]

    # Stage 1a+: UTF-16/32 null-byte pattern detection (for files without
    # BOMs — must run before binary detection since these encodings contain
    # many null bytes that would trigger the binary check)
    utf1632_result = detect_utf1632_patterns(data)
    if utf1632_result is not None and utf1632_result.encoding in allowed:
        return [utf1632_result]

    # Escape-sequence encodings (ISO-2022, HZ-GB-2312, UTF-7): must run
    # before binary detection (ESC is a control byte) and before ASCII
    # detection (HZ-GB-2312 uses only printable ASCII plus tildes).
    escape_result = detect_escape_encoding(data)
    if (
        escape_result is not None
        and escape_result.encoding is not None
        and escape_result.encoding in allowed
    ):
        return [escape_result]

    # Magic number detection for known binary formats — runs before
    # UTF-8/ASCII prechecks to avoid unnecessary analysis on binary data.
    magic_result = detect_magic(data)
    if magic_result is not None:
        return [magic_result]

    # Pre-check UTF-8 to prevent false binary classification.  Valid UTF-8
    # with multi-byte sequences can contain control bytes (e.g. ESC for ANSI
    # codes) that would otherwise exceed the binary threshold.  We compute
    # the result now but return it at the normal pipeline position (after
    # markup) so that explicit charset declarations still take precedence.
    utf8_precheck = detect_utf8(data)

    # Pre-check ASCII to prevent false binary classification.  ASCII text
    # with null byte separators (e.g. find -print0 output) would exceed the
    # binary threshold due to the null bytes.  Like the UTF-8 precheck, we
    # compute the result now but return it at the normal position (after
    # markup) so explicit charset declarations still take precedence.
    ascii_precheck = detect_ascii(data)

    # Stage 0: Binary detection (skip when data is valid UTF-8 or ASCII)
    # Binary detection (encoding=None) is NOT gated by filters.
    if (
        utf8_precheck is None
        and ascii_precheck is None
        and is_binary(data, max_bytes=max_bytes)
    ):
        return [_BINARY_RESULT]

    # Stage 1b: Markup charset extraction (before ASCII/UTF-8 so explicit
    # declarations like <?xml encoding="iso-8859-1"?> are honoured even
    # when the bytes happen to be pure ASCII or valid UTF-8).
    markup_result = detect_markup_charset(data)
    if markup_result is not None and markup_result.encoding in allowed:
        markup_result = _try_promote_markup_superset(data, markup_result, allowed)
        return [markup_result]

    # Stage 1c: ASCII (use pre-computed result)
    if ascii_precheck is not None and ascii_precheck.encoding in allowed:
        return [ascii_precheck]

    # Stage 1d: UTF-8 structural validation (use pre-computed result)
    if utf8_precheck is not None and utf8_precheck.encoding in allowed:
        return [utf8_precheck]

    # Stage 2a: Byte validity filtering
    valid_candidates = filter_by_validity(data, candidates)

    if not valid_candidates:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    # Gate: eliminate CJK multi-byte candidates that lack genuine
    # multi-byte structure.  Cache structural scores for Stage 2b.
    valid_candidates = _gate_cjk_candidates(data, valid_candidates, ctx)

    if not valid_candidates:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    # Stage 2b: Structural probing for multi-byte encodings
    # Reuse scores already computed during the CJK gate above.
    structural_scores: list[tuple[str, float]] = []
    for enc in valid_candidates:
        if enc.is_multibyte:
            score = ctx.mb_scores.get(enc.name)
            if score is None:  # pragma: no cover - gate always populates cache
                score = compute_structural_score(data, enc, ctx)
            if score > 0.0:
                structural_scores.append((enc.name, score))

    # If a multi-byte encoding scored very high, score all candidates
    # (CJK + single-byte) statistically.
    if structural_scores:
        structural_scores.sort(key=lambda x: x[1], reverse=True)
        _, best_score = structural_scores[0]
        if best_score >= _STRUCTURAL_CONFIDENCE_THRESHOLD:
            results = _score_structural_candidates(
                data, structural_scores, valid_candidates, ctx
            )
            if results:
                return _postprocess_results(data, results)

    # Stage 3: Statistical scoring for all remaining candidates.
    # Bigram models converge quickly and don't benefit from scanning
    # beyond 16 KB — cap the data to avoid unnecessary work on large files.
    stat_data = data[:_STAT_SCORE_MAX_BYTES]
    results = list(score_candidates(stat_data, tuple(valid_candidates)))
    if not results:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    return _postprocess_results(data, results)


def run_pipeline(  # noqa: PLR0913
    data: bytes,
    encoding_era: EncodingEra,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
) -> list[DetectionResult]:
    """Run the full detection pipeline.

    :param data: The raw byte data to analyze.
    :param encoding_era: Filter candidates to a specific era of encodings.
    :param max_bytes: Maximum number of bytes to process.
    :param include_encodings: If not ``None``, only return these encodings.
    :param exclude_encodings: If not ``None``, never return these encodings.
    :param no_match_encoding: Encoding returned when no candidate survives.
    :param empty_input_encoding: Encoding returned for empty input.
    :returns: A list of :class:`DetectionResult` sorted by confidence descending.
    """
    results = _run_pipeline_core(
        data,
        encoding_era,
        max_bytes,
        include_encodings=include_encodings,
        exclude_encodings=exclude_encodings,
        no_match_encoding=no_match_encoding,
        empty_input_encoding=empty_input_encoding,
    )
    # Language scoring uses only the first 2 KB — bigrams converge quickly
    # and this keeps Tier 3 (language-model scoring) fast even on large inputs.
    results = _fill_metadata(data[:_LANG_SCORE_MAX_BYTES], results)
    if not results:  # pragma: no cover
        msg = "pipeline must always return at least one result"
        raise RuntimeError(msg)
    # Clamp confidence to [0.0, 1.0] at the public API boundary.  Internal
    # stages may boost confidence above 1.0 for ranking purposes (e.g.
    # CJK byte-coverage boost), but callers expect a probability-like value.
    return [
        DetectionResult(r.encoding, min(r.confidence, 1.0), r.language, r.mime_type)
        if r.confidence > 1.0
        else r
        for r in results
    ]
