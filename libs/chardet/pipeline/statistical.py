"""Stage 3: Statistical bigram scoring.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.models import BigramProfile, score_best_language
from chardet.pipeline import DetectionResult
from chardet.registry import EncodingInfo


def score_candidates(
    data: bytes, candidates: tuple[EncodingInfo, ...]
) -> list[DetectionResult]:
    """Score all candidates and return results sorted by confidence descending.

    :param data: The raw byte data to score.
    :param candidates: Encoding candidates to evaluate.
    :returns: A list of :class:`DetectionResult` sorted by confidence.
    """
    if not data or not candidates:
        return []

    profile = BigramProfile(data)
    scores: list[tuple[str, float, str | None]] = []

    for enc in candidates:
        s, lang = score_best_language(data, enc.name, profile=profile)
        if s > 0.0:
            scores.append((enc.name, s, lang))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        DetectionResult(encoding=name, confidence=s, language=lang)
        for name, s, lang in scores
    ]
