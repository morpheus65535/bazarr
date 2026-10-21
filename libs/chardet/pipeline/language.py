"""Three-tier language detection for filling DetectionResult languages.

Tier 1: hardcoded mapping for single-language encodings (e.g. Big5 -> Chinese).
Tier 2: statistical bigram scoring against the encoding's language-model variants.
Tier 3: decode to UTF-8 and score against the UTF-8 byte-level language models.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.models import (
    _THIN_RARE_MAX_BYTES,
    RARE_LANGUAGES,
    BigramProfile,
    has_model_variants,
    infer_language,
    score_best_language,
)
from chardet.pipeline import DetectionResult

# Maximum bytes of data used for language scoring.
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


def fill_languages(
    data: bytes, results: list[DetectionResult]
) -> list[DetectionResult]:
    """Fill missing ``language`` fields on text results via the three-tier algorithm.

    Tier 1: single-language encodings via hardcoded map (instant).
    Tier 2: multi-language encodings via statistical bigram scoring (lazy).
    Tier 3: decode to UTF-8, score against UTF-8 language models (universal fallback).

    Tiers 2 and 3 score in the IDF-weighted space of
    :meth:`~chardet.models.BigramProfile.for_language`, not the plain
    cosine the encoding ranking uses: with 49 languages in play, the plain
    cosine let the UTF-8 bigram for ``é`` alone hand French text to
    Hungarian.

    Binary results (``encoding is None``) are passed through unchanged, as
    are results that already have a non-``None`` language — except a
    :data:`~chardet.models.RARE_LANGUAGES` label on a thin input, which is
    re-derived through the same scoring so the thin-rare demotion band
    applies to statistically-attached labels too, not only to labels this
    function computes.  A re-derivation can only *demote* to a prevalent
    language; it never swaps one rare label for another.

    :param data: The raw byte data the results were produced from.  Truncated
        to the first 2 KB internally — bigram language models converge quickly.
    :param results: A list of :class:`DetectionResult` from the pipeline.
    :returns: A list of results with ``language`` filled in where possible.
    """
    data = data[:_LANG_SCORE_MAX_BYTES]
    # Thinness is judged once, on the bytes the caller actually has.  Tier 3
    # transcodes to UTF-8 before scoring, which can inflate curly punctuation
    # 3x — judging length after that would exempt exactly the inputs the
    # band exists for.
    thin = 0 < len(data) < _THIN_RARE_MAX_BYTES
    filled: list[DetectionResult] = []
    profile: BigramProfile | None = None
    utf8_profile: BigramProfile | None = None
    utf8_profile_src: bytes | None = None
    for result in results:
        recheck = (
            thin
            and result.language is not None
            and result.language in RARE_LANGUAGES
            and result.encoding is not None
        )
        if result.encoding is None or (result.language is not None and not recheck):
            filled.append(result)
            continue
        encoding = result.encoding
        # Tier 1: single-language encoding (skipped on re-check: the label
        # exists; only the scored tiers can justify a demotion)
        lang = None if recheck else infer_language(encoding)
        # Tier 2: statistical scoring for multi-language encodings
        if lang is None and data and has_model_variants(encoding):
            if profile is None:
                profile = BigramProfile.for_language(data)
            _, lang = score_best_language(
                data,
                encoding,
                profile=profile,
                demote_thin_rare=thin,
                language_weighting=True,
            )
        # Tier 3: decode to UTF-8, score against UTF-8 language models.
        # Also entered by a thin rare Tier-2 label: an encoding whose
        # variant set is all-Celtic (iso8859-14) can never offer the band a
        # prevalent rival, so the utf-8 models — which always have one —
        # get the deciding vote.  Their verdict is only accepted as a
        # demotion; a rare verdict leaves the Tier-2 label in place.
        escalate = thin and lang is not None and lang in RARE_LANGUAGES
        if (lang is None or escalate) and data and has_model_variants("utf-8"):
            utf8_data = _to_utf8(data, encoding)
            if utf8_data:
                if utf8_data != utf8_profile_src:
                    utf8_profile = BigramProfile.for_language(utf8_data)
                    utf8_profile_src = utf8_data
                _, utf8_lang = score_best_language(
                    utf8_data,
                    "utf-8",
                    profile=utf8_profile,
                    demote_thin_rare=thin,
                    language_weighting=True,
                )
                if lang is None or (
                    utf8_lang is not None and utf8_lang not in RARE_LANGUAGES
                ):
                    lang = utf8_lang
        if recheck and (lang is None or lang in RARE_LANGUAGES):
            # The band did not fire (or scoring was unavailable): the
            # original label stands.  Never replace one rare label with
            # another — the re-check's only authority is the demotion.
            filled.append(result)
        elif lang is None:
            filled.append(result)
        else:
            filled.append(
                DetectionResult(encoding, result.confidence, lang, result.mime_type)
            )
    return filled
