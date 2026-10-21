"""Stage 3: Statistical bigram scoring.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.models import (
    BigramProfile,
    _get_model_norms,
    get_enc_index,
    get_rowmax,
    score_best_language,
    score_with_profile,
)
from chardet.pipeline import DetectionResult
from chardet.pipeline.postprocess import forced_encodings, scoring_floor
from chardet.registry import EncodingInfo

# Below this many distinct bigrams the upper-bound prescreen costs about as
# much as the full dot products it would avoid, so score everything directly.
_MIN_NONZERO_FOR_PRESCREEN = 64


def _score_all(
    data: bytes,
    candidates: tuple[EncodingInfo, ...],
    profile: BigramProfile,
) -> list[tuple[str, float, str | None]]:
    """Score every candidate fully (no pruning).  Returns (enc, score, lang)."""
    scores: list[tuple[str, float, str | None]] = []
    for enc in candidates:
        s, lang = score_best_language(data, enc.name, profile=profile)
        if s > 0.0:
            scores.append((enc.name, s, lang))
    return scores


def _split_variants(
    candidates: tuple[EncodingInfo, ...],
    profile: BigramProfile,
) -> tuple[
    list[tuple[str, str | None, bytes, str, int]],
    list[tuple[float, int, str, str | None, bytes, str]],
]:
    """Flatten candidate model variants for pruned scoring.

    Returns ``(mb_entries, sb_entries)`` where multi-byte entries are
    ``(enc, lang, table, key, variant_index)`` and single-byte entries are
    ``(upper_bound, variant_index, enc, lang, table, key)`` sorted by
    descending bound.  The upper bound multiplies each lead byte's total
    profile weight by the model's maximum weight for that lead byte — at
    most 256 terms versus one term per distinct bigram for a full score.
    ``variant_index`` is the variant's position in the encoding index, so
    exact score ties resolve to the same variant the full path keeps.
    """
    index = get_enc_index()
    norms = _get_model_norms()
    rowmax = get_rowmax()
    row_freq = profile.row_freq
    nonzero_rows = profile.nonzero_rows
    input_norm = profile.input_norm

    mb_entries: list[tuple[str, str | None, bytes, str, int]] = []
    sb_entries: list[tuple[float, int, str, str | None, bytes, str]] = []
    for enc in candidates:
        variants = index.get(enc.name)
        if variants is None:
            continue
        if enc.is_multibyte_cjk:
            for vi, (lang, table, key) in enumerate(variants):
                mb_entries.append((enc.name, lang, table, key, vi))
            continue
        for vi, (lang, table, key) in enumerate(variants):
            rm = rowmax[key]
            ub_dot = 0
            for b1 in nonzero_rows:
                ub_dot += rm[b1] * row_freq[b1]
            model_norm = norms.get(key)
            if model_norm is None:
                # Unknown norm: cannot bound the score, so never skip.
                ub = float("inf")
            elif model_norm > 0.0:
                ub = ub_dot / (model_norm * input_norm)
            else:
                # Zero norm: score_with_profile returns 0.0 for this model,
                # so bound it at 0.0 instead of dividing by zero.
                ub = 0.0
            sb_entries.append((ub, vi, enc.name, lang, table, key))
    sb_entries.sort(key=lambda e: e[0], reverse=True)
    return mb_entries, sb_entries


def _score_pruned(
    candidates: tuple[EncodingInfo, ...],
    profile: BigramProfile,
) -> list[tuple[str, float, str | None]]:
    """Score candidates, skipping single-byte variants that provably cannot matter.

    Multi-byte variants are always scored fully — the orchestrator may later
    boost their confidence based on structural coverage, so no raw-score
    bound can rule them out.  Single-byte variants are scored in descending
    upper-bound order (see :func:`_split_variants`) and skipped once their
    bound falls below the pruning contract's ``scoring_floor``: such
    variants can affect neither the winner, nor position 1, nor any
    candidate a rank correction can examine.

    Encodings that ``postprocess_results`` inspects regardless of rank
    (the common Western Latin trio for niche-Latin demotion, KOI8-T for the
    KOI8-R promotion) are force-scored when their trigger could fire.
    Because confusion resolution can promote position 1 or any candidate
    within the band into position 0 before those triggers are evaluated,
    the trigger check covers every encoding near the top, not just the
    statistical winner.

    Returns (enc, score, lang) tuples for encodings scoring above zero, in
    candidate order.
    """
    index = get_enc_index()
    mb_entries, sb_entries = _split_variants(candidates, profile)

    best_score: dict[str, float] = {}
    best_lang: dict[str, str | None] = {}
    best_vi: dict[str, int] = {}
    # Running top-2 scores across distinct encodings; the pruning threshold
    # trails the second-best so the top two encodings stay exact.
    top1_enc = ""
    top1 = 0.0
    top2 = 0.0

    def record(enc_name: str, s: float, lang: str | None, vi: int) -> None:
        nonlocal top1_enc, top1, top2
        prev = best_score.get(enc_name)
        if prev is not None and (s < prev or (s == prev and vi >= best_vi[enc_name])):
            # On exact ties keep the variant that comes first in index
            # order, matching score_best_language on the full path.
            return
        best_score[enc_name] = s
        best_lang[enc_name] = lang
        best_vi[enc_name] = vi
        if enc_name == top1_enc:
            top1 = s
        elif s > top1:
            top2 = top1
            top1 = s
            top1_enc = enc_name
        elif s > top2:
            top2 = s

    for enc_name, lang, table, key, vi in mb_entries:
        record(enc_name, score_with_profile(profile, table, key), lang, vi)

    for ub, vi, enc_name, lang, table, key in sb_entries:
        # The floor below which no rank correction can examine a candidate;
        # everything above it must be scored exactly or detect() would
        # diverge from the unpruned full ranking.
        threshold = scoring_floor(top1, top2)
        if ub < threshold:
            # Sorted by descending bound and the threshold only rises, so
            # no later entry can matter either.
            break
        record(enc_name, score_with_profile(profile, table, key), lang, vi)

    # Force-score the encodings the corrections look up by name, when their
    # trigger could fire.  The trigger scan covers everything at or above
    # the contract floor, because confusion resolution may promote any of
    # those candidates to the top before postprocess evaluates its own
    # trigger conditions.
    trigger_floor = scoring_floor(top1, top2)
    near_top = [e for e, s in best_score.items() if s >= trigger_floor]
    forced = forced_encodings(near_top)
    if forced:
        for enc in candidates:
            if enc.name not in forced:
                continue
            # Score every variant: a partially-pruned encoding may otherwise
            # carry an understated best score into the demotion comparison.
            for vi, (lang, table, key) in enumerate(index.get(enc.name, [])):
                record(enc.name, score_with_profile(profile, table, key), lang, vi)

    return [
        (enc.name, best_score[enc.name], best_lang[enc.name])
        for enc in candidates
        if best_score.get(enc.name, 0.0) > 0.0
    ]


def score_candidates(
    data: bytes,
    candidates: tuple[EncodingInfo, ...],
    *,
    full_ranking: bool = False,
) -> list[DetectionResult]:
    """Score all candidates and return results sorted by confidence descending.

    :param data: The raw byte data to score.
    :param candidates: Encoding candidates to evaluate.
    :param full_ranking: When ``True``, score every candidate fully so the
        returned list is complete (needed by ``detect_all``).  When ``False``
        (the default), single-byte candidates that provably cannot affect the
        top of the ranking may be skipped; the winner, position 1, and all
        candidates within the confusion band of the top score are identical
        to the full ranking.
    :returns: A list of :class:`DetectionResult` sorted by confidence.
    """
    if not data or not candidates:
        return []

    profile = BigramProfile(data)
    if profile.input_norm == 0.0:
        return []

    if full_ranking or len(profile.nonzero) < _MIN_NONZERO_FOR_PRESCREEN:
        scores = _score_all(data, candidates, profile)
    else:
        scores = _score_pruned(candidates, profile)

    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        DetectionResult(encoding=name, confidence=s, language=lang)
        for name, s, lang in scores
    ]
