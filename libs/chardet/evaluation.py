"""Accuracy-evaluation tables and predicates.

Tools for asking *"is this detection acceptable, given what was expected?"*
Used by the test suite and by benchmarking/diagnostic scripts (e.g.,
``scripts/compare_detectors.py``, ``scripts/diagnose_accuracy.py``).

This module owns three kinds of tables:

1. **Directional supersets** (:data:`SUPERSETS`) -- detecting a superset
   encoding when the expected encoding is a subset is correct (e.g.,
   detecting UTF-8 when expected is ASCII), but not the reverse.

2. **Bidirectional encoding groups** (:data:`BIDIRECTIONAL_GROUPS`) --
   groups of encodings where any member is interchangeable with any other.

3. **Bidirectional language groups** (:data:`LANGUAGE_EQUIVALENCES`) --
   ISO 639-1 codes for languages that are nearly indistinguishable by
   statistical detection (e.g., Slovak/Czech, Malay/Indonesian).

The corresponding predicates are :func:`is_correct`,
:func:`is_equivalent_detection`, and :func:`is_language_equivalent`.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable

from chardet.registry import lookup_encoding

# Directional superset relationships: detecting any of the supersets
# when the expected encoding is the subset counts as correct.
# E.g., expected=ascii, detected=utf-8 -> correct (utf-8 ⊃ ascii).
# But expected=utf-8, detected=ascii -> wrong (ascii ⊄ utf-8).
#
# Note: some subset keys (iso-8859-11) are not in the detection
# registry — the detector never returns them.  They appear here because
# chardet test-suite expected values use these names, so the superset
# mapping is needed for accuracy evaluation only.
SUPERSETS: dict[str, frozenset[str]] = {
    "ASCII": frozenset({"utf-8", "cp1252"}),
    "TIS-620": frozenset({"iso8859-11", "cp874"}),
    "ISO-8859-11": frozenset({"cp874"}),
    "GB2312": frozenset({"gb18030"}),
    "GBK": frozenset({"gb18030"}),
    "Big5": frozenset({"big5hkscs", "cp950"}),
    "Shift_JIS": frozenset({"cp932", "shift_jis_2004"}),
    "Shift-JISX0213": frozenset({"shift_jis_2004"}),
    "EUC-JP": frozenset({"euc_jis_2004"}),
    "EUC-JISX0213": frozenset({"euc_jis_2004"}),
    "EUC-KR": frozenset({"cp949"}),
    "CP037": frozenset({"cp1140"}),
    # ISO-2022-JP subsets: any branch variant is acceptable.
    # In our registry, base ISO-2022-JP is an alias of iso2022_jp_2, so all
    # three extended variants are supersets of the same base.  While the
    # extended variants use different escape sequences for non-basic characters,
    # real-world files rarely use those extensions — the base JIS X 0208
    # character set is shared by all variants and cross-decodes identically.
    # ISO2022-JP-1 and ISO2022-JP-3 use Python codec names (no hyphen between
    # "ISO" and "2022") because they appear as expected values in the test suite,
    # not as canonical chardet output.  They are consumed through
    # _NORMALIZED_SUPERSETS which normalizes via codecs.lookup().
    "ISO-2022-JP": frozenset({"iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_ext"}),
    "ISO2022-JP-1": frozenset({"iso2022_jp_2", "iso2022_jp_ext"}),
    "ISO2022-JP-3": frozenset({"iso2022_jp_2004"}),
    # ISO/Windows superset pairs
    "ISO-8859-1": frozenset({"cp1252"}),
    "ISO-8859-2": frozenset({"cp1250"}),
    "ISO-8859-5": frozenset({"cp1251"}),
    "ISO-8859-6": frozenset({"cp1256"}),
    "ISO-8859-7": frozenset({"cp1253"}),
    "ISO-8859-8": frozenset({"cp1255"}),
    "ISO-8859-9": frozenset({"cp1254"}),
    "ISO-8859-13": frozenset({"cp1257"}),
    # UTF-16/32: bare form (BOM-aware) is interchangeable with either endianness,
    # but LE and BE are NOT interchangeable with each other.
    "UTF-16": frozenset({"utf-16-le", "utf-16-be"}),
    "UTF-16-LE": frozenset({"utf-16"}),
    "UTF-16-BE": frozenset({"utf-16"}),
    "UTF-32": frozenset({"utf-32-le", "utf-32-be"}),
    "UTF-32-LE": frozenset({"utf-32"}),
    "UTF-32-BE": frozenset({"utf-32"}),
}

# Bidirectional equivalents -- groups where any member is acceptable for any other.
#
# NOTE: UTF-16/32 endianness is handled via directional SUPERSETS instead,
# because wrong endianness garbles text.  ISO-2022-JP variants remain here
# because base ISO-2022-JP is an alias of iso2022_jp_2 in our registry, so
# the SUPERSETS entries already make all variants interchangeable via the
# shared base.
BIDIRECTIONAL_GROUPS: tuple[tuple[str, ...], ...] = (
    ("iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_ext"),
)

# Bidirectional language equivalences — groups of ISO 639-1 codes for
# languages that are nearly indistinguishable by statistical detection.
# Detecting any member when another member of the same group was expected
# is considered acceptable.
LANGUAGE_EQUIVALENCES: tuple[tuple[str, ...], ...] = (
    ("sk", "cs"),  # Slovak / Czech — ~85% mutual intelligibility
    (
        "uk",
        "ru",
        "bg",
        "be",
    ),  # East Slavic + Bulgarian — shared Cyrillic, high written overlap
    ("ms", "id"),  # Malay / Indonesian — standardized variants of one language
    (
        "no",
        "da",
        "sv",
    ),  # Scandinavian — mutual intelligibility across the dialect continuum
)


def _build_group_index(
    groups: tuple[tuple[str, ...], ...],
    normalize: Callable[[str], str] = lambda x: x,
) -> dict[str, frozenset[str]]:
    """Build a lookup: key -> frozenset of all equivalent keys in the same group."""
    result: dict[str, frozenset[str]] = {}
    for group in groups:
        normed = frozenset(normalize(n) for n in group)
        for name in group:
            result[normalize(name)] = normed
    return result


_LANGUAGE_EQUIV: dict[str, frozenset[str]] = _build_group_index(LANGUAGE_EQUIVALENCES)


def is_language_equivalent(expected: str, detected: str) -> bool:
    """Check whether *detected* is an acceptable language for *expected*.

    Returns ``True`` when *expected* and *detected* are the same ISO 639-1
    code, or belong to the same equivalence group in
    :data:`LANGUAGE_EQUIVALENCES`.

    :param expected: Expected ISO 639-1 language code.
    :param detected: Detected ISO 639-1 language code.
    :returns: ``True`` if the languages are equivalent.
    """
    if expected == detected:
        return True
    group = _LANGUAGE_EQUIV.get(expected)
    return group is not None and detected in group


# Pre-built normalized lookups for fast comparison.
# Built iteratively because multiple SUPERSETS keys can normalize to the same
# canonical name (e.g., Shift_JIS and Shift-JISX0213 both → shift_jis_2004).
# Values are merged (unioned) when keys collide.
_NORMALIZED_SUPERSETS: dict[str, frozenset[str]] = {}
for _subset, _supersets in SUPERSETS.items():
    _key = lookup_encoding(_subset) or _subset
    _normed = frozenset(lookup_encoding(s) or s for s in _supersets)
    _NORMALIZED_SUPERSETS[_key] = _NORMALIZED_SUPERSETS.get(_key, frozenset()) | _normed


_NORMALIZED_BIDIR: dict[str, frozenset[str]] = _build_group_index(
    BIDIRECTIONAL_GROUPS, normalize=lambda n: lookup_encoding(n) or n
)


def is_exact_match(expected: str | None, detected: str | None) -> bool:
    """Check whether *detected* names the very same encoding as *expected*.

    Only alias and case differences are normalized away, so
    ``windows-1252`` matches ``cp1252``. Unlike :func:`is_correct`, this
    credits neither supersets nor byte-order variants: detecting UTF-8
    for an ASCII file is ``False`` here.

    This is the stricter convention some other detectors score
    themselves against. Reporting it alongside :func:`is_correct` makes
    the two conventions directly comparable instead of leaving the
    difference implicit.

    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if both names resolve to the same encoding.
    """
    if expected is None:
        return detected is None
    if detected is None:
        return False
    norm_exp = lookup_encoding(expected) or expected.lower()
    norm_det = lookup_encoding(detected) or detected.lower()
    return norm_exp == norm_det


def is_correct(expected: str | None, detected: str | None) -> bool:
    """Check whether *detected* is an acceptable answer for *expected*.

    Acceptable means:

    1. Exact match (after normalization), OR
    2. Both belong to the same bidirectional byte-order group, OR
    3. *detected* is a known superset of *expected*.

    See :func:`is_exact_match` for the stricter exact-only predicate.

    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if the detection is acceptable.
    """
    if expected is None:
        return detected is None
    if detected is None:
        return False

    # 1. Exact match
    if is_exact_match(expected, detected):
        return True

    norm_exp = lookup_encoding(expected) or expected.lower()
    norm_det = lookup_encoding(detected) or detected.lower()

    # 2. Bidirectional (same byte-order group)
    if norm_exp in _NORMALIZED_BIDIR and norm_det in _NORMALIZED_BIDIR[norm_exp]:
        return True

    # 3. Superset is acceptable (detected is a known superset of expected)
    return (
        norm_exp in _NORMALIZED_SUPERSETS
        and norm_det in _NORMALIZED_SUPERSETS[norm_exp]
    )


def _strip_combining(text: str) -> str:
    """NFKD-normalize *text* and strip all combining marks."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Pre-computed symbol pair lookups for O(1) equivalence checks.
# Both orderings are stored to avoid constructing temporaries per call.
_EQUIVALENT_SYMBOL_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("¤", "€"),
        ("€", "¤"),
    }
)


def _chars_equivalent(a: str, b: str) -> bool:
    """Return True if characters *a* and *b* are functionally equivalent.

    Equivalent means:
    - Same character, OR
    - Same base letter after stripping combining marks, OR
    - An explicitly listed symbol equivalence (e.g. ¤ ↔ €)
    """
    if a == b:
        return True
    if (a, b) in _EQUIVALENT_SYMBOL_PAIRS:
        return True
    # Compare base letters after stripping combining marks.
    return _strip_combining(a) == _strip_combining(b)


def is_equivalent_detection(
    data: bytes, expected: str | None, detected: str | None
) -> bool:
    """Check whether *detected* produces functionally identical text to *expected*.

    Returns ``True`` when:

    1. *detected* is not ``None`` and both encoding names normalize to the same
       codec, OR
    2. Decoding *data* with both encodings yields identical strings, OR
    3. Every differing character pair is functionally equivalent: same base
       letter after stripping combining marks, or an explicitly listed symbol
       equivalence (e.g. ¤ ↔ €).

    Returns ``False`` if *detected* is ``None``, either encoding is unknown,
    or either encoding cannot decode *data*.

    :param data: The raw byte data that was detected.
    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if decoding with *detected* yields functionally identical
        text to decoding with *expected*.
    """
    if expected is None:
        return detected is None
    if detected is None:
        return False

    norm_exp = lookup_encoding(expected) or expected.lower()
    norm_det = lookup_encoding(detected) or detected.lower()

    if norm_exp == norm_det:
        return True

    try:
        text_exp = data.decode(norm_exp)
        text_det = data.decode(norm_det)
    except (UnicodeDecodeError, LookupError):
        return False

    if text_exp == text_det:
        return True

    if len(text_exp) != len(text_det):
        return False

    return all(_chars_equivalent(a, b) for a, b in zip(text_exp, text_det, strict=True))


def is_acceptable(data: bytes, expected: str | None, detected: str | None) -> bool:
    """Check whether *detected* is an acceptable detection of *data* as *expected*.

    The composed predicate every accuracy consumer wants: name-level
    acceptance (:func:`is_correct` — exact match, byte-order group, or known
    superset) or byte-level equivalence on this particular input
    (:func:`is_equivalent_detection`).  Callers needing only one half, or
    the stricter :func:`is_exact_match`, should use the primitives directly.

    :param data: The raw byte data that was detected.
    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if the detection is acceptable for *data*.
    """
    return is_correct(expected, detected) or is_equivalent_detection(
        data, expected, detected
    )
