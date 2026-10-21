"""Public-API encoding-name remapping.

Two output transforms applied to detection results before they cross the
public API:

* :func:`apply_preferred_superset` -- when the ``prefer_superset`` API option
  is enabled, replaces detected ISO/subset encoding names with their
  Windows/CP supersets that modern software actually uses
  (e.g., ISO-8859-1 -> Windows-1252).

* :func:`apply_compat_names` -- when the default ``compat_names=True`` mode
  is enabled, maps internal Python codec names to the names chardet 5.x/6.x
  returned, preserving backward compatibility for callers that compare
  encoding strings directly.

Both transforms operate in-place on a :class:`~chardet.pipeline.DetectionDict`
and return the same dict for fluent chaining.
"""

from __future__ import annotations

from chardet._utils import decodes_without_error
from chardet.pipeline import DetectionDict

# Preferred superset name for each encoding, used by the ``prefer_superset``
# API option.  When enabled, detected encoding names are replaced with the
# Windows/CP superset that modern software actually uses (browsers, editors,
# etc. treat these ISO subsets as their Windows counterparts).
# Values are lowercase codec names, like the keys: this table only swaps one
# codec for another.  Display casing ("Windows-1252") is a separate step that
# :data:`_COMPAT_NAMES` applies afterwards, and a display-cased value here
# would reach it under a name it cannot map and no codec accepts.
PREFERRED_SUPERSET: dict[str, str] = {
    "ascii": "cp1252",
    "euc_kr": "cp949",
    "iso8859-1": "cp1252",
    "iso8859-2": "cp1250",
    "iso8859-5": "cp1251",
    "iso8859-6": "cp1256",
    "iso8859-7": "cp1253",
    "iso8859-8": "cp1255",
    "iso8859-9": "cp1254",
    "iso8859-11": "cp874",
    "iso8859-13": "cp1257",
    "tis-620": "cp874",
}


# Mapping from Python codec names to chardet 5.x/6.x compatible display names.
# Only entries where codec name differs from the compat output are listed.
# Encodings where codec name == compat name (e.g., "ascii", "utf-8") and
# encodings new to v7 have no entry — the codec name passes through unchanged.
_COMPAT_NAMES: dict[str, str] = {
    # 5.x compat — these encodings existed in chardet 5.x with different names
    "big5hkscs": "Big5",
    "cp855": "IBM855",
    "cp866": "IBM866",
    "cp874": "CP874",
    "cp932": "CP932",
    "cp949": "CP949",
    "euc_jis_2004": "EUC-JP",
    "euc_kr": "EUC-KR",
    "gb18030": "GB18030",
    "hz": "HZ-GB-2312",
    "iso2022_jp_2": "ISO-2022-JP",
    "iso2022_kr": "ISO-2022-KR",
    "iso8859-1": "ISO-8859-1",
    "iso8859-2": "ISO-8859-2",
    "iso8859-5": "ISO-8859-5",
    "iso8859-6": "ISO-8859-6",
    "iso8859-7": "ISO-8859-7",
    "iso8859-8": "ISO-8859-8",
    "iso8859-9": "ISO-8859-9",
    "iso8859-13": "ISO-8859-13",
    "johab": "Johab",
    "koi8-r": "KOI8-R",
    "mac-cyrillic": "MacCyrillic",
    "mac-roman": "MacRoman",
    "shift_jis_2004": "SHIFT_JIS",
    "tis-620": "TIS-620",
    "utf-16": "UTF-16",
    "utf-32": "UTF-32",
    "utf-8-sig": "UTF-8-SIG",
    "cp1250": "Windows-1250",
    "cp1251": "Windows-1251",
    "cp1252": "Windows-1252",
    "cp1253": "Windows-1253",
    "cp1254": "Windows-1254",
    "cp1255": "Windows-1255",
    "cp1256": "Windows-1256",
    "cp1257": "Windows-1257",
    # 6.x compat — new in chardet 6.x with different names
    "kz1048": "KZ1048",
    "mac-greek": "MacGreek",
    "mac-iceland": "MacIceland",
    "mac-latin2": "MacLatin2",
    "mac-turkish": "MacTurkish",
}


def _remap_encoding(result: DetectionDict, mapping: dict[str, str]) -> DetectionDict:
    """Replace the encoding name using *mapping*, modifying *result* in-place."""
    enc = result.get("encoding")
    if isinstance(enc, str):
        result["encoding"] = mapping.get(enc, enc)
    return result


def apply_preferred_superset(
    result: DetectionDict,
    data: bytes | None = None,
    *,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
) -> DetectionDict:
    """Replace the encoding name with its preferred Windows/CP superset.

    Modifies the ``"encoding"`` value in *result* in-place and returns *result*
    for fluent chaining.

    The Windows code pages leave a few C1 positions undefined that their ISO
    subsets map (0x81, 0x8D, 0x8F, 0x90, 0x9D under cp1252), so the remap is
    decode-safe only for data that avoids them.  When *data* is given, the
    remap applies only if the superset decodes it; otherwise the detected
    name stands, being the one that does.

    :param result: A detection result dict containing an ``"encoding"`` key.
    :param data: The bytes *result* was detected from, when known.
    :param include_encodings: Canonical encoding names (as returned by
        :func:`~chardet.registry.normalize_encodings`) allowed in the result.
        The superset is skipped when it is not one of them.
    :param exclude_encodings: Canonical encoding names forbidden in the
        result.  The superset is skipped when it is one of them.
    :returns: The same *result* dict, modified in-place.
    """
    enc = result.get("encoding")
    if not isinstance(enc, str):
        return result
    superset = PREFERRED_SUPERSET.get(enc)
    if superset is None:
        return result
    if include_encodings is not None and superset not in include_encodings:
        return result
    if exclude_encodings is not None and superset in exclude_encodings:
        return result
    if data is None or decodes_without_error(data, superset):
        result["encoding"] = superset
    return result


# Deprecated alias — kept for external consumers.
apply_legacy_rename = apply_preferred_superset


#: Internal names whose display name resolves to a *narrower* Python codec.
#: ``EUC-JP`` is ``euc_jp``, which lacks the JIS X 0213 rows that
#: ``euc_jis_2004`` validated; ``SHIFT_JIS``, ``Big5`` and ``ISO-2022-JP``
#: narrow ``shift_jis_2004``, ``big5hkscs`` and ``iso2022_jp_2`` the same
#: way.  A test pins this set to what :mod:`codecs` reports, so a new
#: mapping cannot narrow silently.
NARROWER_DISPLAY_NAMES: frozenset[str] = frozenset(
    {"big5hkscs", "euc_jis_2004", "iso2022_jp_2", "shift_jis_2004"}
)


def apply_compat_names(
    result: DetectionDict,
    data: bytes | None = None,
) -> DetectionDict:
    """Convert internal codec names to chardet 5.x/6.x compatible names.

    Modifies the ``"encoding"`` value in *result* in-place and returns *result*
    for fluent chaining.

    The internal name is the codec the pipeline validated the data under.
    For the names in :data:`NARROWER_DISPLAY_NAMES` the display name is a
    smaller codec, so when *data* is given the rename applies only if the
    display codec decodes it; otherwise the internal name stands, which
    Python's codecs accept as is.  Without *data* the rename is
    unconditional, as before.

    :param result: A detection result dict containing an ``"encoding"`` key.
    :param data: The bytes *result* was detected from, when known.
    :returns: The same *result* dict, modified in-place.
    """
    enc = result.get("encoding")
    if (
        data is not None
        and isinstance(enc, str)
        and enc in NARROWER_DISPLAY_NAMES
        and not decodes_without_error(data, _COMPAT_NAMES[enc])
    ):
        return result
    return _remap_encoding(result, _COMPAT_NAMES)
