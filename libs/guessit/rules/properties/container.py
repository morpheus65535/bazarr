#!/usr/bin/env python
"""
container property
"""

from __future__ import annotations

from typing import Any

from rebulk import Rebulk
from rebulk.remodule import re

from ...reutils import build_or_pattern
from ..common import seps
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def container(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "container"))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE).string_defaults(ignore_case=True)
    rebulk.defaults(
        name="container",
        formatter=lambda value: value.strip(seps),
        tags=["extension"],
        conflict_solver=lambda match, other: (
            other
            if other.name in ("source", "video_codec") or (other.name == "container" and "extension" not in other.tags)
            else "__default__"
        ),
    )

    subtitles = config["subtitles"]
    info = config["info"]
    videos = config["videos"]
    torrent = config["torrent"]
    nzb = config["nzb"]
    archives = config.get("archives", [])
    images = config.get("images", [])

    rebulk.regex(r"\." + build_or_pattern(subtitles) + "$", exts=subtitles, tags=["extension", "subtitle"])
    rebulk.regex(r"\." + build_or_pattern(info) + "$", exts=info, tags=["extension", "info"])
    rebulk.regex(r"\." + build_or_pattern(videos) + "$", exts=videos, tags=["extension", "video"])
    rebulk.regex(r"\." + build_or_pattern(torrent) + "$", exts=torrent, tags=["extension", "torrent"])
    rebulk.regex(r"\." + build_or_pattern(nzb) + "$", exts=nzb, tags=["extension", "nzb"])
    if archives:
        # escape=True because of "7z"; split RAR volumes (.r00/.r01/…) handled separately.
        rebulk.regex(
            r"\." + build_or_pattern(archives, escape=True) + "$", exts=archives, tags=["extension", "archive"]
        )
        rebulk.regex(r"\.r\d{2}$", tags=["extension", "archive"])
    if images:
        rebulk.regex(r"\." + build_or_pattern(images, escape=True) + "$", exts=images, tags=["extension", "image"])

    rebulk.defaults(
        clear=True,
        name="container",
        validator=seps_surround,
        formatter=lambda s: s.lower(),
        conflict_solver=lambda match, other: (
            match
            if other.name in ("source", "video_codec") or (other.name == "container" and "extension" in other.tags)
            else "__default__"
        ),
    )

    rebulk.string(*[sub for sub in subtitles if sub not in ("sub", "ass")], tags=["subtitle"])
    rebulk.string(*videos, tags=["video"])
    rebulk.string(*torrent, tags=["torrent"])
    rebulk.string(*nzb, tags=["nzb"])

    return rebulk
