
from datetime import datetime, date, time, timedelta
from fractions import Fraction
from logging import warning
from json import JSONEncoder
from sys import version
from decimal import Decimal
from .utils import hashodict, call_with_optional_kwargs, NoPandasException, NoNumpyException


class TricksEncoder(JSONEncoder):
	"""
	Encoder that runs any number of encoder functions or instances on
	the objects that are being encoded.

	Each encoder should make any appropriate changes and return an object,
	changed or not. This will be passes to the other encoders.
	"""
	def __init__(self, obj_encoders=None, silence_typeerror=False, primitives=False, **json_kwargs):
		"""
		:param obj_encoders: An iterable of functions or encoder instances to try.
		:param silence_typeerror: If set to True, ignore the TypeErrors that Encoder instances throw (default False).
		"""
		self.obj_encoders = []
		if obj_encoders:
			self.obj_encoders = list(obj_encoders)
		self.silence_typeerror = silence_typeerror
		self.primitives = primitives
		super(TricksEncoder, self).__init__(**json_kwargs)

	def default(self, obj, *args, **kwargs):
		"""
		This is the method of JSONEncoders that is called for each object; it calls
		all the encoders with the previous one's output used as input.

		It works for Encoder instances, but they are expected not to throw
		`TypeError` for unrecognized types (the super method does that by default).

		It never calls the `super` method so if there are non-primitive types
		left at the end, you'll get an encoding error.
		"""
		prev_id = id(obj)
		for encoder in self.obj_encoders:
			if hasattr(encoder, 'default'):
				#todo: write test for this scenario (maybe ClassInstanceEncoder?)
				try:
					obj = call_with_optional_kwargs(encoder.default, obj, primitives=self.primitives)
				except TypeError as err:
					if not self.silence_typeerror:
						raise
			elif hasattr(encoder, '__call__'):
				obj = call_with_optional_kwargs(encoder, obj, primitives=self.primitives)
			else:
				raise TypeError('`obj_encoder` {0:} does not have `default` method and is not callable'.format(encoder))
		if id(obj) == prev_id:
			#todo: test
			raise TypeError('Object of type {0:} could not be encoded by {1:} using encoders [{2:s}]'.format(
				type(obj), self.__class__.__name__, ', '.join(str(encoder) for encoder in self.obj_encoders)))
		return obj


def json_date_time_encode(obj, primitives=False):
	"""
	Encode a date, time, datetime or timedelta to a string of a json dictionary, including optional timezone.

	:param obj: date/time/datetime/timedelta obj
	:return: (dict) json primitives representation of date, time, datetime or timedelta
	"""
	if primitives and isinstance(obj, (date, time, datetime)):
		return obj.isoformat()
	if isinstance(obj, datetime):
		dct = hashodict([('__datetime__', None), ('year', obj.year), ('month', obj.month),
			('day', obj.day), ('hour', obj.hour), ('minute', obj.minute),
			('second', obj.second), ('microsecond', obj.microsecond)])
		if obj.tzinfo:
			dct['tzinfo'] = obj.tzinfo.zone
	elif isinstance(obj, date):
		dct = hashodict([('__date__', None), ('year', obj.year), ('month', obj.month), ('day', obj.day)])
	elif isinstance(obj, time):
		dct = hashodict([('__time__', None), ('hour', obj.hour), ('minute', obj.minute),
			('second', obj.second), ('microsecond', obj.microsecond)])
		if obj.tzinfo:
			dct['tzinfo'] = obj.tzinfo.zone
	elif isinstance(obj, timedelta):
		if primitives:
			return obj.total_seconds()
		else:
			dct = hashodict([('__timedelta__', None), ('days', obj.days), ('seconds', obj.seconds),
				('microseconds', obj.microseconds)])
	else:
		return obj
	for key, val in tuple(dct.items()):
		if not key.startswith('__') and not val:
			del dct[key]
	return dct


def class_instance_encode(obj, primitives=False):
	"""
	Encodes a class instance to json. Note that it can only be recovered if the environment allows the class to be
	imported in the same way.
	"""
	if isinstance(obj, list) or isinstance(obj, dict):
		return obj
	if hasattr(obj, '__class__') and hasattr(obj, '__dict__'):
		if not hasattr(obj, '__new__'):
			raise TypeError('class "{0:s}" does not have a __new__ method; '.format(obj.__class__) +
				('perhaps it is an old-style class not derived from `object`; add `object` as a base class to encode it.'
					if (version[:2] == '2.') else 'this should not happen in Python3'))
		try:
			obj.__new__(obj.__class__)
		except TypeError:
			raise TypeError(('instance "{0:}" of class "{1:}" cannot be encoded because it\'s __new__ method '
				'cannot be called, perhaps it requires extra parameters').format(obj, obj.__class__))
		mod = obj.__class__.__module__
		if mod == '__main__':
			mod = None
			warning(('class {0:} seems to have been defined in the main file; unfortunately this means'
				' that it\'s module/import path is unknown, so you might have to provide cls_lookup_map when '
				'decoding').format(obj.__class__))
		name = obj.__class__.__name__
		if hasattr(obj, '__json_encode__'):
			attrs = obj.__json_encode__()
		else:
			attrs = hashodict(obj.__dict__.items())
		if primitives:
			return attrs
		else:
			return hashodict((('__instance_type__', (mod, name)), ('attributes', attrs)))
	return obj


def json_complex_encode(obj, primitives=False):
	"""
	Encode a complex number as a json dictionary of it's real and imaginary part.

	:param obj: complex number, e.g. `2+1j`
	:return: (dict) json primitives representation of `obj`
	"""
	if isinstance(obj, complex):
		if primitives:
			return [obj.real, obj.imag]
		else:
			return hashodict(__complex__=[obj.real, obj.imag])
	return obj


def numeric_types_encode(obj, primitives=False):
	"""
	Encode Decimal and Fraction.
	
	:param primitives: Encode decimals and fractions as standard floats. You may lose precision. If you do this, you may need to enable `allow_nan` (decimals always allow NaNs but floats do not).
	"""
	if isinstance(obj, Decimal):
		if primitives:
			return float(obj)
		else:
			return {
				'__decimal__': str(obj.canonical()),
			}
	if isinstance(obj, Fraction):
		if primitives:
			return float(obj)
		else:
			return hashodict((
				('__fraction__', True),
				('numerator', obj.numerator),
				('denominator', obj.denominator),
			))
	return obj


class ClassInstanceEncoder(JSONEncoder):
	"""
	See `class_instance_encoder`.
	"""
	# Not covered in tests since `class_instance_encode` is recommended way.
	def __init__(self, obj, encode_cls_instances=True, **kwargs):
		self.encode_cls_instances = encode_cls_instances
		super(ClassInstanceEncoder, self).__init__(obj, **kwargs)

	def default(self, obj, *args, **kwargs):
		if self.encode_cls_instances:
			obj = class_instance_encode(obj)
		return super(ClassInstanceEncoder, self).default(obj, *args, **kwargs)


def json_set_encode(obj, primitives=False):
	"""
	Encode python sets as dictionary with key __set__ and a list of the values.

	Try to sort the set to get a consistent json representation, use arbitrary order if the data is not ordinal.
	"""
	if isinstance(obj, set):
		try:
			repr = sorted(obj)
		except Exception:
			repr = list(obj)
		if primitives:
			return repr
		else:
			return hashodict(__set__=repr)
	return obj


def pandas_encode(obj, primitives=False):
	from pandas import DataFrame, Series
	if isinstance(obj, (DataFrame, Series)):
		#todo: this is experimental
		if not getattr(pandas_encode, '_warned', False):
			pandas_encode._warned = True
			warning('Pandas dumping support in json-tricks is experimental and may change in future versions.')
	if isinstance(obj, DataFrame):
		repr = hashodict()
		if not primitives:
			repr['__pandas_dataframe__'] = hashodict((
				('column_order', tuple(obj.columns.values)),
				('types', tuple(str(dt) for dt in obj.dtypes)),
			))
		repr['index'] = tuple(obj.index.values)
		for k, name in enumerate(obj.columns.values):
			repr[name] = tuple(obj.ix[:, k].values)
		return repr
	if isinstance(obj, Series):
		repr = hashodict()
		if not primitives:
			repr['__pandas_series__'] = hashodict((
				('name', str(obj.name)),
				('type', str(obj.dtype)),
			))
		repr['index'] = tuple(obj.index.values)
		repr['data'] = tuple(obj.values)
		return repr
	return obj


def nopandas_encode(obj):
	if ('DataFrame' in getattr(obj.__class__, '__name__', '') or 'Series' in getattr(obj.__class__, '__name__', '')) \
			and 'pandas.' in getattr(obj.__class__, '__module__', ''):
		raise NoPandasException(('Trying to encode an object of type {0:} which appears to be '
			'a numpy array, but numpy support is not enabled, perhaps it is not installed.').format(type(obj)))
	return obj


def numpy_encode(obj, primitives=False):
	"""
	Encodes numpy `ndarray`s as lists with meta data.
	
	Encodes numpy scalar types as Python equivalents. Special encoding is not possible,
	because int64 (in py2) and float64 (in py2 and py3) are subclasses of primitives,
	which never reach the encoder.
	
	:param primitives: If True, arrays are serialized as (nested) lists without meta info.
	"""
	from numpy import ndarray, generic
	if isinstance(obj, ndarray):
		if primitives:
			return obj.tolist()
		else:
			dct = hashodict((
				('__ndarray__', obj.tolist()),
				('dtype', str(obj.dtype)),
				('shape', obj.shape),
			))
			if len(obj.shape) > 1:
				dct['Corder'] = obj.flags['C_CONTIGUOUS']
			return dct
	elif isinstance(obj, generic):
		if NumpyEncoder.SHOW_SCALAR_WARNING:
			NumpyEncoder.SHOW_SCALAR_WARNING = False
			warning('json-tricks: numpy scalar serialization is experimental and may work differently in future versions')
		return obj.item()
	return obj


class NumpyEncoder(ClassInstanceEncoder):
	"""
	JSON encoder for numpy arrays.
	"""
	SHOW_SCALAR_WARNING = True  # show a warning that numpy scalar serialization is experimental
	
	def default(self, obj, *args, **kwargs):
		"""
		If input object is a ndarray it will be converted into a dict holding
		data type, shape and the data. The object can be restored using json_numpy_obj_hook.
		"""
		warning('`NumpyEncoder` is deprecated, use `numpy_encode`')  #todo
		obj = numpy_encode(obj)
		return super(NumpyEncoder, self).default(obj, *args, **kwargs)


def nonumpy_encode(obj):
	"""
	Raises an error for numpy arrays.
	"""
	if 'ndarray' in getattr(obj.__class__, '__name__', '') and 'numpy.' in getattr(obj.__class__, '__module__', ''):
		raise NoNumpyException(('Trying to encode an object of type {0:} which appears to be '
			'a pandas data stucture, but pandas support is not enabled, perhaps it is not installed.').format(type(obj)))
	return obj


class NoNumpyEncoder(JSONEncoder):
	"""
	See `nonumpy_encode`.
	"""
	def default(self, obj, *args, **kwargs):
		warning('`NoNumpyEncoder` is deprecated, use `nonumpy_encode`')  #todo
		obj = nonumpy_encode(obj)
		return super(NoNumpyEncoder, self).default(obj, *args, **kwargs)


