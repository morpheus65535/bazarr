#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extracts as much information as possible from a video file.
"""
from . import monkeypatch as _monkeypatch

from .api import guessit, GuessItApi
from .options import ConfigurationException
from .rules.common.quantity import Size

from .__version__ import __version__

_monkeypatch.monkeypatch_rebulk()
