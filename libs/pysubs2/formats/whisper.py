"""
Support for the OpenAI Whisper speech recognition library.

See https://github.com/openai/whisper

"""

from ..ssaevent import SSAEvent
from ..ssafile import SSAFile
from ..time import make_time
from typing import Union, List, Dict, Any


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
