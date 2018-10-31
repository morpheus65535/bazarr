
from gzip import GzipFile
from io import BytesIO
from json import loads as json_loads
from os import fsync
from sys import exc_info, version
from .utils import NoNumpyException  # keep 'unused' imports
from .comment import strip_comment_line_with_symbol, strip_comments  # keep 'unused' imports
from .encoders import TricksEncoder, json_date_time_encode, class_instance_encode, ClassInstanceEncoder, \
	json_complex_encode, json_set_encode, numeric_types_encode, numpy_encode, nonumpy_encode, NoNumpyEncoder, \
	nopandas_encode, pandas_encode  # keep 'unused' imports
from .decoders import DuplicateJsonKeyException, TricksPairHook, json_date_time_hook, ClassInstanceHook, \
	json_complex_hook, json_set_hook, numeric_types_hook, json_numpy_obj_hook, json_nonumpy_obj_hook, \
	nopandas_hook, pandas_hook  # keep 'unused' imports
from json import JSONEncoder


is_py3 = (version[:2] == '3.')
str_type = str if is_py3 else (basestring, unicode,)
ENCODING = 'UTF-8'


_cih_instance = ClassInstanceHook()
DEFAULT_ENCODERS = [json_date_time_encode, class_instance_encode, json_complex_encode, json_set_encode, numeric_types_encode,]
DEFAULT_HOOKS = [json_date_time_hook, _cih_instance, json_complex_hook, json_set_hook, numeric_types_hook,]

try:
	import numpy
except ImportError:
	DEFAULT_ENCODERS = [nonumpy_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [json_nonumpy_obj_hook,] + DEFAULT_HOOKS
else:
	# numpy encode needs to be before complex
	DEFAULT_ENCODERS = [numpy_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [json_numpy_obj_hook,] + DEFAULT_HOOKS

try:
	import pandas
except ImportError:
	DEFAULT_ENCODERS = [nopandas_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [nopandas_hook,] + DEFAULT_HOOKS
else:
	DEFAULT_ENCODERS = [pandas_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [pandas_hook,] + DEFAULT_HOOKS


DEFAULT_NONP_ENCODERS = [nonumpy_encode,] + DEFAULT_ENCODERS    # DEPRECATED
DEFAULT_NONP_HOOKS = [json_nonumpy_obj_hook,] + DEFAULT_HOOKS   # DEPRECATED


def dumps(obj, sort_keys=None, cls=TricksEncoder, obj_encoders=DEFAULT_ENCODERS, extra_obj_encoders=(),
		primitives=False, compression=None, allow_nan=False, conv_str_byte=False, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param obj: The Python object to convert.
	:param sort_keys: Keep this False if you want order to be preserved.
	:param cls: The json encoder class to use, defaults to NoNumpyEncoder which gives a warning for numpy arrays.
	:param obj_encoders: Iterable of encoders to use to convert arbitrary objects into json-able promitives.
	:param extra_obj_encoders: Like `obj_encoders` but on top of them: use this to add encoders without replacing defaults. Since v3.5 these happen before default encoders.
	:param allow_nan: Allow NaN and Infinity values, which is a (useful) violation of the JSON standard (default False).
	:param conv_str_byte: Try to automatically convert between strings and bytes (assuming utf-8) (default False).
	:return: The string containing the json-encoded version of obj.

	Other arguments are passed on to `cls`. Note that `sort_keys` should be false if you want to preserve order.
	"""
	if not hasattr(extra_obj_encoders, '__iter__'):
		raise TypeError('`extra_obj_encoders` should be a tuple in `json_tricks.dump(s)`')
	encoders = tuple(extra_obj_encoders) + tuple(obj_encoders)
	txt = cls(sort_keys=sort_keys, obj_encoders=encoders, allow_nan=allow_nan,
		primitives=primitives, **jsonkwargs).encode(obj)
	if not is_py3 and isinstance(txt, str):
		txt = unicode(txt, ENCODING)
	if not compression:
		return txt
	if compression is True:
		compression = 5
	txt = txt.encode(ENCODING)
	sh = BytesIO()
	with GzipFile(mode='wb', fileobj=sh, compresslevel=compression) as zh:
		zh.write(txt)
	gzstring = sh.getvalue()
	return gzstring


def dump(obj, fp, sort_keys=None, cls=TricksEncoder, obj_encoders=DEFAULT_ENCODERS, extra_obj_encoders=(),
		 primitives=False, compression=None, force_flush=False, allow_nan=False, conv_str_byte=False, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param fp: File handle or path to write to.
	:param compression: The gzip compression level, or None for no compression.
	:param force_flush: If True, flush the file handle used, when possibly also in the operating system (default False).
	
	The other arguments are identical to `dumps`.
	"""
	txt = dumps(obj, sort_keys=sort_keys, cls=cls, obj_encoders=obj_encoders, extra_obj_encoders=extra_obj_encoders,
		primitives=primitives, compression=compression, allow_nan=allow_nan, conv_str_byte=conv_str_byte, **jsonkwargs)
	if isinstance(fp, str_type):
		fh = open(fp, 'wb+')
	else:
		fh = fp
		if conv_str_byte:
			try:
				fh.write(b'')
			except TypeError:
				pass
				# if not isinstance(txt, str_type):
				# 	# Cannot write bytes, so must be in text mode, but we didn't get a text
				# 	if not compression:
				# 		txt = txt.decode(ENCODING)
			else:
				try:
					fh.write(u'')
				except TypeError:
					if isinstance(txt, str_type):
						txt = txt.encode(ENCODING)
	try:
		if 'b' not in getattr(fh, 'mode', 'b?') and not isinstance(txt, str_type) and compression:
			raise IOError('If compression is enabled, the file must be opened in binary mode.')
		try:
			fh.write(txt)
		except TypeError as err:
			err.args = (err.args[0] + '. A possible reason is that the file is not opened in binary mode; '
				'be sure to set file mode to something like "wb".',)
			raise
	finally:
		if force_flush:
			fh.flush()
			try:
				if fh.fileno() is not None:
					fsync(fh.fileno())
			except (ValueError,):
				pass
		if isinstance(fp, str_type):
			fh.close()
	return txt


def loads(string, preserve_order=True, ignore_comments=True, decompression=None, obj_pairs_hooks=DEFAULT_HOOKS,
		extra_obj_pairs_hooks=(), cls_lookup_map=None, allow_duplicates=True, conv_str_byte=False, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param string: The string containing a json encoded data structure.
	:param decode_cls_instances: True to attempt to decode class instances (requires the environment to be similar the the encoding one).
	:param preserve_order: Whether to preserve order by using OrderedDicts or not.
	:param ignore_comments: Remove comments (starting with # or //).
	:param decompression: True to use gzip decompression, False to use raw data, None to automatically determine (default). Assumes utf-8 encoding!
	:param obj_pairs_hooks: A list of dictionary hooks to apply.
	:param extra_obj_pairs_hooks: Like `obj_pairs_hooks` but on top of them: use this to add hooks without replacing defaults. Since v3.5 these happen before default hooks.
	:param cls_lookup_map: If set to a dict, for example ``globals()``, then classes encoded from __main__ are looked up this dict.
	:param allow_duplicates: If set to False, an error will be raised when loading a json-map that contains duplicate keys.
	:param parse_float: A function to parse strings to integers (e.g. Decimal). There is also `parse_int`.
	:param conv_str_byte: Try to automatically convert between strings and bytes (assuming utf-8) (default False).
	:return: The string containing the json-encoded version of obj.

	Other arguments are passed on to json_func.
	"""
	if not hasattr(extra_obj_pairs_hooks, '__iter__'):
		raise TypeError('`extra_obj_pairs_hooks` should be a tuple in `json_tricks.load(s)`')
	if decompression is None:
		decompression = string[:2] == b'\x1f\x8b'
	if decompression:
		with GzipFile(fileobj=BytesIO(string), mode='rb') as zh:
			string = zh.read()
			string = string.decode(ENCODING)
	if not isinstance(string, str_type):
		if conv_str_byte:
			string = string.decode(ENCODING)
		else:
			raise TypeError(('Cannot automatically encode object of type "{0:}" in `json_tricks.load(s)` since '
				'the encoding is not known. You should instead encode the bytes to a string and pass that '
				'string to `load(s)`, for example bytevar.encode("utf-8") if utf-8 is the encoding.').format(type(string)))
	if ignore_comments:
		string = strip_comments(string)
	obj_pairs_hooks = tuple(obj_pairs_hooks)
	_cih_instance.cls_lookup_map = cls_lookup_map or {}
	hooks = tuple(extra_obj_pairs_hooks) + obj_pairs_hooks
	hook = TricksPairHook(ordered=preserve_order, obj_pairs_hooks=hooks, allow_duplicates=allow_duplicates)
	return json_loads(string, object_pairs_hook=hook, **jsonkwargs)


def load(fp, preserve_order=True, ignore_comments=True, decompression=None, obj_pairs_hooks=DEFAULT_HOOKS,
		extra_obj_pairs_hooks=(), cls_lookup_map=None, allow_duplicates=True, conv_str_byte=False, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param fp: File handle or path to load from.

	The other arguments are identical to loads.
	"""
	try:
		if isinstance(fp, str_type):
			with open(fp, 'rb') as fh:
				string = fh.read()
		else:
			string = fp.read()
	except UnicodeDecodeError as err:
		# todo: not covered in tests, is it relevant?
		raise Exception('There was a problem decoding the file content. A possible reason is that the file is not ' +
			'opened  in binary mode; be sure to set file mode to something like "rb".').with_traceback(exc_info()[2])
	return loads(string, preserve_order=preserve_order, ignore_comments=ignore_comments, decompression=decompression,
		obj_pairs_hooks=obj_pairs_hooks, extra_obj_pairs_hooks=extra_obj_pairs_hooks, cls_lookup_map=cls_lookup_map,
		allow_duplicates=allow_duplicates, conv_str_byte=conv_str_byte, **jsonkwargs)


