"""Confusion group resolution for similar single-byte encodings.

At runtime, loads pre-computed distinguishing byte maps from confusion.bin
and uses them to resolve statistical scoring ties between similar encodings.

Build-time computation (``compute_confusion_groups``, ``compute_distinguishing_maps``,
``serialize_confusion_data``) lives in ``scripts/confusion_training.py``.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import functools
import importlib.resources
import struct
import warnings

from chardet.models import (
    BigramProfile,
    get_enc_index,
    get_idf_weights,
    score_with_profile,
)
from chardet.pipeline import DetectionResult
from chardet.registry import lookup_encoding

# Type alias for the distinguishing map structure:
# Maps (enc_a, enc_b) -> (distinguishing_byte_set, {byte_val: (cat_a, cat_b)})
DistinguishingMaps = dict[
    tuple[str, str],
    tuple[frozenset[int], dict[int, tuple[str, str]]],
]

# uint8 -> Unicode general category, inverse of the mapping in
# scripts/confusion_training.py used at serialization time.
_INT_TO_CATEGORY: dict[int, str] = {
    0: "Lu",
    1: "Ll",
    2: "Lt",
    3: "Lm",
    4: "Lo",
    5: "Mn",
    6: "Mc",
    7: "Me",
    8: "Nd",
    9: "Nl",
    10: "No",
    11: "Pc",
    12: "Pd",
    13: "Ps",
    14: "Pe",
    15: "Pi",
    16: "Pf",
    17: "Po",
    18: "Sm",
    19: "Sc",
    20: "Sk",
    21: "So",
    22: "Zs",
    23: "Zl",
    24: "Zp",
    25: "Cc",
    26: "Cf",
    27: "Cs",
    28: "Co",
    29: "Cn",
}

# Inverse mapping for serialization — used by scripts/confusion_training.py.
_CATEGORY_TO_INT: dict[str, int] = {v: k for k, v in _INT_TO_CATEGORY.items()}


def deserialize_confusion_data_from_bytes(data: bytes) -> DistinguishingMaps:
    """Load confusion group data from raw bytes.

    :param data: The raw binary content of a confusion.bin file.
    :returns: A :data:`DistinguishingMaps` dictionary keyed by encoding pairs.
    """
    result: DistinguishingMaps = {}
    offset = 0
    (num_pairs,) = struct.unpack_from("!H", data, offset)
    offset += 2

    for _ in range(num_pairs):
        (name_a_len,) = struct.unpack_from("!B", data, offset)
        offset += 1
        name_a = data[offset : offset + name_a_len].decode("utf-8")
        offset += name_a_len

        (name_b_len,) = struct.unpack_from("!B", data, offset)
        offset += 1
        name_b = data[offset : offset + name_b_len].decode("utf-8")
        offset += name_b_len

        (num_diffs,) = struct.unpack_from("!B", data, offset)
        offset += 1

        diff_bytes_list: list[int] = []
        categories: dict[int, tuple[str, str]] = {}
        for _ in range(num_diffs):
            bv, cat_a_int, cat_b_int = struct.unpack_from("!BBB", data, offset)
            offset += 3
            diff_bytes_list.append(bv)
            categories[bv] = (
                _INT_TO_CATEGORY.get(cat_a_int, "Cn"),
                _INT_TO_CATEGORY.get(cat_b_int, "Cn"),
            )
        result[(name_a, name_b)] = (frozenset(diff_bytes_list), categories)

    return result


@functools.cache
def load_confusion_data() -> DistinguishingMaps:
    """Load confusion group data from the bundled confusion.bin file.

    :returns: A :data:`DistinguishingMaps` dictionary keyed by encoding pairs.
    """
    ref = importlib.resources.files("chardet.models").joinpath("confusion.bin")
    raw = ref.read_bytes()
    if not raw:
        warnings.warn(
            "chardet confusion.bin is empty — confusion resolution disabled; "
            "reinstall chardet to fix",
            RuntimeWarning,
            stacklevel=2,
        )
        return {}
    try:
        raw_maps = deserialize_confusion_data_from_bytes(raw)
    except (struct.error, UnicodeDecodeError) as e:
        msg = f"corrupt confusion.bin: {e}"
        raise ValueError(msg) from e
    # Normalize keys to canonical codec names so pipeline output matches.
    normalized: DistinguishingMaps = {}
    for (a, b), value in raw_maps.items():
        norm_a = lookup_encoding(a) or a
        norm_b = lookup_encoding(b) or b
        normalized[(norm_a, norm_b)] = value
    return normalized


# Unicode general category preference scores for voting resolution.
# Higher scores indicate more linguistically meaningful characters.
_CATEGORY_PREFERENCE: dict[str, int] = {
    "Lu": 10,
    "Ll": 10,
    "Lt": 10,
    "Lm": 9,
    "Lo": 9,
    "Nd": 8,
    "Nl": 7,
    "No": 7,
    "Pc": 6,
    "Pd": 6,
    "Ps": 6,
    "Pe": 6,
    "Pi": 6,
    "Pf": 6,
    "Po": 6,
    "Sc": 5,
    "Sm": 5,
    "Sk": 4,
    "So": 4,
    "Zs": 3,
    "Zl": 3,
    "Zp": 3,
    "Cf": 2,
    "Cc": 1,
    "Co": 1,
    "Cs": 0,
    "Cn": 0,
    "Mn": 5,
    "Mc": 5,
    "Me": 5,
}


def resolve_by_category_voting(
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
    categories: dict[int, tuple[str, str]],
) -> str | None:
    """Resolve between two encodings using Unicode category voting.

    For each distinguishing byte present in the data, compare the Unicode
    general category under each encoding. The encoding whose interpretation
    has the higher category preference score gets a vote. The encoding with
    more votes wins.

    :param data: The raw byte data to examine.
    :param enc_a: First encoding name.
    :param enc_b: Second encoding name.
    :param diff_bytes: Byte values where the two encodings differ.
    :param categories: Mapping of byte value to ``(cat_a, cat_b)`` Unicode
        general category pairs.
    :returns: The winning encoding name, or ``None`` if tied.
    """
    votes_a = 0
    votes_b = 0
    relevant = frozenset(data) & diff_bytes
    if not relevant:
        return None
    for bv in relevant:
        cat_a, cat_b = categories[bv]
        pref_a = _CATEGORY_PREFERENCE.get(cat_a, 0)
        pref_b = _CATEGORY_PREFERENCE.get(cat_b, 0)
        if pref_a > pref_b:
            votes_a += pref_a - pref_b
        elif pref_b > pref_a:
            votes_b += pref_b - pref_a
    if votes_a > votes_b:
        return enc_a
    if votes_b > votes_a:
        return enc_b
    return None


def _best_variant_score(
    profile: BigramProfile,
    index: dict[str, list[tuple[str | None, memoryview, str]]],
    enc: str,
) -> float:
    """Return the best bigram score across all language variants for *enc*."""
    variants = index.get(enc)
    if not variants:
        return 0.0
    return max(
        score_with_profile(profile, model, model_key)
        for _, model, model_key in variants
    )


def resolve_by_bigram_rescore(
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
) -> str | None:
    """Resolve between two encodings by re-scoring only distinguishing bigrams.

    Builds a focused bigram profile containing only bigrams where at least one
    byte is a distinguishing byte, then scores both encodings against their
    best language model.

    :param data: The raw byte data to examine.
    :param enc_a: First encoding name.
    :param enc_b: Second encoding name.
    :param diff_bytes: Byte values where the two encodings differ.
    :returns: The winning encoding name, or ``None`` if tied.
    """
    if len(data) < 2:
        return None

    idf = get_idf_weights()
    freq: dict[int, int] = {}
    for i in range(len(data) - 1):
        b1 = data[i]
        b2 = data[i + 1]
        if b1 not in diff_bytes and b2 not in diff_bytes:
            continue
        idx = (b1 << 8) | b2
        freq[idx] = freq.get(idx, 0) + idf[idx]

    if not freq:
        return None

    profile = BigramProfile.from_weighted_freq(freq)

    index = get_enc_index()
    best_a = _best_variant_score(profile, index, enc_a)
    best_b = _best_variant_score(profile, index, enc_b)

    if best_a > best_b:
        return enc_a
    if best_b > best_a:
        return enc_b
    return None


def _find_pair_key(
    maps: DistinguishingMaps,
    enc_a: str,
    enc_b: str,
) -> tuple[str, str] | None:
    """Find the canonical key for a pair of encodings in the confusion maps."""
    if (enc_a, enc_b) in maps:
        return (enc_a, enc_b)
    if (enc_b, enc_a) in maps:
        return (enc_b, enc_a)
    return None


# Maximum confidence gap from the top result for candidates beyond
# position 1 to participate in confusion resolution.
_CONFUSION_BAND = 0.005


def resolve_confusion_groups(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Resolve confusion between similar encodings in the top results.

    Checks the top result against each candidate within a confidence band.
    Always checks position 1 (preserving original top-2 behavior); for
    positions 2+ only checks within the band.  Uses bigram re-scoring
    with category voting as fallback.

    :param data: The raw byte data to examine.
    :param results: Detection results sorted by confidence descending.
    :returns: A reordered list of :class:`DetectionResult` with the winner first.
    """
    if len(results) < 2:
        return results

    top = results[0]
    if top.encoding is None:
        return results

    maps = load_confusion_data()
    top_conf = top.confidence

    for i in range(1, len(results)):
        candidate = results[i]
        if candidate.encoding is None:
            continue
        # Always check position 1 (original top-2 behavior).
        # For positions 2+, only check within the confidence band.
        if i > 1 and top_conf - candidate.confidence > _CONFUSION_BAND:
            break

        pair_key = _find_pair_key(maps, top.encoding, candidate.encoding)
        if pair_key is None:
            continue

        diff_bytes, categories = maps[pair_key]
        enc_a, enc_b = pair_key

        cat_winner = resolve_by_category_voting(
            data, enc_a, enc_b, diff_bytes, categories
        )
        bigram_winner = resolve_by_bigram_rescore(data, enc_a, enc_b, diff_bytes)
        winner = bigram_winner if bigram_winner is not None else cat_winner

        if winner is not None and winner == candidate.encoding:
            # Give the promoted candidate the top result's confidence so
            # the promotion survives any downstream confidence-based sort.
            promoted = DetectionResult(
                candidate.encoding,
                top.confidence,
                candidate.language,
                candidate.mime_type,
            )
            rest = [r for j, r in enumerate(results) if j != i]
            return [promoted, *rest]

    return results
