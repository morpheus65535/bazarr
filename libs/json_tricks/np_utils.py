
"""
This file exists for backward compatibility reasons.
"""

from .utils import hashodict, get_scalar_repr, encode_scalars_inplace
from .utils import NoNumpyException
from . import np

# try:
# 	from numpy import generic, complex64, complex128
# except ImportError:
# 	raise NoNumpyException('Could not load numpy, maybe it is not installed?')


