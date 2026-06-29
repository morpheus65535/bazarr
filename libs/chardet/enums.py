"""Enumerations for chardet."""

from __future__ import annotations

import enum


class EncodingEra(enum.IntFlag):
    """Bit flags representing encoding eras for filtering detection candidates."""

    MODERN_WEB = 1
    LEGACY_ISO = 2
    LEGACY_MAC = 4
    LEGACY_REGIONAL = 8
    DOS = 16
    MAINFRAME = 32
    ALL = MODERN_WEB | LEGACY_ISO | LEGACY_MAC | LEGACY_REGIONAL | DOS | MAINFRAME


class LanguageFilter(enum.IntFlag):
    """Language filter flags for UniversalDetector (chardet 6.x API compat).

    Accepted but not used — our pipeline does not filter by language group.

    .. deprecated::
        Retained only for backward compatibility with chardet 6.x callers.
        Will be removed in a future major version.
    """

    CHINESE_SIMPLIFIED = 0x01
    CHINESE_TRADITIONAL = 0x02
    JAPANESE = 0x04
    KOREAN = 0x08
    NON_CJK = 0x10
    ALL = 0x1F
    CHINESE = CHINESE_SIMPLIFIED | CHINESE_TRADITIONAL
    CJK = CHINESE | JAPANESE | KOREAN
