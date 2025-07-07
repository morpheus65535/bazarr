# coding=utf-8

from .subtitles import api_ns_subtitles
from .subtitles_info import api_ns_subtitles_info
from .subtitles_contents import api_ns_subtitle_contents


api_ns_list_subtitles = [
    api_ns_subtitles,
    api_ns_subtitles_info,
    api_ns_subtitle_contents
]
