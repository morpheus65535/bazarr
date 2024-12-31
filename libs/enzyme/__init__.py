__title__ = "enzyme"
__version__ = "0.5.2"
__author__ = "Antoine Bertin"
__license__ = "MIT"
__copyright__ = "Copyright 2013 Antoine Bertin"

import logging
from .exceptions import *
from .mkv import *


logging.getLogger(__name__).addHandler(logging.NullHandler())
