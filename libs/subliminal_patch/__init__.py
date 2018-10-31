# coding=utf-8

import subliminal

# patch subliminal's subtitle and provider base
from .subtitle import Subtitle, guess_matches
from .providers import Provider
subliminal.subtitle.Subtitle = Subtitle
subliminal.subtitle.guess_matches = guess_matches

from .core import scan_video, search_external_subtitles, list_all_subtitles, save_subtitles, refine, \
    download_best_subtitles
from .score import compute_score
from .video import Video
import extensions
import http

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles
subliminal.save_subtitles = subliminal.core.save_subtitles = save_subtitles
subliminal.refine = subliminal.core.refine = refine
subliminal.video.Video = subliminal.Video = Video
subliminal.video.Episode.__bases__ = (Video,)
subliminal.video.Movie.__bases__ = (Video,)

# add our own list_all_subtitles
subliminal.list_all_subtitles = subliminal.core.list_all_subtitles = list_all_subtitles
