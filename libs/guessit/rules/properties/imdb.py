#!/usr/bin/env python
"""
imdb_id, tmdb_id and tvdb_id properties
"""

from __future__ import annotations

import re
from typing import Any

from rebulk import Rebulk

from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def imdb(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "imdb_id"))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(validator=seps_surround)

    # IMDb ids are `tt` followed by 7-8 digits, e.g. "Movie.2020.tt1234567.1080p".
    rebulk.regex(r"tt\d{7,8}", name="imdb_id", formatter=lambda value: value.lower())

    # TMDb / TVDb ids in Plex/Jellyfin-style naming: {tmdb-12345}, [tvdbid-12345],
    # tmdb=12345, etc. Capture the numeric id only.
    rebulk.regex(
        r"tmdb(?:id)?[-=]?(?P<tmdb_id>\d{1,9})", name="tmdb_id", private_parent=True, children=True, formatter=int
    )
    rebulk.regex(
        r"tvdb(?:id)?[-=]?(?P<tvdb_id>\d{1,9})", name="tvdb_id", private_parent=True, children=True, formatter=int
    )

    return rebulk
