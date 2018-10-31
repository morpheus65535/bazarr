# coding=utf-8

import logging
import os

from guessit import guessit
from subliminal import Episode
from subliminal_patch.core import remove_crap_from_fn

logger = logging.getLogger(__name__)


def update_video(video, fn):
    guess_from = remove_crap_from_fn(fn)

    logger.debug(u"Got original filename: %s", guess_from)

    # guess
    hints = {
        "single_value": True,
        "type": "episode" if isinstance(video, Episode) else "movie",
    }

    guess = guessit(guess_from, options=hints)

    for attr in ("release_group", "format",):
        if attr in guess:
            value = guess.get(attr)
            logger.debug(u"%s: Filling attribute %s: %s", video.name, attr, value)
            setattr(video, attr, value)

    video.original_name = os.path.basename(guess_from)
