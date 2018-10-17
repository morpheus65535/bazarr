#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
container property
"""
from rebulk.remodule import re

from rebulk import Rebulk

from ..common import seps
from ..common.validators import seps_surround
from ...reutils import build_or_pattern


def container():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE).string_defaults(ignore_case=True)
    rebulk.defaults(name='container',
                    formatter=lambda value: value.strip(seps),
                    tags=['extension'],
                    conflict_solver=lambda match, other: other
                    if other.name in ['format', 'video_codec'] or
                    other.name == 'container' and 'extension' not in other.tags
                    else '__default__')

    subtitles = ['srt', 'idx', 'sub', 'ssa', 'ass']
    info = ['nfo']
    videos = ['3g2', '3gp', '3gp2', 'asf', 'avi', 'divx', 'flv', 'm4v', 'mk2',
              'mka', 'mkv', 'mov', 'mp4', 'mp4a', 'mpeg', 'mpg', 'ogg', 'ogm',
              'ogv', 'qt', 'ra', 'ram', 'rm', 'ts', 'wav', 'webm', 'wma', 'wmv',
              'iso', 'vob']
    torrent = ['torrent']
    nzb = ['nzb']

    rebulk.regex(r'\.'+build_or_pattern(subtitles)+'$', exts=subtitles, tags=['extension', 'subtitle'])
    rebulk.regex(r'\.'+build_or_pattern(info)+'$', exts=info, tags=['extension', 'info'])
    rebulk.regex(r'\.'+build_or_pattern(videos)+'$', exts=videos, tags=['extension', 'video'])
    rebulk.regex(r'\.'+build_or_pattern(torrent)+'$', exts=torrent, tags=['extension', 'torrent'])
    rebulk.regex(r'\.'+build_or_pattern(nzb)+'$', exts=nzb, tags=['extension', 'nzb'])

    rebulk.defaults(name='container',
                    validator=seps_surround,
                    formatter=lambda s: s.lower(),
                    conflict_solver=lambda match, other: match
                    if other.name in ['format',
                                      'video_codec'] or other.name == 'container' and 'extension' in other.tags
                    else '__default__')

    rebulk.string(*[sub for sub in subtitles if sub not in ['sub']], tags=['subtitle'])
    rebulk.string(*videos, tags=['video'])
    rebulk.string(*torrent, tags=['torrent'])
    rebulk.string(*nzb, tags=['nzb'])

    return rebulk
