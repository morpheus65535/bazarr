#!/usr/bin/env python
"""
Uniform re module
"""

from __future__ import annotations

import logging
import os
import re as _stdlib_re
from typing import Any

__all__ = ["REGEX_ENABLED", "re"]

log = logging.getLogger(__name__).log

# Default to the standard library `re`; switch to the third-party `regex` module
# when REBULK_REGEX_ENABLED is set and `regex` is importable.
re: Any = _stdlib_re
REGEX_ENABLED = False
if os.environ.get("REBULK_REGEX_ENABLED") in ["1", "true", "True", "Y"]:
    try:
        import regex as _regex

        re = _regex
        REGEX_ENABLED = True
    except ImportError:
        log(
            logging.WARNING,
            "regex module is not available. Unset REBULK_REGEX_ENABLED environment variable, "
            "or install regex module to enable it.",
        )
