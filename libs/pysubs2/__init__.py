from .ssafile import SSAFile
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from . import time, formats, cli
from .exceptions import *
from .common import Color, VERSION

#: Alias for :meth:`SSAFile.load()`.
load = SSAFile.load

#: Alias for :meth:`pysubs2.time.make_time()`.
make_time = time.make_time
