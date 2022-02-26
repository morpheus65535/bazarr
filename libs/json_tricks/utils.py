import gzip
import io
import warnings
from collections import OrderedDict
from functools import partial
from importlib import import_module
from sys import version_info, version


class JsonTricksDeprecation(UserWarning):
	""" Special deprecation warning because the built-in one is ignored by default """
	def __init__(self, msg):
		super(JsonTricksDeprecation, self).__init__(msg)


class hashodict(OrderedDict):
	"""
	This dictionary is hashable. It should NOT be mutated, or all kinds of weird
	bugs may appear. This is not enforced though, it's only used for encoding.
	"""
	def __hash__(self):
		return hash(frozenset(self.items()))


try:
	from inspect import signature
except ImportError:
	try:
		from inspect import getfullargspec
	except ImportError:
		from inspect import getargspec, isfunction
		def get_arg_names(callable):
			if type(callable) == partial and version_info[0] == 2:
				if not hasattr(get_arg_names, '__warned_partial_argspec'):
					get_arg_names.__warned_partial_argspec = True
					warnings.warn("'functools.partial' and 'inspect.getargspec' are not compatible in this Python version; "
						"ignoring the 'partial' wrapper when inspecting arguments of {}, which can lead to problems".format(callable))
				return set(getargspec(callable.func).args)
			if isfunction(callable):
				argspec = getargspec(callable)
			else:
				argspec = getargspec(callable.__call__)
			return set(argspec.args)
	else:
		#todo: this is not covered in test case (py 3+ uses `signature`, py2 `getfullargspec`); consider removing it
		def get_arg_names(callable):
			argspec = getfullargspec(callable)
			return set(argspec.args) | set(argspec.kwonlyargs)
else:
	def get_arg_names(callable):
		sig = signature(callable)
		return set(sig.parameters.keys())


def filtered_wrapper(encoder):
	"""
	Filter kwargs passed to encoder.
	"""
	if hasattr(encoder, "default"):
		encoder = encoder.default
	elif not hasattr(encoder, '__call__'):
		raise TypeError('`obj_encoder` {0:} does not have `default` method and is not callable'.format(enc))
	names = get_arg_names(encoder)

	def wrapper(*args, **kwargs):
		return encoder(*args, **{k: v for k, v in kwargs.items() if k in names})
	return wrapper


class NoNumpyException(Exception):
	""" Trying to use numpy features, but numpy cannot be found. """


class NoPandasException(Exception):
	""" Trying to use pandas features, but pandas cannot be found. """


class NoEnumException(Exception):
	""" Trying to use enum features, but enum cannot be found. """


class NoPathlibException(Exception):
	""" Trying to use pathlib features, but pathlib cannot be found. """


class ClassInstanceHookBase(object):
	def get_cls_from_instance_type(self, mod, name, cls_lookup_map):
		Cls = ValueError()
		if mod is None:
			try:
				Cls = getattr((__import__('__main__')), name)
			except (ImportError, AttributeError):
				if name not in cls_lookup_map:
					raise ImportError(('class {0:s} seems to have been exported from the main file, which means '
						'it has no module/import path set; you need to provide loads argument'
						'`cls_lookup_map={{"{0}": Class}}` to locate the class').format(name))
				Cls = cls_lookup_map[name]
		else:
			imp_err = None
			try:
				module = import_module('{0:}'.format(mod, name))
			except ImportError as err:
				imp_err = ('encountered import error "{0:}" while importing "{1:}" to decode a json file; perhaps '
					'it was encoded in a different environment where {1:}.{2:} was available').format(err, mod, name)
			else:
				if hasattr(module, name):
					Cls = getattr(module, name)
				else:
					imp_err = 'imported "{0:}" but could find "{1:}" inside while decoding a json file (found {2:})'.format(
						module, name, ', '.join(attr for attr in dir(module) if not attr.startswith('_')))
			if imp_err:
				Cls = cls_lookup_map.get(name, None)
				if Cls is None:
					raise ImportError('{}; add the class to `cls_lookup_map={{"{}": Class}}` argument'.format(imp_err, name))
		return Cls


def get_scalar_repr(npscalar):
	return hashodict((
		('__ndarray__', npscalar.item()),
		('dtype', str(npscalar.dtype)),
		('shape', ()),
	))


def encode_scalars_inplace(obj):
	"""
	Searches a data structure of lists, tuples and dicts for numpy scalars
	and replaces them by their dictionary representation, which can be loaded
	by json-tricks. This happens in-place (the object is changed, use a copy).
	"""
	from numpy import generic, complex64, complex128
	if isinstance(obj, (generic, complex64, complex128)):
		return get_scalar_repr(obj)
	if isinstance(obj, dict):
		for key, val in tuple(obj.items()):
			obj[key] = encode_scalars_inplace(val)
		return obj
	if isinstance(obj, list):
		for k, val in enumerate(obj):
			obj[k] = encode_scalars_inplace(val)
		return obj
	if isinstance(obj, (tuple, set)):
		return type(obj)(encode_scalars_inplace(val) for val in obj)
	return obj


def encode_intenums_inplace(obj):
	"""
	Searches a data structure of lists, tuples and dicts for IntEnum
	and replaces them by their dictionary representation, which can be loaded
	by json-tricks. This happens in-place (the object is changed, use a copy).
	"""
	from enum import IntEnum
	from json_tricks import encoders
	if isinstance(obj, IntEnum):
		return encoders.enum_instance_encode(obj)
	if isinstance(obj, dict):
		for key, val in obj.items():
			obj[key] = encode_intenums_inplace(val)
		return obj
	if isinstance(obj, list):
		for index, val in enumerate(obj):
			obj[index] = encode_intenums_inplace(val)
		return obj
	if isinstance(obj, (tuple, set)):
		return type(obj)(encode_intenums_inplace(val) for val in obj)
	return obj


def get_module_name_from_object(obj):
	mod = obj.__class__.__module__
	if mod == '__main__':
		mod = None
		warnings.warn(('class {0:} seems to have been defined in the main file; unfortunately this means'
			' that it\'s module/import path is unknown, so you might have to provide cls_lookup_map when '
			'decoding').format(obj.__class__))
	return mod


def nested_index(collection, indices):
	for i in indices:
		collection = collection[i]
	return collection


def dict_default(dictionary, key, default_value):
	if key not in dictionary:
		dictionary[key] = default_value


def gzip_compress(data, compresslevel):
	"""
	Do gzip compression, without the timestamp. Similar to gzip.compress, but without timestamp, and also before py3.2.
	"""
	buf = io.BytesIO()
	with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=compresslevel, mtime=0) as fh:
		fh.write(data)
	return buf.getvalue()


def gzip_decompress(data):
	"""
	Do gzip decompression, without the timestamp. Just like gzip.decompress, but that's py3.2+.
	"""
	with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
		return f.read()


is_py3 = (version[:2] == '3.')
str_type = str if is_py3 else (basestring, unicode,)

