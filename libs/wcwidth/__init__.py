"""
Python 'wcwidth' module.

https://github.com/jquast/wcwidth
"""

__lazy_modules__ = [
    "wcwidth._clip",
    "wcwidth._wcswidth",
    "wcwidth._wcwidth",
    "wcwidth._width",
    "wcwidth.align",
    "wcwidth.bisearch",
    "wcwidth.escape_sequences",
    "wcwidth.grapheme",
    "wcwidth.hyperlink",
    "wcwidth.sgr_state",
    "wcwidth.table_ambiguous",
    "wcwidth.table_vs16",
    "wcwidth.table_wide",
    "wcwidth.table_zero",
    "wcwidth.text_sizing",
    "wcwidth.textwrap",
    "wcwidth.unicode_versions",
]

# std imports
import os
from functools import lru_cache

# local
from ._clip import clip
# re-export common and outermost functions & definitions, even a few private ones. Some are for
# convenience and others for legacy, only the items in '__all__' are documented as public API
from .bisearch import bisearch as _bisearch
from .grapheme import iter_graphemes_reverse, grapheme_boundary_before
from .textwrap import SequenceTextWrapper, wrap
from .hyperlink import Hyperlink, HyperlinkParams
from ._constants import list_term_programs
from .table_vs16 import VS16_NARROW_TO_WIDE
from .table_wide import WIDE_EASTASIAN
from .table_zero import ZERO_WIDTH
from .text_sizing import TextSizing, TextSizingParams
from .table_ambiguous import AMBIGUOUS_EASTASIAN
from .escape_sequences import iter_sequences
from .unicode_versions import list_versions

# Optional C extension 'wcwidth._wcwidth_c', wrapping the C11 libwcwidth
# library; the Python implementations below are used when it is unavailable.
HAS_C_EXTENSION = False
if not os.environ.get('WCWIDTH_PYTHON', ''):
    try:
        # local
        import wcwidth._wcwidth_c as _wcwidth_c  # noqa: F401  pylint:disable=unused-import,consider-using-from-import
    except ImportError:
        pass
    else:
        HAS_C_EXTENSION = True

# Import order matters for legacy API compatibility (releases before 0.7.0).
#
# The first release (0.1) put _bisearch, wcwidth, and wcswidth in a single 'wcwidth.py' file, and
# while the top-level function importing, 'from wcwidth import wcwidth' was always preferred, the
# deeper 'from wcwidth.wcwidth import wcwidth' was always possible.
#
# Pre-import the legacy submodule so sys.modules['wcwidth.wcwidth'] is populated during package
# initialization: without it, a later ``import wcwidth.wcwidth`` discovers the file on disk and
# rebinds that name from the function to the module object.  It must run before the 'wcwidth'
# binding below, because 'from . import wcwidth' loads the submodule while the package attribute
# is still unset.  The shim's own __lazy_modules__ defers its imports, so this costs one module.
from . import wcwidth as _wcwidth_module  # isort:skip pylint: disable=wrong-import-position

if HAS_C_EXTENSION:
    # local
    from ._wcwidth_c import ljust, rjust, width, center
    from ._wcwidth_c import wcwidth as _c_wcwidth
    from ._wcwidth_c import wcswidth, wcstwidth, propagate_sgr, iter_graphemes, strip_sequences
    wcwidth = lru_cache(maxsize=1024)(_c_wcwidth)
else:
    # local
    from .align import ljust, rjust, center
    from ._width import width
    from ._wcwidth import wcwidth
    from .grapheme import iter_graphemes
    from ._wcswidth import wcswidth, wcstwidth
    from .sgr_state import propagate_sgr
    from .escape_sequences import strip_sequences

from ._wcwidth import _wcmatch_version, _wcversion_value  # isort:skip  # pylint: disable=wrong-import-position


# The __all__ attribute defines the items exported from statement,
# 'from wcwidth import *', but also to say, "This is the public API".
__all__ = ('wcwidth', 'wcswidth', 'wcstwidth', 'width', 'iter_sequences', 'iter_graphemes',
           'iter_graphemes_reverse', 'grapheme_boundary_before',
           'ljust', 'rjust', 'center', 'wrap', 'clip', 'strip_sequences',
           'list_versions', 'list_term_programs', 'propagate_sgr',
           'Hyperlink', 'HyperlinkParams', 'TextSizing', 'TextSizingParams')

# Version is stamped by code generation (bin/update-tables.py) from pyproject.toml.
__version__ = '0.9.3'
