#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uniform re module
"""
# pylint: disable-all
import os

REGEX_AVAILABLE = False
if os.environ.get('REGEX_DISABLED') in ["1", "true", "True", "Y"]:
    import re
else:
    try:
        import regex as re
        REGEX_AVAILABLE = True
    except ImportError:
        import re
