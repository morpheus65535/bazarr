"""Stage 13: post-processing rank corrections.

After statistical scoring produces a ranked list of candidates, a chain
of rank corrections fixes up the ranking when bigrams alone are
insufficient — see :func:`postprocess_results` for the order.  The steps:
dead-heat priors (superset preference, era prevalence), rare-language
arbitration (ADR-0005), confusion-group resolution (delegated to
:mod:`chardet.pipeline.confusion`), niche Latin demotion, KOI8-T
promotion, classic-Mac line-ending promotion, and last of all the
decode-safety flip, which hands a winner whose only multi-byte evidence
is an undecodable trailing sequence to the best rival that can decode
the caller's complete input.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet._utils import (
    dangling_tail_with_ascii_prefix,
    decodes_completely,
    decodes_without_error,
)
from chardet.models import ART_LANGUAGE, RARE_LANGUAGES, get_enc_index
from chardet.output_names import _COMPAT_NAMES
from chardet.pipeline import DetectionResult
from chardet.pipeline.confusion import (
    CONFUSION_BAND,
    CONFUSION_FLOOR_RATIO,
    STRICT_TIER_MAX_CONF,
    _comparable_languages,
    arbitrate_distinguishing_bytes,
    confusion_pair_winner,
    differing_high_bytes,
    resolve_confusion_groups,
)
from chardet.registry import REGISTRY

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

# Encodings that are often false positives when their distinguishing bytes
# are absent.  Keyed by encoding name -> frozenset of byte values where
# that encoding differs from iso-8859-1 (or windows-1252 in the case of
# windows-1254).
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


# Deletion tables for bytes.translate: length changes iff a distinguishing
# byte occurs in the data.  A translate scan runs at C speed where the
# equivalent generator expression iterates the whole (up to max_bytes) input
# with boxed set-membership tests.  All distinguishing bytes are > 0x7F, so
# the old per-byte high-bit filter is subsumed by set membership.
_DEMOTION_DELETE: dict[str, bytes] = {
    enc: bytes(byte_set) for enc, byte_set in _DEMOTION_CANDIDATES.items()
}
_KOI8_T_DELETE: bytes = bytes(_KOI8_T_DISTINGUISHING)


def _should_demote(data: bytes, top: DetectionResult, target: DetectionResult) -> bool:
    """Return True if *top*, a demotion candidate, has no byte evidence over *target*.

    Callers guarantee ``top.encoding`` is in :data:`_DEMOTION_CANDIDATES`.
    Two questions, cheapest first.  Does *data* contain any byte the
    candidate decodes differently from ISO-8859-1?  If not, the data is
    equally valid under both encodings, nothing at the byte level favors
    the candidate, and it is demoted.

    If such bytes are present, do they favor the candidate?  Presence
    alone is symmetric evidence: a Windows-1252 file whose only non-ASCII
    letter is an ``Ö`` carries 0xD6, which HP-Roman8 reads as ``ø``, so
    both candidates "contain" the byte and the question is which reading
    holds up.  That is a confusion-style arbitration between the candidate
    and its swap target on the distinguishing bytes alone (see
    :func:`~chardet.pipeline.confusion.arbitrate_distinguishing_bytes`),
    each side scored under the variant that actually won its slot.  The
    models decide when they can: one Welsh ``ŵ`` keeps ISO-8859-14 because
    the Welsh model knows that bigram and the Windows-1252 reading is a
    ``ð`` no Welsh model has seen.  When the models are silent, word shape
    decides: a Kven ``đ`` keeps a Finnish file on ISO-8859-10 because a
    letter between letters beats the superscript ``¹`` Windows-1252 reads
    there.  A lone ``Ö`` mid-word decides nothing either way, and the more
    prevalent encoding takes the evidence-free tie.

    The arbitration is only asked when the candidate's lead over the swap
    target is within :data:`~chardet.pipeline.confusion.CONFUSION_BAND`.
    A win by more than the band was decided on the full statistics, and
    re-litigating it on a handful of bytes is neither sound nor free: the
    scan is Python level, and mainstream Turkish text tops as windows-1254
    with hundreds of distinguishing bytes and a lead of 0.2.
    """
    encoding = top.encoding or ""
    if len(data.translate(None, _DEMOTION_DELETE[encoding])) == len(data):
        return True
    if top.confidence - target.confidence > CONFUSION_BAND:
        return False
    winner = arbitrate_distinguishing_bytes(
        data,
        encoding,
        target.encoding or "",
        _DEMOTION_CANDIDATES[encoding],
        languages_a=None if top.language is None else frozenset((top.language,)),
        languages_b=None if target.language is None else frozenset((target.language,)),
    )
    return winner != encoding


def _swap_target(candidates: list[DetectionResult]) -> DetectionResult:
    """Pick the common Latin candidate that replaces a demoted top.

    Among the candidates within :data:`_DEAD_HEAT_EPSILON` of the
    highest-scoring one, era prevalence chooses (windows-1252 over
    iso-8859-1): inside that band the confidence order is noise, the very
    premise of the demotion.  A candidate trailing the best common Latin
    by more than the epsilon lost to it on real evidence and stays put.
    Equal era ranks (iso-8859-1 against iso-8859-15, both legacy ISO) keep
    confidence order, since ``min`` returns the first of equals and the
    candidates arrive ranked.
    """
    lead_conf = max(r.confidence for r in candidates)
    in_band = [r for r in candidates if lead_conf - r.confidence <= _DEAD_HEAT_EPSILON]
    return min(in_band, key=lambda r: _era_rank(r.encoding or ""))


def _demote_niche_latin(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Demote a niche Latin top that its distinguishing bytes do not support.

    Some bigram models (iso-8859-10, iso-8859-14, windows-1254, hp-roman8)
    can win on data that contains only bytes shared with the common Western
    Latin encodings, or on a lone shared byte the models cannot arbitrate.
    When :func:`_should_demote` finds no byte-level evidence for the
    winning encoding, promote the swap target :func:`_swap_target` picks
    among the common Latin candidates and push the demoted encoding to
    last.

    The demoted entries take the confidence of the candidate they now sit
    behind.  Rank position alone does not survive the trip out to callers:
    ``detect_all`` re-sorts by confidence, and a stable sort hands an entry
    that kept the top score its old place back.

    :param data: The raw byte data the results were produced from.
    :param results: A list of :class:`DetectionResult` ranked by confidence.
    :returns: A new list (or the same list) with the demotion applied.
    """
    if len(results) < 2 or results[0].encoding not in _DEMOTION_CANDIDATES:
        return results
    candidates = [r for r in results[1:] if r.encoding in _COMMON_LATIN_ENCODINGS]
    if not candidates:
        return results
    target = _swap_target(candidates)
    if not _should_demote(data, results[0], target):
        return results
    demoted_encoding = results[0].encoding
    top_conf = results[0].confidence
    promoted = DetectionResult(
        target.encoding, top_conf, target.language, target.mime_type
    )
    others = [x for x in results if x.encoding != demoted_encoding and x is not target]
    tail_conf = others[-1].confidence if others else top_conf
    demoted_entries = [
        DetectionResult(
            x.encoding,
            min(x.confidence, tail_conf),
            x.language,
            x.mime_type,
        )
        for x in results
        if x.encoding == demoted_encoding
    ]
    return [promoted, *others, *demoted_entries]


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
    if len(data.translate(None, _KOI8_T_DELETE)) != len(data):
        return _promote_to_top(results, koi8t_idx)
    return results


# Confidence gap below which two candidates are a statistical dead heat:
# their scores differ only through model-norm noise on bigrams that carry no
# real evidence (observed dead heats sit within ~1e-5; genuinely decided
# rankings lead by >= 2e-3).
_DEAD_HEAT_EPSILON = 1e-4

# On a dead heat between an encoding and its Windows superset, prefer the
# superset: it decodes everything the base encoding does, so it is never a
# worse answer when the statistics cannot separate them.  Mirrors
# ``markup._MARKUP_SUPERSET_PROMOTIONS``.
_DEAD_HEAT_SUPERSETS: dict[str, str] = {
    "shift_jis": "cp932",
    "shift_jis_2004": "cp932",
    "euc_kr": "cp949",
}

# Confidence band for the classic-Mac line-ending promotion.  Wider than the
# dead-heat epsilon because bare-\r line endings are decisive platform
# evidence, not just a prior.  Structurally the confusion band: retuning
# ``CONFUSION_BAND`` carries this promotion's reach with it, keeping the
# band inside ``_CORRECTION_REACH`` so pruning always scores what it scans.
_CR_MAC_BAND = CONFUSION_BAND

# Minimum number of \r line endings before the classic-Mac promotion fires.
_CR_MAC_MIN_LINES = 3

# EncodingEra.LEGACY_MAC — value inlined to avoid importing the enum into
# this mypyc-compiled hot path for a single constant.
_LEGACY_MAC_ERA = 4


# Cap on the data scanned for high-byte bigram evidence — matches the
# window statistical scoring uses (``orchestrator._STAT_SCORE_MAX_BYTES``),
# so the evidence check sees the same bytes the scores were computed from.
_EVIDENCE_SCAN_MAX_BYTES = 16384


def _era_rank(encoding: str) -> int:
    """Return the lowest era bit for *encoding* (lower = more prevalent today)."""
    info = REGISTRY.get(encoding)
    if info is None:
        return 1 << 30
    era = int(info.era)
    return era & -era


def _has_high_byte_evidence(data: bytes, encoding: str, language: "str | None") -> bool:
    """Return True if *encoding*'s winning model weights a high-byte bigram present in *data*.

    A candidate whose model assigns zero weight to every non-ASCII bigram in
    the data earned its statistical score purely from ASCII bigrams — noise
    that cannot distinguish encodings.  Only the variant that actually won
    (*language*) counts: another language's variant having weight for those
    bytes says nothing about why *this* result is on top.  Only called on
    dead heats, so the Python-level scan of the (capped) data is off the
    hot path.
    """
    variants = get_enc_index().get(encoding)
    if not variants:
        return False
    window = data[:_EVIDENCE_SCAN_MAX_BYTES]
    seen: set[int] = set()
    prev = window[0]
    for i in range(1, len(window)):
        b = window[i]
        if prev >= 0x80 or b >= 0x80:
            seen.add((prev << 8) | b)
        prev = b
    if not seen:
        return False
    for lang, table, _key in variants:
        if language is not None and lang != language:
            continue
        for idx in seen:
            if table[idx]:
                return True
    return False


def _prefer_prevalent_on_dead_heat(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Break statistical dead heats in favor of the more prevalent era.

    When several encodings score within :data:`_DEAD_HEAT_EPSILON` of the
    top result, the ranking among them is mostly an artifact of
    ASCII-bigram noise.  Promote the candidate from the most prevalent era
    (modern web > legacy ISO > Mac > regional > DOS > mainframe) so
    evidence-free dead heats resolve to the likeliest real-world answer.

    A top result whose models carry no weight for any high-byte bigram in
    the data has no evidence at all and yields outright.  One whose models
    do weight an observed bigram is not thereby safe: an English file with
    one capital ``É`` ranks MacRoman first because the MacRoman model
    reads 0xC9 as the ellipsis English text is full of, a lead worth
    2e-5.  Such a top is arbitrated against the prevalent candidate on the
    bytes the two read differently, under the languages the two can be
    compared in (see :func:`~chardet.pipeline.confusion.arbitrate_distinguishing_bytes`
    and confusion's ``_comparable_languages``): the Windows-1252 French
    model knows ``École`` even when the English one does not, while its
    Icelandic model may not read a Welsh ``dŵr`` as ``dðr`` against an
    encoding that models no Icelandic.  The prevalent candidate is
    promoted only when it wins outright; a tie keeps the top, so an
    ISO-8859-1 result tied with Windows-1252 on data without C1 bytes
    stays where the statistics put it.  Genuine MacRoman text never
    reaches the arbitration, since its hundreds of distinguishing bytes
    put Windows-1252 far outside the band.
    """
    top = results[0] if results else None
    if top is None or top.encoding is None or len(results) < 2:
        return results
    best_idx = 0
    best_rank = _era_rank(top.encoding)
    for i in range(1, len(results)):
        r = results[i]
        if r.encoding is None:
            continue
        if top.confidence - r.confidence > _DEAD_HEAT_EPSILON:
            break
        rank = _era_rank(r.encoding)
        if rank < best_rank:
            best_rank = rank
            best_idx = i
    if best_idx == 0:
        return results
    if not _has_high_byte_evidence(data, top.encoding, top.language):
        return _promote_to_top(results, best_idx)
    rival = results[best_idx].encoding or ""
    comparable = _comparable_languages(
        top.encoding,
        rival,
        frozenset(
            lang
            for lang in (top.language, results[best_idx].language)
            if lang is not None
        ),
    )
    winner = arbitrate_distinguishing_bytes(
        data,
        top.encoding,
        rival,
        differing_high_bytes(top.encoding, rival),
        languages_a=comparable,
        languages_b=comparable,
    )
    if winner == rival:
        return _promote_to_top(results, best_idx)
    return results


def _promote_to_top(results: list[DetectionResult], i: int) -> list[DetectionResult]:
    """Move ``results[i]`` to the top, carrying the current top confidence."""
    r = results[i]
    promoted = DetectionResult(
        r.encoding, results[0].confidence, r.language, r.mime_type
    )
    rest = [x for j, x in enumerate(results) if j != i]
    return [promoted, *rest]


def _promote_superset_on_dead_heat(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Promote a Windows superset over its base encoding on a dead heat."""
    top = results[0] if results else None
    if top is None or top.encoding is None or len(results) < 2:
        return results
    superset = _DEAD_HEAT_SUPERSETS.get(top.encoding)
    if superset is None:
        return results
    for i in range(1, len(results)):
        r = results[i]
        if top.confidence - r.confidence > _DEAD_HEAT_EPSILON:
            break
        if r.encoding == superset and decodes_without_error(data, superset):
            return _promote_to_top(results, i)
    return results


# Languages whose (language, encoding) variants never accumulated a
# measurable legacy document population.  Not a judgment about the
# languages — a graded prior about legacy-era *bytes*: iso8859-14 (Latin-8,
# the Celtic code page) was standardized in 1998 but Celtic text lived in
# latin-1 and moved to UTF-8; this project's wild-page mining has found no
# native specimen, and web surveys place the encoding at noise level.  The
# one documented genuine niche — Irish gettext .po catalogues that declare
# ISO-8859-14 (Scannell's vim/gettext translations, in the test suite) —
# measures safely outside the arbitration gate: genuine Celtic text has no
# prevalent-language rival anywhere near it.  Revision protocol per
# ADR-0005: any new genuine specimen goes into test-data and forces a
# re-audit of the set.  The set itself is :data:`chardet.models.RARE_LANGUAGES`
# — one definition, used by this gate and by the language fill's thin-margin
# band, so the two can never drift apart.  Membership changes happen there.

# Maximum lead over the best prevalent-language candidate for a
# rare-language winner to count as a coin flip rather than evidence.
_RARE_ARBITRATION_MARGIN = 0.02

# Maximum absolute confidence for arbitration to apply: genuine
# rare-language text scores well above this even when short, so the gate
# only opens in the evidence-free zone.
_RARE_ARBITRATION_MAX_CONFIDENCE = 0.15


def _arbitrate_rare_language(
    results: list[DetectionResult],
) -> list[DetectionResult]:
    """Demote a rare-language winner that leads a prevalent rival by a coin flip.

    Fires only when the winner's language is in
    :data:`~chardet.models.RARE_LANGUAGES`, its absolute confidence is
    inside the evidence-free zone, and a prevalent-language candidate sits
    within :data:`_RARE_ARBITRATION_MARGIN`.  Genuine rare-language text fails
    both gates: even short files score confidently, and their entire
    neighborhood is same-language variants.
    """
    top = results[0] if results else None
    if (
        top is None
        or top.encoding is None
        or top.language not in RARE_LANGUAGES
        or top.confidence >= _RARE_ARBITRATION_MAX_CONFIDENCE
        or len(results) < 2
    ):
        return results
    for i in range(1, len(results)):
        r = results[i]
        if top.confidence - r.confidence > _RARE_ARBITRATION_MARGIN:
            break
        if r.encoding is None or r.language is None:
            continue
        if r.language not in RARE_LANGUAGES:
            return _promote_to_top(results, i)
    return results


def _promote_mac_on_cr_line_endings(
    data: bytes,
    results: list[DetectionResult],
) -> list[DetectionResult]:
    r"""Promote a classic-Mac candidate when line endings are bare ``\r``.

    Classic Mac OS is the only platform that terminated lines with a lone
    carriage return, so data with several ``\r`` bytes and no ``\n`` is
    near-certainly Mac-era text.  When a LEGACY_MAC candidate scores within
    :data:`_CR_MAC_BAND` of a non-Mac top result, promote it — unless the
    pair has a distinguishing-byte map and the byte-level evidence says the
    current top wins: a platform prior must not overturn direct evidence
    that confusion resolution may have just used to establish the top.
    """
    top = results[0] if results else None
    if top is None or top.encoding is None or len(results) < 2:
        return results
    if _era_rank(top.encoding) == _LEGACY_MAC_ERA:
        return results
    # An art-model win is not up for prose-based review: the pairwise
    # veto below reasons about word shapes and prose bigrams, which
    # box-drawing data is not, and old ANSI art legitimately carries
    # bare-CR line endings.
    if top.language == ART_LANGUAGE:
        return results
    if data.find(b"\n") >= 0 or data.count(b"\r") < _CR_MAC_MIN_LINES:
        return results
    for i in range(1, len(results)):
        r = results[i]
        if top.confidence - r.confidence > _CR_MAC_BAND:
            break
        if r.encoding is not None and _era_rank(r.encoding) == _LEGACY_MAC_ERA:
            # Pass both languages so the veto arbitrates this pair under
            # the same rule confusion resolution just applied to it.
            langs = frozenset(
                lang for lang in (top.language, r.language) if lang is not None
            )
            if (
                confusion_pair_winner(data, top.encoding, r.encoding, langs)
                == top.encoding
            ):
                # Byte-level evidence says the top beats the best-ranked
                # Mac candidate: stop entirely rather than letting a
                # lower-ranked sibling take the promotion just because it
                # has no distinguishing-byte map to be checked against.
                break
            return _promote_to_top(results, i)
    return results


def _decodes_under_public_names(data: bytes, encoding: str) -> bool:
    """Check that *data* decodes completely under *encoding* and its output name.

    The flip's promise is that the caller's ``data.decode(result)`` works,
    and the caller sees the *public* name: ``compat_names=True`` (the
    default) can remap to a strictly narrower codec (``euc_jis_2004`` is
    reported as ``EUC-JP``), so a rival must decode under both names to be
    promoted.  ``prefer_superset=True`` can also narrow (cp125x leaves
    codepoints undefined that iso-8859-x maps), but that output transform
    checks the data itself before remapping.
    """
    if not decodes_completely(data, encoding):
        return False
    display = _COMPAT_NAMES.get(encoding)
    return display is None or decodes_completely(data, display)


def _prefer_decodable_on_tie(
    data: bytes,
    results: list[DetectionResult],
    *,
    input_truncated: bool,
) -> list[DetectionResult]:
    """Promote a strictly decoding rival over a winner with no real evidence.

    Byte-validity filtering runs incremental decoders with ``final=False``,
    tolerating an incomplete multi-byte sequence at the end because detection
    input is often a prefix of a larger whole.  When chardet examined the
    caller's *entire* input, that tolerance can hand back an encoding the
    caller's very next ``data.decode()`` will reject --- a four-byte
    ``iso-8859-1`` word ending in ``0xE1`` detected as utf-8 (issue #380).

    Fires only when *data* is the whole of what the caller handed over ---
    *input_truncated* is False --- the tail can actually hold a
    dangling sequence (a high byte in the final four, multi-byte winner),
    and the winner's tolerant decode is **non-empty pure ASCII** --- its
    only multi-byte evidence is the dangling tail itself.  An empty
    tolerant decode (the whole input is one clipped sequence) is zero
    evidence, not ASCII evidence, and disqualifies the flip.  The
    best-ranked rival that decodes the input completely under both its
    internal and public names then takes the top slot, regardless of the
    confidence gap: an all-ASCII-evidence winner detected nothing the
    rival did not also detect, and any statistical lead it holds comes
    from ASCII bigrams the rival matched equally well.  The scan sees the
    ranking as given, which under ``full_ranking=False`` is pruned; if no
    listed rival decodes, the winner stands (measured across a 648-case
    accent-final sweep, the pruned ranking always carried a decodable
    rival).

    The pure-ASCII condition is what makes the unconditional flip safe.  A
    short mid-character CJK cut has a correct answer that cannot decode the
    input --- flipping it to whichever single-byte codec happens to decode
    the bytes trades a right answer for a wrong one, and a 5-40 byte sweep
    measured exactly that under a gap-based rule (34 correct CJK answers
    lost, Big5 becoming cp1125).  Such a winner has decoded real multi-byte
    characters and keeps its ranking; with the pure-ASCII condition in
    place, the same sweep measures zero lost answers at any gap.
    """
    top = results[0] if results else None
    if (
        input_truncated
        or top is None
        or top.encoding is None
        or len(results) < 2
        # A dangling multi-byte tail needs a high byte among the final
        # bytes (empty data trivially has none).  No cheaper winner gate
        # exists: the registry's is_multibyte_cjk means CJK-style structural
        # multibyte and is False for utf-8, the main deferring codec.  The
        # helper below is a single tolerant decode; validity already ran
        # the same decode once per candidate, so this adds at most one
        # more, and only for high-byte-tailed winners.
        or not any(b >= 0x80 for b in data[-4:])
        or not dangling_tail_with_ascii_prefix(data, top.encoding)
    ):
        return results
    for i in range(1, len(results)):
        r = results[i]
        if r.encoding is None or not _decodes_under_public_names(data, r.encoding):
            continue
        return _promote_to_top(results, i)
    return results


# ---------------------------------------------------------------------------
# The pruning contract: what statistical pruning must score exactly
# ---------------------------------------------------------------------------

#: How far below the running second-best score a candidate can sit and still
#: be examined by a rank correction: rare-language arbitration reads margins
#: up to ``_RARE_ARBITRATION_MARGIN`` from the top, and confusion resolution
#: examines the band, kept with a 2x cushion for float noise.
_CORRECTION_REACH = _RARE_ARBITRATION_MARGIN + 2 * CONFUSION_BAND


def scoring_floor(top1: float, top2: float) -> float:
    """Return the score below which the rank corrections cannot examine a candidate.

    One half of the pruning contract statistical scoring consumes: given
    the running top two encoding scores, every candidate at or above this
    floor must carry its exact full-ranking score, or a correction could
    fire on an understated (or missing) entry and ``detect()`` would
    diverge from the unpruned full ranking.  The floor trails the
    second-best score by the corrections' reach; while the top is low
    enough for confusion resolution's strict tier to open, it extends down
    to that tier's floor, because a strict-tier promotion may raise any
    candidate above the tier floor into position 0 before the other
    corrections evaluate their triggers.

    One correction sits deliberately outside this floor: the decode-safety
    flip (:func:`_prefer_decodable_on_tie`) scans the ranking *as given*,
    including pruned-path tails whose entries may be understated or absent
    — a measured trade-off documented in its own docstring, not a floor
    violation to fix by widening the reach.
    """
    floor = top2 - _CORRECTION_REACH
    if top1 < STRICT_TIER_MAX_CONF:
        floor = min(floor, top1 * CONFUSION_FLOOR_RATIO)
    return floor


def forced_encodings(near_top: list[str]) -> list[str]:
    """Return the encodings the corrections look up by name, given the near-top set.

    The other half of the pruning contract: :func:`postprocess_results`
    inspects some encodings wherever they rank (the common Western Latin
    trio for niche Latin demotion, KOI8-T for the KOI8-R promotion), so
    pruning must score every variant of these whenever a trigger encoding
    sits at or above the :func:`scoring_floor` — confusion resolution may
    promote any such candidate to the top before those triggers are
    evaluated.
    """
    forced: list[str] = []
    if any(e in _DEMOTION_CANDIDATES for e in near_top):
        forced.extend(_COMMON_LATIN_ENCODINGS)
    if "koi8-r" in near_top:
        forced.append("koi8-t")
    return forced


def postprocess_results(
    data: bytes,
    results: list[DetectionResult],
    *,
    input_truncated: bool = False,
) -> list[DetectionResult]:
    """Apply rank corrections to the statistically scored results.

    Steps run in sequence, weakest evidence first: dead-heat priors
    (superset preference, era prevalence), then confusion-group resolution,
    niche Latin demotion, and KOI8-T promotion (byte-level evidence), and
    finally the classic-Mac line-ending promotion (platform evidence that
    should override the priors).  The decode-safety tiebreak runs last of
    all: whatever the ranking settled on, a winner that cannot decode the
    caller's complete input, and whose own evidence is nothing but the
    undecodable tail, yields to the best-ranked rival that can decode it.

    :param data: The raw byte data the results were produced from.
    :param results: A list of :class:`DetectionResult` ranked by confidence.
    :param input_truncated: True when *data* is a chardet-made slice rather
        than the caller's whole input --- the ``max_bytes`` slice, the
        evidence-cap slice, or ``UniversalDetector``'s buffer cap.  Any of
        them means the bytes here are not the whole story, so the
        decode-safety tiebreak, which reasons about what the caller will
        decode, stands down.
    :returns: A new list (or the same list) with rank corrections applied.
    """
    results = _promote_superset_on_dead_heat(data, results)
    results = _prefer_prevalent_on_dead_heat(data, results)
    results = _arbitrate_rare_language(results)
    results = resolve_confusion_groups(data, results)
    results = _demote_niche_latin(data, results)
    results = _promote_koi8t(data, results)
    results = _promote_mac_on_cr_line_endings(data, results)
    return _prefer_decodable_on_tie(data, results, input_truncated=input_truncated)
