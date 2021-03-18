# -*- coding: utf-8 -*-
__title__ = 'enzyme'
__version__ = '0.4.1'
__author__ = 'Antoine Bertin'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2013 Antoine Bertin'

import logging
from .exceptions import *
from .mkv import *


logging.getLogger(__name__).addHandler(logging.NullHandler())
