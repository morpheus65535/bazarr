
try:
	from json import JSONDecodeError  # imported for convenience
except ImportError:
	""" Older versions of Python use ValueError, of which JSONDecodeError is a subclass; it's recommended to catch ValueError. """
from .utils import hashodict, NoEnumException, NoNumpyException, NoPandasException, get_scalar_repr, encode_intenums_inplace, encode_scalars_inplace
from .comment import strip_comment_line_with_symbol, strip_comments
from .encoders import TricksEncoder, json_date_time_encode, class_instance_encode, json_complex_encode, \
	numeric_types_encode, ClassInstanceEncoder, json_set_encode, pandas_encode, nopandas_encode, \
	numpy_encode, NumpyEncoder, nonumpy_encode, NoNumpyEncoder, fallback_ignore_unknown, pathlib_encode, \
	bytes_encode
from .decoders import DuplicateJsonKeyException, TricksPairHook, json_date_time_hook, json_complex_hook, \
	numeric_types_hook, ClassInstanceHook, json_set_hook, pandas_hook, nopandas_hook, json_numpy_obj_hook, \
	json_nonumpy_obj_hook, pathlib_hook, json_bytes_hook
from .nonp import dumps, dump, loads, load
from ._version import VERSION

__version__ = VERSION


try:
	# find_module takes just as long as importing, so no optimization possible
	import numpy
except ImportError:
	NUMPY_MODE = False
	# from .nonp import dumps, dump, loads, load, nonumpy_encode as numpy_encode, json_nonumpy_obj_hook as json_numpy_obj_hook
else:
	NUMPY_MODE = True
	# from .np import dumps, dump, loads, load, numpy_encode, NumpyEncoder, json_numpy_obj_hook
	# from .np_utils import encode_scalars_inplace


