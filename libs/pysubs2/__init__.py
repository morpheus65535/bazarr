from .ssafile import SSAFile
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from . import time, formats, cli, whisper
from .exceptions import *
from .common import Color, Alignment, VERSION

#: Alias for :meth:`SSAFile.load()`.
load = SSAFile.load

#: Alias for :meth:`pysubs2.whisper.load_from_whisper()`.
load_from_whisper = whisper.load_from_whisper

#: Alias for :meth:`pysubs2.time.make_time()`.
make_time = time.make_time

#: Alias for `pysubs2.common.VERSION`.
__version__ = VERSION
