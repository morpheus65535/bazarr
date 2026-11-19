"""Pipeline orchestrator — runs all detection stages in sequence.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import warnings

from chardet._utils import DEFAULT_MAX_BYTES, EVIDENCE_CAP_BYTES, decodes_without_error
from chardet.enums import EncodingEra
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
from chardet.pipeline.escape import detect_escape_encoding
from chardet.pipeline.language import fill_languages
from chardet.pipeline.magic import detect_magic
from chardet.pipeline.markup import detect_markup_charset, promote_markup_superset
from chardet.pipeline.postprocess import postprocess_results
from chardet.pipeline.statistical import score_candidates
from chardet.pipeline.structural import (
    compute_lead_byte_diversity,
    compute_multibyte_byte_coverage,
    compute_structural_score,
)
from chardet.pipeline.utf8 import scan_utf8
from chardet.pipeline.utf1632 import detect_utf1632_patterns
from chardet.pipeline.validity import filter_by_validity
from chardet.registry import EncodingInfo, get_candidates

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


def _hold_validity_past_cap(
    data: bytes,
    evidence: bytes,
    results: list[DetectionResult],
    allowed: frozenset[str],
    no_match_encoding: str,
) -> list[DetectionResult]:
    """Keep the validity contract for the part of the window past the evidence cap.

    Byte-validity filtering converges on the first ``EVIDENCE_CAP_BYTES``
    of the window (ADR-0006), so on a longer window a candidate that
    cannot decode the rest can still reach the top.  What callers rely on
    is that the answer decodes the window chardet examined: they pass
    ``max_bytes`` precisely to say how much of the input the verdict is
    about.  So walk the corrected ranking and drop every entry ahead of
    the first one that decodes the whole window, under the same tolerant
    judgment the validity filter passes on the evidence slice.  Those
    entries are what validity would have removed had it seen the bytes;
    the survivors keep their own ranks and confidences, since nothing
    about the evidence they were scored on has changed.

    The walk is bounded by the ranking's length, each step is one C-speed
    decode that stops at the first bad byte, and it costs nothing at all
    when the window fits inside the cap, which every default call does.
    Entries below the first decodable one are not re-examined, so a
    ``detect_all`` ranking on a long window is exact down to its winner
    and unverified past it.  When no listed entry decodes, the answer is
    the no-match fallback, as it is when validity leaves nothing.
    """
    if len(data) <= len(evidence):
        return results
    for i, r in enumerate(results):
        if r.encoding is not None and decodes_without_error(data, r.encoding):
            return results if i == 0 else results[i:]
    return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")


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
        if enc.is_multibyte_cjk:
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
    *,
    full_ranking: bool = False,
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
        e.name: e for e in valid_candidates if e.is_multibyte_cjk
    }
    valid_mb = tuple(
        enc_lookup[name] for name, _sc in structural_scores if name in enc_lookup
    )
    single_byte = tuple(e for e in valid_candidates if not e.is_multibyte_cjk)
    results = list(
        score_candidates(
            data[:_STAT_SCORE_MAX_BYTES],
            (*valid_mb, *single_byte),
            full_ranking=full_ranking,
        )
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


def _with_default_mime(result: DetectionResult) -> DetectionResult:
    """Default ``mime_type`` to ``text/plain`` (text) or ``application/octet-stream`` (binary)."""
    if result.mime_type is not None:
        return result
    mime = "text/plain" if result.encoding is not None else "application/octet-stream"
    return DetectionResult(result.encoding, result.confidence, result.language, mime)


def _run_pipeline_core(  # noqa: PLR0913
    data: bytes,
    encoding_era: EncodingEra,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
    full_ranking: bool = False,
    input_truncated: bool = False,
) -> list[DetectionResult]:
    """Core pipeline logic. Returns list of results sorted by confidence."""
    ctx = PipelineContext()
    input_truncated = input_truncated or len(data) > max_bytes
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
    bom_result = detect_bom(data, input_truncated=input_truncated)
    if bom_result is not None and bom_result.encoding in allowed:
        return [bom_result]

    # Stage 1a+: UTF-16/32 null-byte pattern detection (for files without
    # BOMs — must run before binary detection since these encodings contain
    # many null bytes that would trigger the binary check)
    utf1632_result = detect_utf1632_patterns(data)
    # The stage samples and decodes the first few KB only.  The answer has
    # to decode the whole window, so a lone surrogate or out-of-range unit
    # past the sample sends the input on to the other stages instead.
    if (
        utf1632_result is not None
        and utf1632_result.encoding is not None
        and utf1632_result.encoding in allowed
        and decodes_without_error(data, utf1632_result.encoding)
    ):
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
    utf8_valid, utf8_precheck = scan_utf8(data)

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
    # when the bytes happen to be pure ASCII).
    markup_result = detect_markup_charset(data)
    if markup_result is not None and markup_result.encoding in allowed:
        # A declaration is honoured over pure ASCII (the declared encoding
        # decodes those bytes identically), but not over genuine UTF-8
        # structure: data containing valid multi-byte UTF-8 sequences is
        # UTF-8 regardless of what the (frequently stale) declaration
        # claims, and decoding it as the declared encoding would produce
        # mojibake.  Keep the markup mime type; only the encoding wins.
        if (
            utf8_precheck is not None
            and utf8_precheck.encoding != markup_result.encoding
            and utf8_precheck.encoding in allowed
        ):
            return [
                DetectionResult(
                    utf8_precheck.encoding,
                    utf8_precheck.confidence,
                    utf8_precheck.language,
                    markup_result.mime_type,
                )
            ]
        # The stage already holds every declaration it returns, and the
        # promotion it may apply, to the whole window.
        markup_result = promote_markup_superset(data, markup_result, allowed)
        return [markup_result]

    # Stage 1c: ASCII (use pre-computed result)
    if ascii_precheck is not None and ascii_precheck.encoding in allowed:
        return [ascii_precheck]

    # Stage 1d: UTF-8 structural validation (use pre-computed result)
    if utf8_precheck is not None and utf8_precheck.encoding in allowed:
        return [utf8_precheck]

    # The filtering, gating, and probing stages below converge on bounded
    # evidence (ADR-0006).  One slice, taken here, feeds them all: the
    # structural analysis cache is keyed by encoding name only, so every
    # consumer must see the same view of the data.  For the decode-safety
    # flip in postprocess, a window that outruns the cap counts as
    # truncation — the slice's tail is a chardet-made cut, not the end of
    # what the caller will decode.
    evidence = data[:EVIDENCE_CAP_BYTES]
    evidence_truncated = input_truncated or len(data) > len(evidence)

    # Stage 2a: Byte validity filtering
    valid_candidates = filter_by_validity(evidence, candidates)

    # The exhaustive UTF-8 check saw the whole window; when it *rejected*
    # the data but the window extends past the evidence cap, the slice
    # alone may still look like valid UTF-8 to the statistical path.  Honor
    # the proof: chardet never calls data UTF-8 that is not valid UTF-8
    # throughout the window.  A missing precheck result is not a rejection
    # — valid UTF-8 with no multi-byte evidence (pure ASCII, ASCII plus
    # control bytes, ASCII plus a truncated tail) also returns None, and
    # ruling utf-8 out for those would be wrong.  (Within the cap the slice
    # is the window, so validity already agrees and this never fires.)
    if not utf8_valid and len(data) > len(evidence):
        valid_candidates = tuple(e for e in valid_candidates if e.name != "utf-8")

    if not valid_candidates:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    # Gate: eliminate CJK multi-byte candidates that lack genuine
    # multi-byte structure.  Cache structural scores for Stage 2b.
    valid_candidates = _gate_cjk_candidates(evidence, valid_candidates, ctx)

    if not valid_candidates:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    # Stage 2b: Structural probing for multi-byte encodings
    # Reuse scores already computed during the CJK gate above.
    structural_scores: list[tuple[str, float]] = []
    for enc in valid_candidates:
        if enc.is_multibyte_cjk:
            score = ctx.mb_scores.get(enc.name)
            if score is None:  # pragma: no cover - gate always populates cache
                score = compute_structural_score(evidence, enc, ctx)
            if score > 0.0:
                structural_scores.append((enc.name, score))

    # If a multi-byte encoding scored very high, score all candidates
    # (CJK + single-byte) statistically.
    if structural_scores:
        structural_scores.sort(key=lambda x: x[1], reverse=True)
        _, best_score = structural_scores[0]
        if best_score >= _STRUCTURAL_CONFIDENCE_THRESHOLD:
            results = _score_structural_candidates(
                evidence,
                structural_scores,
                valid_candidates,
                ctx,
                full_ranking=full_ranking,
            )
            if results:
                results = postprocess_results(
                    evidence, results, input_truncated=evidence_truncated
                )
                return _hold_validity_past_cap(
                    data, evidence, results, allowed, no_match_encoding
                )

    # Stage 3: Statistical scoring for all remaining candidates.
    # Bigram models converge quickly and don't benefit from scanning
    # beyond 16 KB — cap the data to avoid unnecessary work on large files.
    stat_data = evidence[:_STAT_SCORE_MAX_BYTES]
    results = list(
        score_candidates(stat_data, tuple(valid_candidates), full_ranking=full_ranking)
    )
    if not results:
        return _make_fallback_or_none(no_match_encoding, allowed, "no_match_encoding")

    # Rank corrections reason about the same evidence window the ranking
    # came from, which also bounds their byte-presence scans.
    results = postprocess_results(evidence, results, input_truncated=evidence_truncated)
    return _hold_validity_past_cap(data, evidence, results, allowed, no_match_encoding)


def run_pipeline(  # noqa: PLR0913
    data: bytes,
    encoding_era: EncodingEra,
    max_bytes: int = DEFAULT_MAX_BYTES,
    *,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
    no_match_encoding: str = "cp1252",
    empty_input_encoding: str = "utf-8",
    full_ranking: bool = False,
    input_truncated: bool = False,
) -> list[DetectionResult]:
    """Run the full detection pipeline.

    :param data: The raw byte data to analyze.
    :param encoding_era: Filter candidates to a specific era of encodings.
    :param max_bytes: Maximum number of bytes to process.
    :param include_encodings: If not ``None``, only return these encodings.
    :param exclude_encodings: If not ``None``, never return these encodings.
    :param no_match_encoding: Encoding returned when no candidate survives.
    :param empty_input_encoding: Encoding returned for empty input.
    :param full_ranking: When ``True``, statistical scoring evaluates every
        candidate so the returned list is complete (``detect_all`` needs
        this).  When ``False``, candidates that provably cannot affect the
        top of the ranking may be omitted from the tail.
    :param input_truncated: Pass ``True`` when *data* is already a truncated
        view of the caller's input (``UniversalDetector`` caps its buffer at
        ``max_bytes``, which this function cannot see from ``len(data)``
        alone).  Truncation by the ``max_bytes`` slice here is detected
        either way; the flag only ever widens it.
    :returns: A list of :class:`DetectionResult` sorted by confidence descending.
    """
    results = _run_pipeline_core(
        data,
        encoding_era,
        max_bytes,
        input_truncated=input_truncated,
        include_encodings=include_encodings,
        exclude_encodings=exclude_encodings,
        no_match_encoding=no_match_encoding,
        empty_input_encoding=empty_input_encoding,
        full_ranking=full_ranking,
    )
    # Same slice the core ran on: ``max_bytes`` is the caller's cap on what
    # chardet may look at, and language fill is not exempt from it just
    # because it applies a smaller cap of its own.
    results = fill_languages(data[:max_bytes], results)
    # The ANSI-art model is keyed under the "zxx" pseudo-language (ISO 639
    # for "no linguistic content").  Kept internal so language fill does not
    # overwrite it; callers see language=None.
    results = [
        DetectionResult(r.encoding, r.confidence, None, r.mime_type)
        if r.language == "zxx"
        else r
        for r in results
    ]
    results = [_with_default_mime(r) for r in results]
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
