# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime

from dogpile.cache import make_region
from dogpile.cache.util import sha1_mangle_key

#: Expiration time for show caching
SHOW_EXPIRATION_TIME = datetime.timedelta(weeks=3).total_seconds()

#: Expiration time for episode caching
EPISODE_EXPIRATION_TIME = datetime.timedelta(days=3).total_seconds()

#: Expiration time for scraper searches
REFINER_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()

# Mangle keys to prevent long filenames
region = make_region(key_mangler=sha1_mangle_key)
