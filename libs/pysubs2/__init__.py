from .ssafile import SSAFile
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from . import time, formats, cli, exceptions
from .formats import whisper
from .exceptions import *  # noqa: F403
from .common import Color, Alignment, VERSION

__all__ = [
    "SSAFile",
    "SSAEvent",
    "SSAStyle",
    "time",
    "formats",
    "cli",
    "whisper",
    "exceptions",
    "Color",
    "Alignment",
    "VERSION",
    "load",
    "load_from_whisper",
    "make_time",
]

#: Alias for :meth:`SSAFile.load()`.
load = SSAFile.load

#: Alias for :meth:`pysubs2.whisper.load_from_whisper()`.
load_from_whisper = whisper.load_from_whisper

#: Alias for :meth:`pysubs2.time.make_time()`.
make_time = time.make_time

#: Alias for `pysubs2.common.VERSION`.
__version__ = VERSION
