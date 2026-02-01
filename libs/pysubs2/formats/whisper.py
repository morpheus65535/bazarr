"""
Support for the OpenAI Whisper speech recognition library.

See https://github.com/openai/whisper

"""
from .base import FormatBase
from ..ssaevent import SSAEvent
from ..ssafile import SSAFile
from ..time import make_time, timestamp_to_ms
from typing import Union, List, Dict, Any, Optional, Sequence, TextIO
import re


def load_from_whisper(result_or_segments: Union[Dict[str, Any], List[Dict[str, Any]]]) -> SSAFile:
    """
    Load subtitle file from OpenAI Whisper transcript

    Example:
        >>> import whisper
        >>> import pysubs2
        >>> model = whisper.load_model("base")
        >>> result = model.transcribe("audio.mp3")
        >>> subs = pysubs2.load_from_whisper(result)
        >>> subs.save("audio.ass")

    See also:
        https://github.com/openai/whisper

    Arguments:
        result_or_segments: Either a dict with a ``"segments"`` key
            that holds a list of segment dicts, or the segment list-of-dicts.
            Each segment is a dict with keys ``"start"``, ``"end"`` (float, timestamps
            in seconds) and ``"text"`` (str with caption text).

    Returns:
        :class:`pysubs2.SSAFile`

    """
    if isinstance(result_or_segments, dict):
        segments = result_or_segments["segments"]
    elif isinstance(result_or_segments, list):
        segments = result_or_segments
    else:
        raise TypeError("Expected either a dict with 'segments' key, or a list of segments")

    subs = SSAFile()
    for segment in segments:
        event = SSAEvent(start=make_time(s=segment["start"]), end=make_time(s=segment["end"]))
        event.plaintext = segment["text"].strip()
        subs.append(event)

    return subs


class WhisperJAXFormat(FormatBase):
    """
    Parser for Whisper JAX transcription, one event per line, eg. ``[00:02.880 -> 00:07.240]  transcribed text``

    """
    TIMESTAMP = re.compile(r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[.](\d{3})")
    LINE = re.compile(r"\[([^]]+) -> ([^]]+)] (.*)")

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        for line in text.lstrip().splitlines():
            if cls.parse_line(line):
                return "whisper_jax"
            else:
                return None

        return None

    @classmethod
    def parse_line(cls, line: str) -> Optional[SSAEvent]:
        m = cls.LINE.match(line)
        if m is None:
            return None

        m_start = cls.TIMESTAMP.fullmatch(m.group(1))
        m_end = cls.TIMESTAMP.fullmatch(m.group(2))
        text = m.group(3).strip()

        if m_start is None or m_end is None:
            return None

        start_ms = cls.timestamp_to_ms(m_start.groups())
        end_ms = cls.timestamp_to_ms(m_end.groups())

        return SSAEvent(start=start_ms, end=end_ms, text=text)

    @staticmethod
    def timestamp_to_ms(groups: Sequence[str]) -> int:
        return timestamp_to_ms([x or "0" for x in groups])

    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        See :meth:`pysubs2.formats.FormatBase.from_file()`
        """
        for line in fp.readlines():
            line = line.strip()
            e = cls.parse_line(line)
            if e is not None:
                subs.append(e)
