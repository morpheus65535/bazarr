import warnings
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from fractions import Fraction
from functools import wraps
from json import JSONEncoder
from sys import version, stderr

from .utils import hashodict, get_module_name_from_object, NoEnumException, NoPandasException, \
	NoNumpyException, str_type, JsonTricksDeprecation, gzip_compress, filtered_wrapper


def _fallback_wrapper(encoder):
	"""
	This decorator makes an encoder run only if the current object hasn't been changed yet.
	(Changed-ness is checked with is_changed which is based on identity with `id`).
	"""
	@wraps(encoder)
	def fallback_encoder(obj, is_changed, **kwargs):
		if is_changed:
			return obj
		return encoder(obj, is_changed=is_changed, **kwargs)
	return fallback_encoder


def fallback_ignore_unknown(obj, is_changed=None, fallback_value=None):
	"""
	This encoder returns None if the object isn't changed by another encoder and isn't a primitive.
	"""
	if is_changed:
		return obj
	if obj is None or isinstance(obj, (int, float, str_type, bool, list, dict)):
		return obj
	return fallback_value


class TricksEncoder(JSONEncoder):
	"""
	Encoder that runs any number of encoder functions or instances on
	the objects that are being encoded.

	Each encoder should make any appropriate changes and return an object,
	changed or not. This will be passes to the other encoders.
	"""
	def __init__(self, obj_encoders=None, silence_typeerror=False, primitives=False, fallback_encoders=(), properties=None, **json_kwargs):
		"""
		:param obj_encoders: An iterable of functions or encoder instances to try.
		:param silence_typeerror: DEPRECATED - If set to True, ignore the TypeErrors that Encoder instances throw (default False).
		"""
		if silence_typeerror and not getattr(TricksEncoder, '_deprecated_silence_typeerror'):
			TricksEncoder._deprecated_silence_typeerror = True
			stderr.write('TricksEncoder.silence_typeerror is deprecated and may be removed in a future version\n')
		self.obj_encoders = []
		if obj_encoders:
			self.obj_encoders = list(obj_encoders)
		self.obj_encoders.extend(_fallback_wrapper(encoder) for encoder in list(fallback_encoders))
		self.obj_encoders = [filtered_wrapper(enc) for enc in self.obj_encoders]
		self.silence_typeerror = silence_typeerror
		self.properties = properties
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
			obj = encoder(obj, primitives=self.primitives, is_changed=id(obj) != prev_id, properties=self.properties)
		if id(obj) == prev_id:
			raise TypeError(('Object of type {0:} could not be encoded by {1:} using encoders [{2:s}]. '
				'You can add an encoders for this type using `extra_obj_encoders`. If you want to \'skip\' this '
				'object, consider using `fallback_encoders` like `str` or `lambda o: None`.').format(
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


def enum_instance_encode(obj, primitives=False, with_enum_value=False):
	"""Encodes an enum instance to json. Note that it can only be recovered if the environment allows the enum to be
	imported in the same way.
	:param primitives: If true, encode the enum values as primitive (more readable, but cannot be restored automatically).
	:param with_enum_value: If true, the value of the enum is also exported (it is not used during import, as it should be constant).
	"""
	from enum import Enum
	if not isinstance(obj, Enum):
		return obj
	if primitives:
		return {obj.name: obj.value}
	mod = get_module_name_from_object(obj)
	representation = dict(
		__enum__=dict(
			# Don't use __instance_type__ here since enums members cannot be created with __new__
			# Ie we can't rely on class deserialization to read them.
			__enum_instance_type__=[mod, type(obj).__name__],
			name=obj.name,
		),
	)
	if with_enum_value:
		representation['__enum__']['value'] = obj.value
	return representation


def noenum_instance_encode(obj, primitives=False):
	if type(obj.__class__).__name__ == 'EnumMeta':
		raise NoEnumException(('Trying to encode an object of type {0:} which appears to be '
			'an enum, but enum support is not enabled, perhaps it is not installed.').format(type(obj)))
	return obj


def class_instance_encode(obj, primitives=False):
	"""
	Encodes a class instance to json. Note that it can only be recovered if the environment allows the class to be
	imported in the same way.
	"""
	if isinstance(obj, list) or isinstance(obj, dict):
		return obj
	if hasattr(obj, '__class__') and (hasattr(obj, '__dict__') or hasattr(obj, '__slots__')):
		if not hasattr(obj, '__new__'):
			raise TypeError('class "{0:s}" does not have a __new__ method; '.format(obj.__class__) +
				('perhaps it is an old-style class not derived from `object`; add `object` as a base class to encode it.'
					if (version[:2] == '2.') else 'this should not happen in Python3'))
		if type(obj) == type(lambda: 0):
			raise TypeError('instance "{0:}" of class "{1:}" cannot be encoded because it appears to be a lambda or function.'
				.format(obj, obj.__class__))
		try:
			obj.__new__(obj.__class__)
		except TypeError:
			raise TypeError(('instance "{0:}" of class "{1:}" cannot be encoded, perhaps because it\'s __new__ method '
				'cannot be called because it requires extra parameters').format(obj, obj.__class__))
		mod = get_module_name_from_object(obj)
		if mod == 'threading':
			# In Python2, threading objects get serialized, which is probably unsafe
			return obj
		name = obj.__class__.__name__
		if hasattr(obj, '__json_encode__'):
			attrs = obj.__json_encode__()
			if primitives:
				return attrs
			else:
				return hashodict((('__instance_type__', (mod, name)), ('attributes', attrs)))
		dct = hashodict([('__instance_type__',(mod, name))])
		if hasattr(obj, '__slots__'):
			slots = obj.__slots__
			if isinstance(slots, str):
				slots = [slots]
			slots = list(item for item in slots if item != '__dict__')
			dct['slots'] = hashodict([])
			for s in slots:
				dct['slots'][s] = getattr(obj, s)
		if hasattr(obj, '__dict__'):
			dct['attributes'] = hashodict(obj.__dict__)
		if primitives:
			attrs = dct.get('attributes',{})
			attrs.update(dct.get('slots',{}))
			return attrs
		else:
			return dct
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


def pathlib_encode(obj, primitives=False):
    from pathlib import Path
    if not isinstance(obj, Path):
        return obj

    if primitives:
        return str(obj)

    return {'__pathlib__': str(obj)}


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
	if isinstance(obj, DataFrame):
		repr = hashodict()
		if not primitives:
			repr['__pandas_dataframe__'] = hashodict((
				('column_order', tuple(obj.columns.values)),
				('types', tuple(str(dt) for dt in obj.dtypes)),
			))
		repr['index'] = tuple(obj.index.values)
		for k, name in enumerate(obj.columns.values):
			repr[name] = tuple(obj.iloc[:, k].values)
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


def numpy_encode(obj, primitives=False, properties=None):
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
			properties = properties or {}
			use_compact = properties.get('ndarray_compact', None)
			json_compression = bool(properties.get('compression', False))
			if use_compact is None and json_compression and not getattr(numpy_encode, '_warned_compact', False):
				numpy_encode._warned_compact = True
				warnings.warn('storing ndarray in text format while compression in enabled; in the next major version '
					'of json_tricks, the default when using compression will change to compact mode; to already use '
					'that smaller format, pass `properties={"ndarray_compact": True}` to json_tricks.dump; '
					'to silence this warning, pass `properties={"ndarray_compact": False}`; '
					'see issue https://github.com/mverleg/pyjson_tricks/issues/73', JsonTricksDeprecation)
			# Property 'use_compact' may also be an integer, in which case it's the number of
			# elements from which compact storage is used.
			if isinstance(use_compact, int) and not isinstance(use_compact, bool):
				use_compact = obj.size >= use_compact
			if use_compact:
				# If the overall json file is compressed, then don't compress the array.
				data_json = _ndarray_to_bin_str(obj, do_compress=not json_compression)
			else:
				data_json = obj.tolist()
			dct = hashodict((
				('__ndarray__', data_json),
				('dtype', str(obj.dtype)),
				('shape', obj.shape),
			))
			if len(obj.shape) > 1:
				dct['Corder'] = obj.flags['C_CONTIGUOUS']
			return dct
	elif isinstance(obj, generic):
		if NumpyEncoder.SHOW_SCALAR_WARNING:
			NumpyEncoder.SHOW_SCALAR_WARNING = False
			warnings.warn('json-tricks: numpy scalar serialization is experimental and may work differently in future versions')
		return obj.item()
	return obj


def _ndarray_to_bin_str(array, do_compress):
	"""
	From ndarray to base64 encoded, gzipped binary data.
	"""
	from base64 import standard_b64encode
	assert array.flags['C_CONTIGUOUS'], 'only C memory order is (currently) supported for compact ndarray format'

	original_size = array.size * array.itemsize
	header = 'b64:'
	data = array.data
	if do_compress:
		small = gzip_compress(data, compresslevel=9)
		if len(small) < 0.9 * original_size and len(small) < original_size - 8:
			header = 'b64.gz:'
			data = small
	data = standard_b64encode(data)
	return header + data.decode('ascii')


class NumpyEncoder(ClassInstanceEncoder):
	"""
	JSON encoder for numpy arrays.
	"""
	SHOW_SCALAR_WARNING = True	# show a warning that numpy scalar serialization is experimental

	def default(self, obj, *args, **kwargs):
		"""
		If input object is a ndarray it will be converted into a dict holding
		data type, shape and the data. The object can be restored using json_numpy_obj_hook.
		"""
		warnings.warn('`NumpyEncoder` is deprecated, use `numpy_encode`', JsonTricksDeprecation)
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
		warnings.warn('`NoNumpyEncoder` is deprecated, use `nonumpy_encode`', JsonTricksDeprecation)
		obj = nonumpy_encode(obj)
		return super(NoNumpyEncoder, self).default(obj, *args, **kwargs)
