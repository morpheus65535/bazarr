#!/usr/bin/env python
"""
Typed keys (rebulk 6) binding match names to value types and formatters.

Single source of truth for the scalar properties whose patterns are built with a
typed :class:`~rebulk.key.Key`. Each key wires the match ``name``, its Python
value type and the ``(str) -> value`` formatter in one place: passing it via
``key=`` (Python-built patterns) or as a default formatter to
:func:`~guessit.config.load_config_patterns` (config-driven patterns) keeps that
binding here, and enables typed retrieval elsewhere (``matches[KEY]`` ->
``T | None``, ``matches.all(KEY)`` -> ``list[T]``).

``value_type`` must be scalar; structured/enum properties (``source``, ``other``,
…) carry no conversion and are intentionally left out.
"""

from __future__ import annotations

from rebulk import Key
from rebulk.remodule import re

from .quantity import BitRate, Size


def _format_volume(value: str) -> int:
    """Extract the volume number from a matched ``vol…N`` token."""
    return int(re.sub(r"\D", "", value))


# crc / uuid (raw string values)
CRC32 = Key("crc32", str)
UUID = Key("uuid", str)

# integer counters
BONUS = Key("bonus", int)
CD = Key("cd", int)
CD_COUNT = Key("cd_count", int)
FILM = Key("film", int)
VOLUME = Key("volume", int, formatter=_format_volume)

# episode core: declared once on the episodes builder; digit patterns inherit
# ``int`` per name while roman/CJK patterns keep their own formatter override.
#: ``count`` is an internal match name, renamed to ``episode_count`` / ``season_count``.
SEASON = Key("season", int)
EPISODE = Key("episode", int)
VERSION = Key("version", int)
COUNT = Key("count", int)

# quantities (custom scalar value types)
SIZE = Key("size", Size, formatter=Size.fromstring)
#: Patterns build matches named ``audio_bit_rate``; ``BitRateTypeRule`` renames
#: some of them to ``video_bit_rate`` afterwards (same value type).
AUDIO_BIT_RATE = Key("audio_bit_rate", BitRate, formatter=BitRate.fromstring)
