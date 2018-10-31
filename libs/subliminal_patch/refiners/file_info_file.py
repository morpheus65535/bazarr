# coding=utf-8
import sys
import os
import logging
import codecs

from common import update_video
logger = logging.getLogger(__name__)


def refine(video, **kwargs):
    """

    :param video:
    :param kwargs:
    :return:
    """

    check_fns = [".file_info", "file_info"]

    # check for file_info on win32 first
    if sys.platform == "win32":
        check_fns.reverse()

    delimiter = '="'
    del_len = len(delimiter)
    video_fn = os.path.basename(video.name)
    orig_fn = None
    for fn in check_fns:
        path = os.path.join(os.path.dirname(video.name), fn)
        if os.path.isfile(path):
            logger.info(u"Found %s for %s", fn, video_fn)
            with codecs.open(path, "rb", encoding="utf-8") as f:
                for line in f:
                    if video_fn in line and delimiter in line:
                        orig_fn_start = line.index(delimiter) + del_len

                        # find end of orig fn
                        orig_fn_end = line.index('"', orig_fn_start)
                        orig_fn = line[orig_fn_start:orig_fn_end].strip()

                        # get optional json blob
                        break
        if orig_fn:
            update_video(video, orig_fn)
            break
