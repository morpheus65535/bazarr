import re
from typing import List, Sequence, Optional, TextIO, Any

from ..ssaevent import SSAEvent
from .subrip import SubripFormat
from ..time import make_time
from ..ssafile import SSAFile


class WebVTTFormat(SubripFormat):
    """
    Web Video Text Tracks (WebVTT) subtitle format implementation

    Currently, this shares implementation with :class:`pysubs2.formats.subrip.SubripFormat`.
    """
    TIMESTAMP = re.compile(r"(\d{0,4}:)?(\d{2}):(\d{2})\.(\d{2,3})")

    @staticmethod
    def ms_to_timestamp(ms: int) -> str:
        result = SubripFormat.ms_to_timestamp(ms)
        return result.replace(',', '.')

    @staticmethod
    def timestamp_to_ms(groups: Sequence[str]) -> int:
        _h, _m, _s, _ms = groups
        if not _h:
            h = 0
        else:
            h = int(_h.strip(":"))
        m, s, ms = map(int, (_m, _s, _ms))
        return make_time(h=h, m=m, s=s, ms=ms)

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if text.lstrip().startswith("WEBVTT"):
            return "vtt"
        else:
            return None

    @classmethod
    def to_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:  # type: ignore[override]
        """
        See :meth:`pysubs2.formats.SubripFormat.to_file()`, additional SRT options are supported by VTT as well
        """
        print("WEBVTT\n", file=fp)
        return super(WebVTTFormat, cls).to_file(
            subs=subs, fp=fp, format_=format_, **kwargs)

    @classmethod
    def _get_visible_lines(cls, subs: "SSAFile") -> List[SSAEvent]:
        visible_lines = super()._get_visible_lines(subs)
        visible_lines.sort(key=lambda e: e.start)
        return visible_lines
