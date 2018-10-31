
from collections import OrderedDict


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
		from inspect import getargspec
		def get_arg_names(callable):
			argspec = getargspec(callable)
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


def call_with_optional_kwargs(callable, *args, **optional_kwargs):
	accepted_kwargs = get_arg_names(callable)
	use_kwargs = {}
	for key, val in optional_kwargs.items():
		if key in accepted_kwargs:
			use_kwargs[key] = val
	return callable(*args, **use_kwargs)


class NoNumpyException(Exception):
	""" Trying to use numpy features, but numpy cannot be found. """


class NoPandasException(Exception):
	""" Trying to use pandas features, but pandas cannot be found. """


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


