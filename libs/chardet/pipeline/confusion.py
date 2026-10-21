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
import unicodedata
import warnings

from chardet.models import (
    ART_LANGUAGE,
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

#: Inverse mapping for serialization.  Public because the build side
#: (``scripts/confusion_training.py``) must encode categories with the
#: exact map this module decodes them with.
CATEGORY_TO_INT: dict[str, int] = {v: k for k, v in _INT_TO_CATEGORY.items()}


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


# Preference assigned to a letter reading whose context makes it an
# implausible word member — below every punctuation and symbol category.
_IMPLAUSIBLE_LETTER_PREFERENCE = 2

# Vote margin at which category voting overrides the bigram rescore.  Two
# context-decisive occurrences (letter-vs-punctuation with the word-shape
# rule fired: 2 x (6 - 2)) clear it; a lone punctuation-vs-punctuation
# reading (margin 1) never does.  Raising this threshold is not safe: the
# EBCDIC record suite depends on a decisive margin of 12 (three
# occurrences) to hold off the rescore's max-over-variants bias.
_DECISIVE_VOTE_MARGIN = 8

# Minimum number of distinct demotion-earning occurrences for a vote to be
# decisive.  A single occurrence can reach margin 8 on its own (a
# plausible-letter reading at preference 10 against an implausible-letter
# reading demoted to 2), and one byte of context must never outrank the
# rescore's model evidence.
_DECISIVE_MIN_EVENTS = 2

# Cap on distinguishing-byte occurrences examined per pair.  Sparse by
# nature; the cap only bounds pathological inputs.
_MAX_VOTE_OCCURRENCES = 256

# Density at which the focused-profile scan stops paying off.  Below one
# distinguishing byte per this many input bytes, locating the hits with a
# C-level scan beats walking every byte in Python; above it, the set of
# start indices costs more than the straight loop it replaces.  Only 62 of
# 2,170 rescore calls over the test corpus are that dense.
_DENSE_HIT_DIVISOR = 4


@functools.cache
def _letter_case_table(encoding: str) -> bytes:
    """256-entry table: 0 = non-letter, 1 = uppercase letter, 2 = other letter.

    Combining marks count as letters: in decomposed text (Vietnamese under
    windows-1258) a base letter's neighbor is its diacritic, which is
    word-internal, not a word boundary.  Whitespace deliberately counts as
    a plain non-letter: exempting space-adjacent letters from the
    isolated-letter demotion (to spare one-letter words like French ``à``)
    was tried and falsified by the accuracy suite — Irish/Finnish po files
    and the EBCDIC record set depend on space-adjacent demotions, so the
    cross-family decisive-override gate handles the ``à`` failure mode
    instead.
    """
    table = bytearray(256)
    for b in range(256):
        try:
            ch = bytes([b]).decode(encoding)
        except UnicodeDecodeError:
            continue
        # Stateful codecs can decode a byte to zero characters (utf-7's
        # ``+`` opens a base64 run and yields ``""``), and category()
        # rejects anything but a single character.
        if len(ch) != 1:
            continue
        cat = unicodedata.category(ch)
        if cat == "Lu":
            table[b] = 1
        elif cat[0] == "L" or cat in ("Mn", "Mc"):
            table[b] = 2
    return bytes(table)


def _context_preference(cat: str, left: int, right: int, case_table: bytes) -> int:
    """Preference for reading a byte as *cat*, adjusted for word shape.

    A letter reading only deserves its high preference when its neighbors
    make it look like part of a word under the same encoding: a letter with
    no letter neighbors is quoted/isolated punctuation in disguise, and a
    lowercase letter immediately followed by an uppercase one is not a word
    shape any of the supported languages produce.
    """
    pref = _CATEGORY_PREFERENCE.get(cat, 0)
    if cat[0] != "L":
        return pref
    left_kind = case_table[left]
    right_kind = case_table[right]
    if left_kind == 0 and right_kind == 0:
        return _IMPLAUSIBLE_LETTER_PREFERENCE
    if cat == "Ll" and right_kind == 1:
        return _IMPLAUSIBLE_LETTER_PREFERENCE
    return pref


def _vote_with_margin(
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
    categories: dict[int, tuple[str, str]],
) -> tuple[str | None, int, int, int]:
    """Context-aware category voting.

    Returns ``(winner, margin, demotion_margin, demotion_events)``.

    For each occurrence of a distinguishing byte, compare the two
    encodings' readings: Unicode category preference, adjusted for word
    shape (see :func:`_context_preference`).  The reading that makes more
    linguistic sense of the byte *in its context* collects the vote;
    occurrences vote independently, so repeated evidence counts.

    ``demotion_margin`` counts only the winner's votes earned where the
    *losing* side's letter reading was word-shape-implausible — evidence
    against an impossible reading, which is far stronger than the naive
    letters-beat-symbols preference.  ``demotion_events`` counts how many
    distinct occurrences contributed to it, so callers can tell repeated
    evidence from one loud byte.
    """
    # Delete every non-distinguishing byte value in one C-level translate
    # pass; what survives is exactly the distinguishing bytes present.
    # Equivalent to ``frozenset(data) & diff_bytes`` but ~5x faster, since
    # that would hash every byte of the (up to max_bytes) input.
    non_diff, _ = _pair_byte_tables(diff_bytes)
    relevant = frozenset(data.translate(None, non_diff))
    if not relevant:
        return None, 0, 0, 0
    table_a = _letter_case_table(enc_a)
    table_b = _letter_case_table(enc_b)
    votes_a = 0
    votes_b = 0
    demotion_a = 0
    demotion_b = 0
    events_a = 0
    events_b = 0
    end = len(data) - 1
    for bv in relevant:
        cat_a, cat_b = categories[bv]
        needle = bytes((bv,))
        pos = data.find(needle)
        examined = 0
        while pos >= 0 and examined < _MAX_VOTE_OCCURRENCES:
            left = data[pos - 1] if pos > 0 else 0
            right = data[pos + 1] if pos < end else 0
            pref_a = _context_preference(cat_a, left, right, table_a)
            pref_b = _context_preference(cat_b, left, right, table_b)
            # A letter reading beating a *punctuation* reading on naive
            # preference alone is not evidence: punctuation of every
            # category legitimately borders letters (delimiters, hyphens,
            # brackets, apostrophes), so the letter interpretation is
            # never the only plausible one.  A letter beating a *symbol*
            # reading still counts — box-drawing or dingbats inside a
            # word is not a shape prose produces.
            if pref_a > pref_b:
                if cat_a[0] == "L" and cat_b[0] == "P":
                    pass
                else:
                    votes_a += pref_a - pref_b
                    if cat_b[0] == "L" and pref_b == _IMPLAUSIBLE_LETTER_PREFERENCE:
                        demotion_a += pref_a - pref_b
                        events_a += 1
            elif pref_b > pref_a:
                if cat_b[0] == "L" and cat_a[0] == "P":
                    pass
                else:
                    votes_b += pref_b - pref_a
                    if cat_a[0] == "L" and pref_a == _IMPLAUSIBLE_LETTER_PREFERENCE:
                        demotion_b += pref_b - pref_a
                        events_b += 1
            examined += 1
            pos = data.find(needle, pos + 1)
    if votes_a > votes_b:
        return enc_a, votes_a - votes_b, demotion_a, events_a
    if votes_b > votes_a:
        return enc_b, votes_b - votes_a, demotion_b, events_b
    return None, 0, 0, 0


def confusion_pair_winner(
    data: bytes,
    enc_x: str,
    enc_y: str,
    languages: frozenset[str] = frozenset(),
) -> str | None:
    """Return the byte-evidence winner between two encodings, or ``None``.

    Mirrors the in-band pairwise rule of :func:`resolve_confusion_groups`
    (decisive demotion vote, else bigram rescore, else category vote) for
    callers outside the ranked-results scan — e.g. the classic-Mac
    line-ending promotion, whose platform prior must not override
    distinguishing-byte evidence.  Returns ``None`` when the pair has no
    distinguishing map or the evidence is inconclusive.

    *languages* must carry what the two results being compared report, or
    the mirror breaks: the rescore would arbitrate the same pair under a
    different rule than the confusion stage just did, and a veto built on
    that answer can reverse a promotion the stage had settled.
    """
    maps = load_confusion_data()
    pair_key = _find_pair_key(maps, enc_x, enc_y)
    if pair_key is None:
        return None
    diff_bytes, categories = maps[pair_key]
    enc_a, enc_b = pair_key
    cat_winner, _margin, demotion_margin, demotion_events = _vote_with_margin(
        data, enc_a, enc_b, diff_bytes, categories
    )
    if (
        cat_winner is not None
        and demotion_margin >= _DECISIVE_VOTE_MARGIN
        and demotion_events >= _DECISIVE_MIN_EVENTS
        and len(diff_bytes) < _CROSS_FAMILY_MIN_DIFFS
    ):
        return cat_winner
    bigram_winner = resolve_by_bigram_rescore(data, enc_a, enc_b, diff_bytes, languages)
    if len(diff_bytes) >= _CROSS_FAMILY_MIN_DIFFS:
        # Cross-family pairs: corroboration required (see the strict rule
        # in resolve_confusion_groups).
        if bigram_winner is not None and bigram_winner == cat_winner:
            return bigram_winner
        return None
    return bigram_winner if bigram_winner is not None else cat_winner


def resolve_by_category_voting(
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
    categories: dict[int, tuple[str, str]],
) -> str | None:
    """Resolve between two encodings using context-aware category voting.

    :returns: The winning encoding name, or ``None`` if tied.
    """
    winner, _margin, _demotion, _events = _vote_with_margin(
        data, enc_a, enc_b, diff_bytes, categories
    )
    return winner


@functools.cache
def _pair_byte_tables(diff_bytes: frozenset[int]) -> tuple[bytes, bytes]:
    """Return ``(non_diff_delete, membership)`` byte tables for a pair.

    ``non_diff_delete`` holds every byte value *not* in *diff_bytes* (for
    ``bytes.translate`` deletion) and ``membership`` is a 256-entry table
    with 1 at each distinguishing byte (native indexing under mypyc, where
    frozenset probes are boxed).  Cached because *diff_bytes* comes from
    the fixed per-pair confusion maps loaded once per process.
    """
    member = bytearray(256)
    for b in diff_bytes:
        member[b] = 1
    non_diff = bytes(b for b in range(256) if not member[b])
    return non_diff, bytes(member)


#: Pseudo-language for models trained on data with no linguistic content
#: (ANSI art / box drawing).  Not a language, so language-fairness rules
#: do not apply to it.  Canonically defined beside the model tables.
_ART_LANGUAGE = ART_LANGUAGE


@functools.cache
def _modelled_languages(enc: str) -> frozenset[str]:
    """Languages *enc* has a bigram model for."""
    return frozenset(
        lang for lang, _, _ in get_enc_index().get(enc, []) if lang is not None
    )


def _comparable_languages(
    enc_a: str,
    enc_b: str,
    languages: frozenset[str],
) -> frozenset[str] | None:
    """Languages to score *enc_a* and *enc_b* under, or ``None`` for all.

    ``None`` means *unrestricted* — score every variant, the original
    max-over-models comparison.  It is not an abstention.

    An encoding should not win on language coverage the other side lacks.
    On a Hungarian document the u-double-acute bytes score 0.014 against
    iso8859-2's *Czech* model (which reads them as a common r-hacek) and
    only 0.006 against iso8859-16's Hungarian one, so max-over-variants
    hands Hungarian text to the Czech reading.  Dropping the languages
    only one side models removes that particular unfairness.

    This is deliberately a narrow rule, and two tempting generalisations
    were measured and rejected against the accuracy suite:

    * Restricting to *languages* themselves rather than the shared set
      costs 12 tests.  As a consequence the restriction is a no-op for
      pairs whose language coverage already matches (67 of the 236
      confusion pairs), which is accepted — those pairs have no coverage
      asymmetry to correct in the first place.
    * Restricting when *languages* is not wholly inside the shared set
      costs 6 tests: cp1125 models only Ukrainian, so a Belarusian cp866
      document shares just ``uk`` with it, and scoring the *right*
      encoding under the *wrong* language loses to cp1125.  Falling back
      to unrestricted is also what keeps a Vietnamese windows-1258
      document, whose rival cp1252 models no Vietnamese, resolving
      correctly.  The cost is that pairs modelling disjoint languages
      (koi8-r/koi8-u, mac-roman/mac-turkish) never restrict at all —
      about 20% of calls over the corpus.
    """
    if not languages:
        return None
    langs_a = _modelled_languages(enc_a)
    langs_b = _modelled_languages(enc_b)
    shared = langs_a & langs_b
    if not languages <= shared:
        return None
    # The art pseudo-language is not a language, so the fairness argument
    # above does not reach it: cp437 is the only encoding carrying a zxx
    # model, which means a plain intersection would strip box-drawing
    # evidence from every restricted rescore it takes part in.  Keeping it
    # for whichever side has it preserves the art protection the module
    # maintains elsewhere (see the zxx guard in resolve_confusion_groups).
    if _ART_LANGUAGE in langs_a or _ART_LANGUAGE in langs_b:
        return shared | {_ART_LANGUAGE}
    return shared


def _best_variant_score(
    profile: BigramProfile,
    index: dict[str, list[tuple[str | None, bytes, str]]],
    enc: str,
    languages: frozenset[str] | None,
) -> float:
    """Return the best bigram score for *enc*, restricted to *languages*.

    *languages* of ``None`` means every variant, the unrestricted
    max-over-models comparison.  The ``default`` guards a caller-supplied
    set that names no variant of *enc*; note that scoring 0.0 hands the
    comparison to the rival rather than abstaining, so callers wanting an
    abstention must not rely on it.
    """
    variants = index.get(enc)
    if not variants:
        return 0.0
    return max(
        (
            score_with_profile(profile, model, model_key)
            for lang, model, model_key in variants
            if languages is None or lang in languages
        ),
        default=0.0,
    )


def build_focused_profile(
    data: bytes, diff_bytes: frozenset[int]
) -> BigramProfile | None:
    """Build the bigram profile of *data* restricted to *diff_bytes* context.

    The profile holds only bigrams where at least one byte is in
    *diff_bytes*, weighted by IDF like the full-input profile, so scoring a
    model against it asks how well that model explains the bytes two
    encodings read differently, and nothing else.  Returns ``None`` when
    *data* cannot form a bigram or contains no distinguishing byte.

    :param data: The raw byte data to examine.
    :param diff_bytes: Byte values where the two encodings differ.
    """
    if len(data) < 2:
        return None

    # C-level prefilter: if no distinguishing byte occurs anywhere, the
    # focused profile below would be empty — skip the per-byte loop.
    # Deleting the *non*-distinguishing bytes leaves a result that is tiny
    # (usually empty) rather than a near-full copy of the input.
    non_diff, is_diff = _pair_byte_tables(diff_bytes)
    hits = len(data.translate(None, non_diff))
    if not hits:
        return None

    idf = get_idf_weights()
    freq: dict[int, int] = {}
    limit = len(data) - 1
    if hits * _DENSE_HIT_DIVISOR < len(data):
        # Sparse case, which is nearly all of them: locate the hits with
        # bytes.find rather than walking every byte.  Each hit at position
        # p belongs to the bigrams starting at p-1 and p; collecting start
        # indices counts a bigram whose bytes are both distinguishing once,
        # exactly as the dense scan below does.
        starts: set[int] = set()
        for bv in frozenset(data.translate(None, non_diff)):
            needle = bytes((bv,))
            pos = data.find(needle)
            while pos >= 0:
                if pos:
                    starts.add(pos - 1)
                if pos < limit:
                    starts.add(pos)
                pos = data.find(needle, pos + 1)
        for i in starts:
            idx = (data[i] << 8) | data[i + 1]
            freq[idx] = freq.get(idx, 0) + idf[idx]
    else:
        for i in range(limit):
            b1 = data[i]
            b2 = data[i + 1]
            if not (is_diff[b1] | is_diff[b2]):
                continue
            idx = (b1 << 8) | b2
            freq[idx] = freq.get(idx, 0) + idf[idx]

    # Unreachable: the hit prefilter above already returned when no
    # distinguishing byte occurs, and with len(data) >= 2 every hit byte
    # belongs to at least one bigram, so both scan paths put a key in
    # ``freq`` (a zero IDF weight still creates the key).  Kept so a future
    # scan-path change cannot hand an empty profile to the scorer.
    if not freq:  # pragma: no cover
        return None

    return BigramProfile.from_weighted_freq(freq)


def resolve_by_bigram_rescore(
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
    languages: frozenset[str] = frozenset(),
) -> str | None:
    """Resolve between two encodings by re-scoring only distinguishing bigrams.

    Builds a focused bigram profile containing only bigrams where at least one
    byte is a distinguishing byte, then scores both encodings under the
    languages they can be compared in (see :func:`_comparable_languages`).

    There is no abstention path here: when the pair has no comparable
    language the comparison widens to every variant rather than declining
    to answer.  That is why a Danish mac-roman/mac-turkish document, whose
    pair models disjoint languages, is still decided by the Turkish model
    the rescore has no business consulting — the caller's category vote is
    better placed on such evidence, and overriding this to abstain was
    measured as costing more accuracy than it recovers.

    :param data: The raw byte data to examine.
    :param enc_a: First encoding name.
    :param enc_b: Second encoding name.
    :param diff_bytes: Byte values where the two encodings differ.
    :param languages: Languages the ranked results report for this pair;
        empty when the caller has no ranking to draw on, which scores
        every variant.
    :returns: The winning encoding name, or ``None`` if tied or if no
        distinguishing byte occurs in *data*.
    """
    profile = build_focused_profile(data, diff_bytes)
    if profile is None:
        return None

    comparable = _comparable_languages(enc_a, enc_b, languages)

    index = get_enc_index()
    best_a = _best_variant_score(profile, index, enc_a, comparable)
    best_b = _best_variant_score(profile, index, enc_b, comparable)

    if best_a > best_b:
        return enc_a
    if best_b > best_a:
        return enc_b
    return None


@functools.cache
def differing_high_bytes(enc_a: str, enc_b: str) -> frozenset[int]:
    """Byte values >= 0x80 that *enc_a* and *enc_b* decode to different text.

    The distinguishing set for a pair the confusion maps do not cover,
    computed from the codecs themselves.  A byte only one side can decode
    counts as differing.  Bytes below 0x80 are left out: the callers ask
    about high-byte evidence, and every single-byte Latin family agrees
    on ASCII anyway.
    """
    out: set[int] = set()
    for b in range(0x80, 0x100):
        raw = bytes((b,))
        try:
            text_a: str | None = raw.decode(enc_a)
        except UnicodeDecodeError:
            text_a = None
        try:
            text_b: str | None = raw.decode(enc_b)
        except UnicodeDecodeError:
            text_b = None
        if text_a != text_b:
            out.add(b)
    return frozenset(out)


@functools.cache
def _pair_categories(
    enc_a: str, enc_b: str, diff_bytes: frozenset[int]
) -> dict[int, tuple[str, str]]:
    """Unicode general categories of each distinguishing byte under both encodings.

    The confusion maps carry this table for their own pairs; callers that
    arbitrate a pair the maps do not cover (the niche-Latin demotion's
    candidate against its swap target) build it here.  A byte one side
    cannot decode reads as unassigned (``Cn``), which the vote treats as
    the least plausible reading of all.
    """
    table: dict[int, tuple[str, str]] = {}
    for b in diff_bytes:
        cats = []
        for enc in (enc_a, enc_b):
            try:
                ch = bytes([b]).decode(enc)
            except UnicodeDecodeError:
                cats.append("Cn")
                continue
            cats.append(unicodedata.category(ch) if len(ch) == 1 else "Cn")
        table[b] = (cats[0], cats[1])
    return table


def arbitrate_distinguishing_bytes(  # noqa: PLR0913
    data: bytes,
    enc_a: str,
    enc_b: str,
    diff_bytes: frozenset[int],
    *,
    languages_a: frozenset[str] | None,
    languages_b: frozenset[str] | None,
) -> str | None:
    """Decide a pair on its distinguishing bytes: model rescore, then context.

    The in-band rule of :func:`resolve_confusion_groups` for a pair the
    confusion maps do not cover, with one difference: each side is scored
    under the languages the caller names for it rather than the shared
    set.  The bigram rescore decides when the models have an opinion; when
    they score the distinguishing bigrams equally (usually both at zero,
    a byte neither model has seen in that context), the category vote
    reads word shape instead, so a letter between letters still beats a
    superscript between letters.  Returns ``None`` when neither step can
    tell the two apart.

    :param data: The raw byte data to examine.
    :param enc_a: First encoding name.
    :param enc_b: Second encoding name.
    :param diff_bytes: Byte values where the two encodings differ.
    :param languages_a: Variants of *enc_a* to score; ``None`` for all.
    :param languages_b: Variants of *enc_b* to score; ``None`` for all.
    """
    profile = build_focused_profile(data, diff_bytes)
    if profile is not None:
        index = get_enc_index()
        best_a = _best_variant_score(profile, index, enc_a, languages_a)
        best_b = _best_variant_score(profile, index, enc_b, languages_b)
        if best_a > best_b:
            return enc_a
        if best_b > best_a:
            return enc_b
    winner, _margin, _demotion, _events = _vote_with_margin(
        data, enc_a, enc_b, diff_bytes, _pair_categories(enc_a, enc_b, diff_bytes)
    )
    return winner


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


# Pairs whose distinguishing set is at least this large come from the
# cross-family tier of the pair generator (byte-similar siblings differ at
# most at 51 positions under its 0.80 similarity floor).  Cross-family
# pairs arbitrate wholesale-different byte tables, where the rescore alone
# is a coin flip whenever the distinguishing evidence in the data is
# sparse — so these pairs require vote/rescore corroboration even for
# in-band near-ties.
_CROSS_FAMILY_MIN_DIFFS = 52

#: Maximum confidence gap from the top result for candidates beyond
#: position 1 to participate in confusion resolution.  Public because it
#: is a contract fact: the pruning contract in
#: :mod:`chardet.pipeline.postprocess` composes it into the floor that
#: statistical pruning must score exactly.
CONFUSION_BAND = 0.005

#: Minimum confidence, as a fraction of the top result's, for out-of-band
#: candidates to participate in the strict tier of confusion resolution.
#: Confusion siblings can score far apart in absolute terms while the
#: statistical ranking among them is still noise (EBCDIC record data), so
#: the strict tier extends beyond the band — but only for challengers with
#: corroborated evidence (vote and bigram agreement, or a decisive
#: demotion-driven vote).  Public: a contract fact, see
#: :data:`CONFUSION_BAND`.
CONFUSION_FLOOR_RATIO = 0.5

#: The strict tier only opens when the top confidence is below this value.
#: A low absolute confidence means no model explains the data, so the
#: ranking among confusion siblings is noise and corroborated byte-level
#: evidence may overturn it.  A confident top means the statistics are
#: working; overriding them from far down the ranking does more harm than
#: good (correlated vote/rescore errors across the many near-scoring
#: Latin encodings).  Public: a contract fact, see :data:`CONFUSION_BAND`.
STRICT_TIER_MAX_CONF = 0.2


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
    # An art-model win (the zxx pseudo-language: no linguistic content) is
    # not up for linguistic-plausibility review — voting and rescoring both
    # reason about prose, which box-drawing data is not.  Narrowing this to
    # rescore-only review was tried and rejected: under era filtering a
    # prose sibling can tie the art model exactly (cp850-en vs cp437-zxx on
    # a real artpack file) and the flickery diff-focused rescore then
    # dethrones genuine art, while the case the review would rescue —
    # box-drawing strong enough to outrank dominant prose statistically,
    # yet weaker than it in the diff-byte rescore — is a knife-edge regime
    # the statistical ranking already resolves whenever prose dominates.
    if top.language == _ART_LANGUAGE:
        return results

    maps = load_confusion_data()
    top_conf = top.confidence
    floor = top_conf * CONFUSION_FLOOR_RATIO

    champion_idx = 0
    champion = top
    # Tracked alongside ``champion`` as a narrowed ``str``.  Rebinding
    # ``champion`` on promotion widens ``.encoding`` back to ``str | None``
    # for the type checker, and both values it can hold — ``top`` and a
    # promoted ``candidate`` — are None-checked before they get here.
    champion_enc = top.encoding
    for i in range(1, len(results)):
        candidate = results[i]
        if candidate.encoding is None:
            continue
        # Position 1 and band members use the original in-band rules;
        # candidates between the band and the floor enter the strict tier,
        # which only opens when the statistics have failed outright.
        in_band = i == 1 or top_conf - candidate.confidence <= CONFUSION_BAND
        if not in_band and (
            top_conf >= STRICT_TIER_MAX_CONF or candidate.confidence < floor
        ):
            break

        pair_key = _find_pair_key(maps, champion_enc, candidate.encoding)
        if pair_key is None:
            continue

        diff_bytes, categories = maps[pair_key]
        enc_a, enc_b = pair_key

        cat_winner, _vote_margin, demotion_margin, demotion_events = _vote_with_margin(
            data, enc_a, enc_b, diff_bytes, categories
        )
        # A demotion-driven vote outranks the bigram rescore: those votes
        # were earned where the opposing reading was a word-shape-impossible
        # letter (lowercase jammed between digits or capitals), which is
        # stronger evidence than the rescore's prose-typicality priors.  A
        # vote won on the naive letters-beat-symbols preference defers
        # to the rescore's model evidence.  Decisiveness requires repeated
        # evidence: one occurrence can reach the margin on its own, and a
        # single byte of context must never outrank the models.
        winner: str | None
        # The decisive-demotion override exists because *sibling* models
        # are too similar for the rescore to arbitrate — a premise that
        # only holds within-family.  Cross-family models differ wholesale,
        # so there the rescore is at its most informative and the vote's
        # linguistic priors at their least reliable (a French ``à`` read
        # as a footnote dagger collects huge demotion margins): cross-
        # family pairs always require corroboration instead.
        if (
            cat_winner is not None
            and demotion_margin >= _DECISIVE_VOTE_MARGIN
            and demotion_events >= _DECISIVE_MIN_EVENTS
            and len(diff_bytes) < _CROSS_FAMILY_MIN_DIFFS
        ):
            winner = cat_winner
        else:
            # When both results read the document as the same language,
            # the rescore compares them in it rather than under whichever
            # language happens to like the distinguishing bytes most.
            langs = frozenset(
                lang
                for lang in (champion.language, candidate.language)
                if lang is not None
            )
            bigram_winner = resolve_by_bigram_rescore(
                data, enc_a, enc_b, diff_bytes, langs
            )
            if in_band and len(diff_bytes) < _CROSS_FAMILY_MIN_DIFFS:
                winner = bigram_winner if bigram_winner is not None else cat_winner
            # Strict rule (out-of-band candidates, and cross-family pairs
            # even in-band): overturning the ranking needs corroboration —
            # the vote and the rescore must agree.  (The decisive-demotion
            # case is handled above.)
            elif bigram_winner is not None and bigram_winner == cat_winner:
                winner = bigram_winner
            else:
                winner = None

        if winner is None or winner != candidate.encoding:
            continue
        if in_band:
            # In-band promotion: trust it and stop, preserving the
            # original single-promotion behavior for near-ties.
            promoted = DetectionResult(
                candidate.encoding,
                top_conf,
                candidate.language,
                candidate.mime_type,
            )
            rest = [r for j, r in enumerate(results) if j != i]
            return [promoted, *rest]
        # Strict-tier promotion: the new champion must defend against
        # the remaining candidates (king-of-the-hill), because the
        # correct member of a clique may rank below another sibling
        # that also beats the current champion.  Known limitation: the
        # scan is single-pass, so a higher-ranked candidate skipped
        # earlier for lack of a pair with the then-champion is never
        # revisited against the new one — accepted, since the original
        # top-anchored code could not arbitrate those either.
        champion_idx = i
        champion = candidate
        champion_enc = candidate.encoding

    if champion_idx == 0:
        return results

    # Give the promoted candidate the top result's confidence so the
    # promotion survives any downstream confidence-based sort.
    promoted = DetectionResult(
        champion.encoding,
        top_conf,
        champion.language,
        champion.mime_type,
    )
    rest = [r for j, r in enumerate(results) if j != champion_idx]
    return [promoted, *rest]
