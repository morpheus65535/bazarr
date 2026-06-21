"""Encoding registry with metadata for all supported encodings."""

from __future__ import annotations

import codecs
import dataclasses
import functools
from collections.abc import Iterable
from types import MappingProxyType
from typing import Literal

from chardet.enums import EncodingEra

EncodingName = Literal[
    "ascii",
    "big5hkscs",
    "cp1006",
    "cp1026",
    "cp1125",
    "cp1140",
    "cp1250",
    "cp1251",
    "cp1252",
    "cp1253",
    "cp1254",
    "cp1255",
    "cp1256",
    "cp1257",
    "cp1258",
    "cp273",
    "cp424",
    "cp437",
    "cp500",
    "cp720",
    "cp737",
    "cp775",
    "cp850",
    "cp852",
    "cp855",
    "cp856",
    "cp857",
    "cp858",
    "cp860",
    "cp861",
    "cp862",
    "cp863",
    "cp864",
    "cp865",
    "cp866",
    "cp869",
    "cp874",
    "cp875",
    "cp932",
    "cp949",
    "euc_jis_2004",
    "euc_kr",
    "gb18030",
    "hp-roman8",
    "hz",
    "iso2022_jp_2",
    "iso2022_jp_2004",
    "iso2022_jp_ext",
    "iso2022_kr",
    "iso8859-1",
    "iso8859-10",
    "iso8859-13",
    "iso8859-14",
    "iso8859-15",
    "iso8859-16",
    "iso8859-2",
    "iso8859-3",
    "iso8859-4",
    "iso8859-5",
    "iso8859-6",
    "iso8859-7",
    "iso8859-8",
    "iso8859-9",
    "johab",
    "koi8-r",
    "koi8-t",
    "koi8-u",
    "kz1048",
    "mac-cyrillic",
    "mac-greek",
    "mac-iceland",
    "mac-latin2",
    "mac-roman",
    "mac-turkish",
    "ptcp154",
    "shift_jis_2004",
    "tis-620",
    "utf-16",
    "utf-16-be",
    "utf-16-le",
    "utf-32",
    "utf-32-be",
    "utf-32-le",
    "utf-7",
    "utf-8",
    "utf-8-sig",
]

# Shared language tuples — used by multiple EncodingInfo entries below.
_WESTERN = (
    "br",
    "cy",
    "da",
    "de",
    "en",
    "es",
    "fi",
    "fr",
    "ga",
    "id",
    "is",
    "it",
    "ms",
    "nl",
    "no",
    "pt",
    "sv",
)
_WESTERN_TR = (*_WESTERN, "tr")
_CYRILLIC = ("ru", "bg", "uk", "sr", "mk", "be")
_CENTRAL_EU = ("pl", "cs", "hu", "hr", "ro", "sk", "sl")
_CENTRAL_EU_NO_RO = ("pl", "cs", "hu", "hr", "sk", "sl")
_BALTIC = ("et", "lt", "lv")
_ARABIC = ("ar", "fa")


@dataclasses.dataclass(frozen=True, slots=True)
class EncodingInfo:
    """Metadata for a single encoding."""

    name: EncodingName
    aliases: tuple[str, ...]
    era: EncodingEra
    is_multibyte: bool
    languages: tuple[str, ...]


@functools.lru_cache(maxsize=256)
def get_candidates(
    era: EncodingEra,
    include_encodings: frozenset[str] | None = None,
    exclude_encodings: frozenset[str] | None = None,
) -> tuple[EncodingInfo, ...]:
    """Return registry entries matching the given filters.

    Filters are applied in order: era, include, exclude.

    :param era: Bit flags specifying which encoding eras to include.
    :param include_encodings: If not ``None``, only return encodings in this set.
    :param exclude_encodings: If not ``None``, exclude encodings in this set.
    :returns: A tuple of matching :class:`EncodingInfo` entries.
    """
    candidates = (enc for enc in REGISTRY.values() if enc.era & era)
    if include_encodings is not None:
        candidates = (enc for enc in candidates if enc.name in include_encodings)
    if exclude_encodings is not None:
        candidates = (enc for enc in candidates if enc.name not in exclude_encodings)
    return tuple(candidates)


# Era assignments match chardet 6.0.0's chardet/metadata/charsets.py

_REGISTRY_ENTRIES = (
    # === MODERN_WEB ===
    EncodingInfo(
        name="ascii",
        aliases=("us-ascii",),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-8",
        aliases=(
            "utf-8",
            "utf8",
            "csutf8",
            "unicode-1-1-utf-8",
            "unicode11utf8",
            "unicode20utf8",
            "x-unicode20utf8",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-8-sig",
        aliases=("UTF-8-SIG", "utf-8-bom"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-16",
        aliases=("UTF-16", "utf16", "csutf16"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-16-be",
        aliases=("UTF-16-BE", "utf-16be", "csutf16be"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-16-le",
        aliases=("UTF-16-LE", "utf-16le", "csutf16le"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-32",
        aliases=("UTF-32", "utf32", "csutf32"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-32-be",
        aliases=("UTF-32-BE", "utf-32be", "csutf32be"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-32-le",
        aliases=("UTF-32-LE", "utf-32le", "csutf32le"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(),
    ),
    EncodingInfo(
        name="utf-7",
        aliases=("UTF-7", "utf7", "csutf7"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=(),
    ),
    # CJK - Modern Web
    EncodingInfo(
        name="big5hkscs",
        aliases=(
            "Big5-HKSCS",
            "Big5HKSCS",
            "big5",
            "big5-tw",
            "csbig5",
            "cp950",
            "cn-big5",
            "x-x-big5",
            "csbig5hkscs",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("zh",),
    ),
    EncodingInfo(
        name="cp932",
        aliases=(
            "CP932",
            "ms932",
            "mskanji",
            "ms-kanji",
            "cswindows31j",
            "windows-31j",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    EncodingInfo(
        # Note: "korean" is NOT an alias here.  Python's codec table
        # already resolves "korean" to ``euc_kr``, and WHATWG's primary
        # name for the group is EUC-KR, so letting the default fall
        # through is more spec-aligned than routing to cp949.
        name="cp949",
        aliases=(
            "CP949",
            "ms949",
            "uhc",
            "windows-949",
            "csksc56011987",
            "iso-ir-149",
            "ks_c_5601-1987",
            "ks_c_5601-1989",
            "ksc5601",
            "ksc_5601",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ko",),
    ),
    EncodingInfo(
        name="euc_jis_2004",
        aliases=(
            "EUC-JIS-2004",
            "euc-jp",
            "eucjp",
            "ujis",
            "u-jis",
            "euc-jisx0213",
            "cseucpkdfmtjapanese",
            "x-euc-jp",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    EncodingInfo(
        name="euc_kr",
        aliases=("EUC-KR", "euckr", "cseuckr"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ko",),
    ),
    EncodingInfo(
        # Note: "chinese" is NOT listed here because the label is
        # semantically ambiguous between Traditional (Big5) and Simplified
        # (GB18030) Chinese.  Python's codec table still resolves
        # "chinese" -> "gb2312" -> (via the gb2312 alias below) gb18030,
        # so the label continues to work for Simplified content via the
        # codec fallback in lookup_encoding().  We simply decline to
        # bless the ambiguity in our own table.
        name="gb18030",
        aliases=(
            "GB18030",
            "gb-18030",
            "gb2312",
            "gbk",
            "csgb2312",
            "gb_2312",
            "gb_2312-80",
            "x-gbk",
            "csiso58gb231280",
            "iso-ir-58",
            "csgb18030",
            "csgbk",
            "cp936",
            "ms936",
            "windows-936",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("zh",),
    ),
    EncodingInfo(
        name="hz",
        aliases=("HZ-GB-2312", "hz"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=True,
        languages=("zh",),
    ),
    EncodingInfo(
        name="iso2022_jp_2",
        aliases=(
            "ISO-2022-JP-2",
            "iso-2022-jp",
            "csiso2022jp",
            "iso2022-jp-1",
            "csiso2022jp2",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    EncodingInfo(
        name="iso2022_jp_2004",
        aliases=("ISO-2022-JP-2004", "iso2022-jp-3"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    EncodingInfo(
        name="iso2022_jp_ext",
        aliases=("ISO-2022-JP-EXT",),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    EncodingInfo(
        name="iso2022_kr",
        aliases=("ISO-2022-KR", "csiso2022kr"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=True,
        languages=("ko",),
    ),
    EncodingInfo(
        name="shift_jis_2004",
        aliases=(
            "Shift-JIS-2004",
            "Shift_JIS_2004",
            "shift_jis",
            "sjis",
            "shiftjis",
            "s_jis",
            "shift-jisx0213",
            "x-sjis",
            "csshiftjis",
            "ms_kanji",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=True,
        languages=("ja",),
    ),
    # Windows code pages - Modern Web
    EncodingInfo(
        name="cp874",
        aliases=("CP874", "windows-874", "dos-874"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("th",),
    ),
    EncodingInfo(
        name="cp1250",
        aliases=("Windows-1250", "cp1250", "x-cp1250", "cswindows1250"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=(*_CENTRAL_EU, "sr"),
    ),
    EncodingInfo(
        name="cp1251",
        aliases=("Windows-1251", "cp1251", "x-cp1251", "cswindows1251"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=_CYRILLIC,
    ),
    EncodingInfo(
        name="cp1252",
        aliases=("Windows-1252", "cp1252", "x-cp1252", "cswindows1252"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="cp1253",
        aliases=("Windows-1253", "cp1253", "x-cp1253", "cswindows1253"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("el",),
    ),
    EncodingInfo(
        name="cp1254",
        aliases=("Windows-1254", "cp1254", "x-cp1254", "cswindows1254"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("tr",),
    ),
    EncodingInfo(
        name="cp1255",
        aliases=("Windows-1255", "cp1255", "x-cp1255", "cswindows1255"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("he",),
    ),
    EncodingInfo(
        name="cp1256",
        aliases=("Windows-1256", "cp1256", "x-cp1256", "cswindows1256"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=_ARABIC,
    ),
    EncodingInfo(
        name="cp1257",
        aliases=("Windows-1257", "cp1257", "x-cp1257", "cswindows1257"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=_BALTIC,
    ),
    EncodingInfo(
        name="cp1258",
        aliases=("Windows-1258", "cp1258", "x-cp1258", "cswindows1258"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("vi",),
    ),
    # KOI8 - Modern Web
    EncodingInfo(
        name="koi8-r",
        aliases=("KOI8-R", "koi8r", "koi", "koi8", "cskoi8r"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("ru",),
    ),
    EncodingInfo(
        name="koi8-u",
        aliases=("KOI8-U", "koi8u", "koi8-ru", "cskoi8u"),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("uk",),
    ),
    # TIS-620 - Modern Web
    EncodingInfo(
        name="tis-620",
        aliases=(
            "TIS-620",
            "tis620",
            "iso-8859-11",
            "iso8859-11",
            "iso885911",
            "cstis620",
        ),
        era=EncodingEra.MODERN_WEB,
        is_multibyte=False,
        languages=("th",),
    ),
    # === LEGACY_ISO ===
    EncodingInfo(
        name="iso8859-1",
        aliases=("ISO-8859-1", "latin-1", "latin1", "iso8859-1", "iso88591"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="iso8859-2",
        aliases=("ISO-8859-2", "latin-2", "latin2", "iso8859-2", "iso88592"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_CENTRAL_EU,
    ),
    EncodingInfo(
        name="iso8859-3",
        aliases=("ISO-8859-3", "latin-3", "latin3", "iso8859-3", "iso88593"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("eo", "mt", "tr"),
    ),
    EncodingInfo(
        name="iso8859-4",
        aliases=("ISO-8859-4", "latin-4", "latin4", "iso8859-4", "iso88594"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_BALTIC,
    ),
    EncodingInfo(
        name="iso8859-5",
        aliases=("ISO-8859-5", "iso8859-5", "cyrillic", "iso88595"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_CYRILLIC,
    ),
    EncodingInfo(
        # The -E ("explicit directionality") and -I ("implicit
        # directionality") variants listed by IANA and WHATWG are
        # higher-level bidi-ordering hints, not separate codecs -- Python
        # stdlib has no distinct decoder for them, so all four resolve to
        # the same ``iso8859-6`` canonical here.
        name="iso8859-6",
        aliases=(
            "ISO-8859-6",
            "iso8859-6",
            "arabic",
            "iso88596",
            "iso-8859-6-e",
            "iso-8859-6-i",
            "csiso88596e",
            "csiso88596i",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_ARABIC,
    ),
    EncodingInfo(
        name="iso8859-7",
        aliases=(
            "ISO-8859-7",
            "iso8859-7",
            "greek",
            "iso88597",
            "sun_eu_greek",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("el",),
    ),
    EncodingInfo(
        # WHATWG and IANA distinguish ISO-8859-8 ("visual", -E) from
        # ISO-8859-8-I ("logical", -I) to signal Hebrew bidi ordering, but
        # Python's stdlib has a single ``iso8859-8`` codec -- the bidi
        # distinction is a higher-layer concern.  All variants collapse
        # onto this one canonical.
        name="iso8859-8",
        aliases=(
            "ISO-8859-8",
            "iso8859-8",
            "hebrew",
            "iso88598",
            "iso-8859-8-e",
            "iso-8859-8-i",
            "csiso88598e",
            "csiso88598i",
            "visual",
            "logical",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("he",),
    ),
    EncodingInfo(
        name="iso8859-9",
        aliases=("ISO-8859-9", "latin-5", "latin5", "iso8859-9", "iso88599"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("tr",),
    ),
    EncodingInfo(
        name="iso8859-10",
        aliases=("ISO-8859-10", "latin-6", "latin6", "iso8859-10", "iso885910"),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("is", "fi"),
    ),
    EncodingInfo(
        name="iso8859-13",
        aliases=(
            "ISO-8859-13",
            "latin-7",
            "latin7",
            "iso8859-13",
            "iso885913",
            "csiso885913",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_BALTIC,
    ),
    EncodingInfo(
        # ``iso-celtic`` is a Python stdlib alias, not a WHATWG/IANA name.
        name="iso8859-14",
        aliases=(
            "ISO-8859-14",
            "latin-8",
            "latin8",
            "iso8859-14",
            "iso885914",
            "csiso885914",
            "iso-ir-199",
            "iso-celtic",
            "l8",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("cy", "ga", "br", "gd"),
    ),
    EncodingInfo(
        name="iso8859-15",
        aliases=(
            "ISO-8859-15",
            "latin-9",
            "latin9",
            "iso8859-15",
            "iso885915",
            "csisolatin9",
            "csiso885915",
            "l9",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="iso8859-16",
        aliases=(
            "ISO-8859-16",
            "latin-10",
            "latin10",
            "iso8859-16",
            "iso885916",
            "csiso885916",
            "iso-ir-226",
            "l10",
        ),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=False,
        languages=("ro", "pl", "hr", "hu", "sk", "sl"),
    ),
    # Johab - Legacy ISO per chardet 6.0.0
    EncodingInfo(
        name="johab",
        aliases=("Johab",),
        era=EncodingEra.LEGACY_ISO,
        is_multibyte=True,
        languages=("ko",),
    ),
    # === LEGACY_MAC ===
    EncodingInfo(
        name="mac-cyrillic",
        aliases=(
            "Mac-Cyrillic",
            "MacCyrillic",
            "maccyrillic",
            "x-mac-cyrillic",
            "x-mac-ukrainian",
        ),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=_CYRILLIC,
    ),
    EncodingInfo(
        name="mac-greek",
        aliases=("Mac-Greek", "MacGreek", "macgreek"),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=("el",),
    ),
    EncodingInfo(
        name="mac-iceland",
        aliases=("Mac-Iceland", "MacIceland", "maciceland"),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=("is",),
    ),
    EncodingInfo(
        name="mac-latin2",
        aliases=("Mac-Latin2", "MacLatin2", "maclatin2", "maccentraleurope"),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=_CENTRAL_EU_NO_RO,
    ),
    EncodingInfo(
        name="mac-roman",
        aliases=(
            "Mac-Roman",
            "MacRoman",
            "macroman",
            "macintosh",
            "csmacintosh",
            "mac",
            "x-mac-roman",
        ),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="mac-turkish",
        aliases=("Mac-Turkish", "MacTurkish", "macturkish"),
        era=EncodingEra.LEGACY_MAC,
        is_multibyte=False,
        languages=("tr",),
    ),
    # === LEGACY_REGIONAL ===
    EncodingInfo(
        name="cp720",
        aliases=("CP720",),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=_ARABIC,
    ),
    EncodingInfo(
        name="cp1006",
        aliases=("CP1006",),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=("ur",),
    ),
    EncodingInfo(
        name="cp1125",
        aliases=("CP1125",),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=("uk",),
    ),
    EncodingInfo(
        name="koi8-t",
        aliases=("KOI8-T",),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=("tg",),
    ),
    EncodingInfo(
        name="kz1048",
        aliases=("KZ-1048", "kz1048", "strk1048-2002", "rk1048"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=("kk",),
    ),
    EncodingInfo(
        name="ptcp154",
        aliases=("PTCP154", "pt154", "cp154"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=("kk",),
    ),
    EncodingInfo(
        name="hp-roman8",
        aliases=("HP-Roman8", "roman8", "r8", "csHPRoman8"),
        era=EncodingEra.LEGACY_REGIONAL,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    # === DOS ===
    EncodingInfo(
        name="cp437",
        aliases=("CP437",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("en", "fr", "de", "es", "pt", "it", "nl", "da", "sv", "fi", "ga"),
    ),
    EncodingInfo(
        name="cp737",
        aliases=("CP737",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("el",),
    ),
    EncodingInfo(
        name="cp775",
        aliases=("CP775",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_BALTIC,
    ),
    EncodingInfo(
        name="cp850",
        aliases=("CP850",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="cp852",
        aliases=("CP852",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_CENTRAL_EU,
    ),
    EncodingInfo(
        name="cp855",
        aliases=("CP855",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_CYRILLIC,
    ),
    EncodingInfo(
        name="cp856",
        aliases=("CP856",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("he",),
    ),
    EncodingInfo(
        name="cp857",
        aliases=("CP857",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("tr",),
    ),
    EncodingInfo(
        name="cp858",
        aliases=("CP858",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="cp860",
        aliases=("CP860",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("pt",),
    ),
    EncodingInfo(
        name="cp861",
        aliases=("CP861",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("is",),
    ),
    EncodingInfo(
        name="cp862",
        aliases=("CP862",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("he",),
    ),
    EncodingInfo(
        name="cp863",
        aliases=("CP863",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("fr",),
    ),
    EncodingInfo(
        name="cp864",
        aliases=("CP864",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("ar",),
    ),
    EncodingInfo(
        name="cp865",
        aliases=("CP865",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("da", "no"),
    ),
    EncodingInfo(
        name="cp866",
        aliases=("CP866",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=_CYRILLIC,
    ),
    EncodingInfo(
        name="cp869",
        aliases=("CP869",),
        era=EncodingEra.DOS,
        is_multibyte=False,
        languages=("el",),
    ),
    # === MAINFRAME ===
    EncodingInfo(
        name="cp1140",
        aliases=(
            "CP1140",
            "cp037",
            "cp01140",
            "ibm01140",
            "ibm1140",
            "csibm01140",
        ),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=_WESTERN_TR,
    ),
    EncodingInfo(
        name="cp424",
        aliases=("CP424",),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=("he",),
    ),
    EncodingInfo(
        name="cp500",
        aliases=("CP500",),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=_WESTERN,
    ),
    EncodingInfo(
        name="cp875",
        aliases=("CP875",),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=("el",),
    ),
    EncodingInfo(
        name="cp1026",
        aliases=("CP1026",),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=("tr",),
    ),
    EncodingInfo(
        name="cp273",
        aliases=("CP273",),
        era=EncodingEra.MAINFRAME,
        is_multibyte=False,
        languages=("de",),
    ),
)

REGISTRY: MappingProxyType[str, EncodingInfo] = MappingProxyType(
    {e.name: e for e in _REGISTRY_ENTRIES}
)


@functools.cache
def lookup_encoding(name: str) -> EncodingName | None:
    """Convert an encoding name string to the canonical EncodingName.

    Handles arbitrary casing, aliases, and Python codec names.

    :param name: Any encoding name string.
    :returns: The canonical :data:`EncodingName`, or ``None`` if unknown.
    """
    lowered = name.lower()
    for entry in REGISTRY.values():
        if entry.name == lowered:
            return entry.name
        for alias in entry.aliases:
            if alias.lower() == lowered:
                return entry.name
    # Fallback: resolve through Python's codec registry
    try:
        codec_name = codecs.lookup(name).name
    except (LookupError, ValueError):
        return None
    if codec_name != lowered:
        return lookup_encoding(codec_name)
    return None


def _validate_encoding(name: str, param_name: str) -> str:
    """Validate and normalize a single encoding name.

    :param name: The encoding name to validate.
    :param param_name: Parameter name for error messages.
    :returns: The canonical encoding name.
    :raises ValueError: If the encoding name is unknown.
    """
    canonical = lookup_encoding(name)
    if canonical is None:
        msg = f"Unknown encoding {name!r} in {param_name}"
        raise ValueError(msg)
    return canonical


def normalize_encodings(
    encodings: Iterable[str] | None,
    param_name: str,
) -> frozenset[str] | None:
    """Normalize an iterable of encoding names to canonical forms.

    :param encodings: Encoding names to normalize, or ``None``.
    :param param_name: Parameter name for error messages.
    :returns: A frozenset of canonical encoding names, or ``None``.
    :raises ValueError: If any encoding name is unknown.
    """
    if encodings is None:
        return None
    result = frozenset(_validate_encoding(name, param_name) for name in encodings)
    if not result:
        msg = f"{param_name} must not be empty; omit the argument or pass None to disable filtering"
        raise ValueError(msg)
    return result
