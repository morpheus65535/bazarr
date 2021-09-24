# coding=utf-8
from __future__ import absolute_import
import os

from .common import update_video


def refine(video, **kwargs):
    """

    :param video:
    :param kwargs:
    :return:
    """
    try:
        orig_fn = os.path.basename(os.path.realpath(video.name))
    except Exception:
        return

    if orig_fn:
        update_video(video, orig_fn)
