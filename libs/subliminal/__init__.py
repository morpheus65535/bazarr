# -*- coding: utf-8 -*-
__title__ = 'subliminal'
__version__ = '2.0.5'
__short_version__ = '.'.join(__version__.split('.')[:2])
__author__ = 'Antoine Bertin'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016, Antoine Bertin'

import logging

from .core import (AsyncProviderPool, ProviderPool, check_video, download_best_subtitles, download_subtitles,
                   list_subtitles, refine, save_subtitles, scan_video, scan_videos)
from .cache import region
from .exceptions import Error, ProviderError
from .extensions import provider_manager, refiner_manager
from .providers import Provider
from .score import compute_score, get_scores
from .subtitle import SUBTITLE_EXTENSIONS, Subtitle
from .video import VIDEO_EXTENSIONS, Episode, Movie, Video

logging.getLogger(__name__).addHandler(logging.NullHandler())
