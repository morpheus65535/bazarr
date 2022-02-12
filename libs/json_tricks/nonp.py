import warnings
from json import loads as json_loads
from os import fsync
from sys import exc_info

from json_tricks.utils import is_py3, dict_default, gzip_compress, gzip_decompress, JsonTricksDeprecation
from .utils import str_type, NoNumpyException  # keep 'unused' imports
from .comment import strip_comments  # keep 'unused' imports
#TODO @mark: imports removed?
from .encoders import TricksEncoder, json_date_time_encode, \
	class_instance_encode, json_complex_encode, json_set_encode, numeric_types_encode, numpy_encode, \
	nonumpy_encode, nopandas_encode, pandas_encode, noenum_instance_encode, \
	enum_instance_encode, pathlib_encode # keep 'unused' imports
from .decoders import TricksPairHook, \
	json_date_time_hook, ClassInstanceHook, \
	json_complex_hook, json_set_hook, numeric_types_hook, json_numpy_obj_hook, \
	json_nonumpy_obj_hook, \
	nopandas_hook, pandas_hook, EnumInstanceHook, \
	noenum_hook, pathlib_hook, nopathlib_hook  # keep 'unused' imports


ENCODING = 'UTF-8'


_cih_instance = ClassInstanceHook()
_eih_instance = EnumInstanceHook()
DEFAULT_ENCODERS = [json_date_time_encode, json_complex_encode, json_set_encode,
					numeric_types_encode, class_instance_encode, ]
DEFAULT_HOOKS = [json_date_time_hook, json_complex_hook, json_set_hook,
				numeric_types_hook, _cih_instance, ]


#TODO @mark: add properties to all built-in encoders (for speed - but it should keep working without)
try:
	import enum
except ImportError:
	DEFAULT_ENCODERS = [noenum_instance_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [noenum_hook,] + DEFAULT_HOOKS
else:
	DEFAULT_ENCODERS = [enum_instance_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [_eih_instance,] + DEFAULT_HOOKS

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

try:
	import pathlib
except:
	# No need to include a "nopathlib_encode" hook since we would not encounter
	# the Path object if pathlib isn't available. However, we *could* encounter
	# a serialized Path object (produced by a version of Python with pathlib).
	DEFAULT_HOOKS = [nopathlib_hook,] + DEFAULT_HOOKS
else:
	DEFAULT_ENCODERS = [pathlib_encode,] + DEFAULT_ENCODERS
	DEFAULT_HOOKS = [pathlib_hook,] + DEFAULT_HOOKS


DEFAULT_NONP_ENCODERS = [nonumpy_encode,] + DEFAULT_ENCODERS		# DEPRECATED
DEFAULT_NONP_HOOKS = [json_nonumpy_obj_hook,] + DEFAULT_HOOKS		# DEPRECATED


def dumps(obj, sort_keys=None, cls=None, obj_encoders=DEFAULT_ENCODERS, extra_obj_encoders=(),
		primitives=False, compression=None, allow_nan=False, conv_str_byte=False, fallback_encoders=(),
		properties=None, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param obj: The Python object to convert.
	:param sort_keys: Keep this False if you want order to be preserved.
	:param cls: The json encoder class to use, defaults to NoNumpyEncoder which gives a warning for numpy arrays.
	:param obj_encoders: Iterable of encoders to use to convert arbitrary objects into json-able promitives.
	:param extra_obj_encoders: Like `obj_encoders` but on top of them: use this to add encoders without replacing defaults. Since v3.5 these happen before default encoders.
	:param fallback_encoders: These are extra `obj_encoders` that 1) are ran after all others and 2) only run if the object hasn't yet been changed.
	:param allow_nan: Allow NaN and Infinity values, which is a (useful) violation of the JSON standard (default False).
	:param conv_str_byte: Try to automatically convert between strings and bytes (assuming utf-8) (default False).
	:param properties: A dictionary of properties that is passed to each encoder that will accept it.
	:return: The string containing the json-encoded version of obj.

	Other arguments are passed on to `cls`. Note that `sort_keys` should be false if you want to preserve order.
	"""
	if not hasattr(extra_obj_encoders, '__iter__'):
		raise TypeError('`extra_obj_encoders` should be a tuple in `json_tricks.dump(s)`')
	encoders = tuple(extra_obj_encoders) + tuple(obj_encoders)
	properties = properties or {}
	dict_default(properties, 'primitives', primitives)
	dict_default(properties, 'compression', compression)
	dict_default(properties, 'allow_nan', allow_nan)
	if cls is None:
		cls = TricksEncoder
	txt = cls(sort_keys=sort_keys, obj_encoders=encoders, allow_nan=allow_nan,
		primitives=primitives, fallback_encoders=fallback_encoders,
	  	properties=properties, **jsonkwargs).encode(obj)
	if not is_py3 and isinstance(txt, str):
		txt = unicode(txt, ENCODING)
	if not compression:
		return txt
	if compression is True:
		compression = 5
	txt = txt.encode(ENCODING)
	gzstring = gzip_compress(txt, compresslevel=compression)
	return gzstring


def dump(obj, fp, sort_keys=None, cls=None, obj_encoders=DEFAULT_ENCODERS, extra_obj_encoders=(),
		primitives=False, compression=None, force_flush=False, allow_nan=False, conv_str_byte=False,
		fallback_encoders=(), properties=None, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param fp: File handle or path to write to.
	:param compression: The gzip compression level, or None for no compression.
	:param force_flush: If True, flush the file handle used, when possibly also in the operating system (default False).

	The other arguments are identical to `dumps`.
	"""
	if (isinstance(obj, str_type) or hasattr(obj, 'write')) and isinstance(fp, (list, dict)):
		raise ValueError('json-tricks dump arguments are in the wrong order: provide the data to be serialized before file handle')
	txt = dumps(obj, sort_keys=sort_keys, cls=cls, obj_encoders=obj_encoders, extra_obj_encoders=extra_obj_encoders,
		primitives=primitives, compression=compression, allow_nan=allow_nan, conv_str_byte=conv_str_byte,
		fallback_encoders=fallback_encoders, properties=properties, **jsonkwargs)
	if isinstance(fp, str_type):
		if compression:
			fh = open(fp, 'wb+')
		else:
			fh = open(fp, 'w+')
	else:
		fh = fp
		if conv_str_byte:
			try:
				fh.write(b'')
			except TypeError:
				pass
				# if not isinstance(txt, str_type):
				#		# Cannot write bytes, so must be in text mode, but we didn't get a text
				#		if not compression:
				#			txt = txt.decode(ENCODING)
			else:
				try:
					fh.write(u'')
				except TypeError:
					if isinstance(txt, str_type):
						txt = txt.encode(ENCODING)
	try:
		if compression and 'b' not in getattr(fh, 'mode', 'b?') and not isinstance(txt, str_type):
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


def loads(string, preserve_order=True, ignore_comments=None, decompression=None, obj_pairs_hooks=DEFAULT_HOOKS,
		extra_obj_pairs_hooks=(), cls_lookup_map=None, allow_duplicates=True, conv_str_byte=False,
		properties=None, **jsonkwargs):
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
		decompression = isinstance(string, bytes) and string[:2] == b'\x1f\x8b'
	if decompression:
		string = gzip_decompress(string).decode(ENCODING)
	if not isinstance(string, str_type):
		if conv_str_byte:
			string = string.decode(ENCODING)
		else:
			raise TypeError(('The input was of non-string type "{0:}" in `json_tricks.load(s)`. '
				'Bytes cannot be automatically decoding since the encoding is not known. Recommended '
				'way is to instead encode the bytes to a string and pass that string to `load(s)`, '
				'for example bytevar.encode("utf-8") if utf-8 is the encoding. Alternatively you can '
				'force an attempt by passing conv_str_byte=True, but this may cause decoding issues.')
					.format(type(string)))
	if ignore_comments or ignore_comments is None:
		new_string = strip_comments(string)
		if ignore_comments is None and not getattr(loads, '_ignore_comments_warned', False) and string != new_string:
			warnings.warn('`json_tricks.load(s)` stripped some comments, but `ignore_comments` was '
				'not passed; in the next major release, the behaviour when `ignore_comments` is not '
				'passed will change; it is recommended to explicitly pass `ignore_comments=True` if '
				'you want to strip comments; see https://github.com/mverleg/pyjson_tricks/issues/74',
				JsonTricksDeprecation)
			loads._ignore_comments_warned = True
		string = new_string
	properties = properties or {}
	dict_default(properties, 'preserve_order', preserve_order)
	dict_default(properties, 'ignore_comments', ignore_comments)
	dict_default(properties, 'decompression', decompression)
	dict_default(properties, 'cls_lookup_map', cls_lookup_map)
	dict_default(properties, 'allow_duplicates', allow_duplicates)
	hooks = tuple(extra_obj_pairs_hooks) + tuple(obj_pairs_hooks)
	hook = TricksPairHook(ordered=preserve_order, obj_pairs_hooks=hooks, allow_duplicates=allow_duplicates, properties=properties)
	return json_loads(string, object_pairs_hook=hook, **jsonkwargs)


def load(fp, preserve_order=True, ignore_comments=None, decompression=None, obj_pairs_hooks=DEFAULT_HOOKS,
		extra_obj_pairs_hooks=(), cls_lookup_map=None, allow_duplicates=True, conv_str_byte=False,
		properties=None, **jsonkwargs):
	"""
	Convert a nested data structure to a json string.

	:param fp: File handle or path to load from.

	The other arguments are identical to loads.
	"""
	try:
		if isinstance(fp, str_type):
			if decompression is not None:
				open_binary = bool(decompression)
			else:
				with open(fp, 'rb') as fh:
					# This attempts to detect gzip mode; gzip should always
					# have this header, and text json can't have it.
					open_binary = (fh.read(2) == b'\x1f\x8b')
			with open(fp, 'rb' if open_binary else 'r') as fh:
				string = fh.read()
		else:
			string = fp.read()
	except UnicodeDecodeError as err:
		# todo: not covered in tests, is it relevant?
		raise Exception('There was a problem decoding the file content. A possible reason is that the file is not ' +
			'opened  in binary mode; be sure to set file mode to something like "rb".').with_traceback(exc_info()[2])
	return loads(string, preserve_order=preserve_order, ignore_comments=ignore_comments, decompression=decompression,
		obj_pairs_hooks=obj_pairs_hooks, extra_obj_pairs_hooks=extra_obj_pairs_hooks, cls_lookup_map=cls_lookup_map,
		allow_duplicates=allow_duplicates, conv_str_byte=conv_str_byte, properties=properties, **jsonkwargs)


