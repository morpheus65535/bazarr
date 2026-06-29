"""Backward-compatibility stub for ``chardet.universaldetector``.

chardet 6.x exposed :class:`UniversalDetector` via this module path.
In chardet 7+ the canonical location is :mod:`chardet.detector`, but this
stub keeps ``from chardet.universaldetector import UniversalDetector``
working for existing callers.

.. deprecated:: 7.0
    Import from :mod:`chardet` or :mod:`chardet.detector` instead.
"""

from __future__ import annotations

import warnings

from chardet.detector import UniversalDetector

warnings.warn(
    "chardet.universaldetector is deprecated, "
    "import UniversalDetector from chardet or chardet.detector instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["UniversalDetector"]
