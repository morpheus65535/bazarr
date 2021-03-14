# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
from hashlib import sha1

from dogpile.cache import make_region

#: Expiration time for show caching
SHOW_EXPIRATION_TIME = datetime.timedelta(weeks=3).total_seconds()

#: Expiration time for episode caching
EPISODE_EXPIRATION_TIME = datetime.timedelta(days=3).total_seconds()

#: Expiration time for scraper searches
REFINER_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()


def sha1_key_mangler(key):
    """Return sha1 hex for cache keys"""
    if isinstance(key, str):
        key = key.encode("utf-8")

    return sha1(key).hexdigest()


# Use key mangler to limit cache key names to 40 characters
region = make_region(key_mangler=sha1_key_mangler)
