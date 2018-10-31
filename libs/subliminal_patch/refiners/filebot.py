# coding=utf-8

import logging
from libfilebot import get_filebot_attrs
from common import update_video

logger = logging.getLogger(__name__)


def refine(video, **kwargs):
    """

    :param video:
    :param kwargs:
    :return:
    """
    try:
        orig_fn = get_filebot_attrs(video.name)

        if orig_fn:
            update_video(video, orig_fn)
        else:
            logger.info(u"%s: Filebot didn't return an original filename", video.name)
    except:
        logger.exception(u"%s: Something went wrong when retrieving filebot attributes:", video.name)
