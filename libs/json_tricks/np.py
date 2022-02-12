
"""
This file exists for backward compatibility reasons.
"""

import warnings
from .nonp import NoNumpyException, DEFAULT_ENCODERS, DEFAULT_HOOKS, dumps, dump, loads, load  # keep 'unused' imports
from .utils import hashodict, NoPandasException, JsonTricksDeprecation
from .comment import strip_comment_line_with_symbol, strip_comments  # keep 'unused' imports
from .encoders import TricksEncoder, json_date_time_encode, class_instance_encode, ClassInstanceEncoder, \
	numpy_encode, NumpyEncoder # keep 'unused' imports
from .decoders import DuplicateJsonKeyException, TricksPairHook, json_date_time_hook, ClassInstanceHook, \
	json_complex_hook, json_set_hook, json_numpy_obj_hook  # keep 'unused' imports

try:
	import numpy
except ImportError:
	raise NoNumpyException('Could not load numpy, maybe it is not installed? If you do not want to use numpy encoding '
		'or decoding, you can import the functions from json_tricks.nonp instead, which do not need numpy.')


warnings.warn('`json_tricks.np` is deprecated, you can import directly from `json_tricks`', JsonTricksDeprecation)


DEFAULT_NP_ENCODERS = [numpy_encode,] + DEFAULT_ENCODERS    # DEPRECATED
DEFAULT_NP_HOOKS = [json_numpy_obj_hook,] + DEFAULT_HOOKS   # DEPRECATED


