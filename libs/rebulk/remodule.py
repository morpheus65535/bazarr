#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uniform re module
"""
# pylint: disable-all
import os
import logging

log = logging.getLogger(__name__).log

REGEX_ENABLED = False
if os.environ.get('REBULK_REGEX_ENABLED') in ["1", "true", "True", "Y"]:
    try:
        import regex as re
        REGEX_ENABLED = True
    except ImportError:
        log.warning('regex module is not available. Unset REBULK_REGEX_ENABLED environment variable, or install regex module to enabled it.')
        import re
else:
    import re
