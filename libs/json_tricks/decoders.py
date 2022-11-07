import warnings
from base64 import standard_b64decode
from collections import OrderedDict
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from fractions import Fraction

from json_tricks import NoEnumException, NoPandasException, NoNumpyException
from .utils import ClassInstanceHookBase, nested_index, str_type, gzip_decompress, filtered_wrapper


class DuplicateJsonKeyException(Exception):
	""" Trying to load a json map which contains duplicate keys, but allow_duplicates is False """


class TricksPairHook(object):
	"""
	Hook that converts json maps to the appropriate python type (dict or OrderedDict)
	and then runs any number of hooks on the individual maps.
	"""
	def __init__(self, ordered=True, obj_pairs_hooks=None, allow_duplicates=True, properties=None):
		"""
		:param ordered: True if maps should retain their ordering.
		:param obj_pairs_hooks: An iterable of hooks to apply to elements.
		"""
		self.properties = properties or {}
		self.map_type = OrderedDict
		if not ordered:
			self.map_type = dict
		self.obj_pairs_hooks = []
		if obj_pairs_hooks:
			self.obj_pairs_hooks = list(filtered_wrapper(hook) for hook in obj_pairs_hooks)
		self.allow_duplicates = allow_duplicates

	def __call__(self, pairs):
		if not self.allow_duplicates:
			known = set()
			for key, value in pairs:
				if key in known:
					raise DuplicateJsonKeyException(('Trying to load a json map which contains a ' +
						'duplicate key "{0:}" (but allow_duplicates is False)').format(key))
				known.add(key)
		map = self.map_type(pairs)
		for hook in self.obj_pairs_hooks:
			map = hook(map, properties=self.properties)
		return map


def json_date_time_hook(dct):
	"""
	Return an encoded date, time, datetime or timedelta to it's python representation, including optional timezone.

	:param dct: (dict) json encoded date, time, datetime or timedelta
	:return: (date/time/datetime/timedelta obj) python representation of the above
	"""
	def get_tz(dct):
		if not 'tzinfo' in dct:
			return None
		try:
			import pytz
		except ImportError as err:
			raise ImportError(('Tried to load a json object which has a timezone-aware (date)time. '
				'However, `pytz` could not be imported, so the object could not be loaded. '
				'Error: {0:}').format(str(err)))
		return pytz.timezone(dct['tzinfo'])

	if not isinstance(dct, dict):
		return dct
	if '__date__' in dct:
		return date(year=dct.get('year', 0), month=dct.get('month', 0), day=dct.get('day', 0))
	elif '__time__' in dct:
		tzinfo = get_tz(dct)
		return time(hour=dct.get('hour', 0), minute=dct.get('minute', 0), second=dct.get('second', 0),
			microsecond=dct.get('microsecond', 0), tzinfo=tzinfo)
	elif '__datetime__' in dct:
		tzinfo = get_tz(dct)
		dt = datetime(year=dct.get('year', 0), month=dct.get('month', 0), day=dct.get('day', 0),
			hour=dct.get('hour', 0), minute=dct.get('minute', 0), second=dct.get('second', 0),
			microsecond=dct.get('microsecond', 0))
		if tzinfo is None:
			return dt
		return tzinfo.localize(dt)
	elif '__timedelta__' in dct:
		return timedelta(days=dct.get('days', 0), seconds=dct.get('seconds', 0),
			microseconds=dct.get('microseconds', 0))
	return dct


def json_complex_hook(dct):
	"""
	Return an encoded complex number to Python complex type.

	:param dct: (dict) json encoded complex number (__complex__)
	:return: python complex number
	"""
	if not isinstance(dct, dict):
		return dct
	if not '__complex__' in dct:
		return dct
	parts = dct['__complex__']
	assert len(parts) == 2
	return parts[0] + parts[1] * 1j


def json_bytes_hook(dct):
	"""
	Return encoded bytes, either base64 or utf8, back to Python bytes.

	:param dct: any object, if it is a dict containing encoded bytes, they will be converted
	:return: python complex number
	"""
	if not isinstance(dct, dict):
		return dct
	if '__bytes_b64__' in dct:
		return standard_b64decode(dct['__bytes_b64__'])
	if '__bytes_utf8__' in dct:
		return dct['__bytes_utf8__'].encode('utf-8')
	return dct


def numeric_types_hook(dct):
	if not isinstance(dct, dict):
		return dct
	if '__decimal__' in dct:
		return Decimal(dct['__decimal__'])
	if '__fraction__' in dct:
		return Fraction(numerator=dct['numerator'], denominator=dct['denominator'])
	return dct


def noenum_hook(dct):
	if isinstance(dct, dict) and '__enum__' in dct:
		raise NoEnumException(('Trying to decode a map which appears to represent a enum '
			'data structure, but enum support is not enabled, perhaps it is not installed.'))
	return dct


def pathlib_hook(dct):
	if not isinstance(dct, dict):
		return dct
	if not '__pathlib__' in dct:
		return dct
	from pathlib import Path
	return Path(dct['__pathlib__'])


def nopathlib_hook(dct):
	if isinstance(dct, dict) and '__pathlib__' in dct:
		raise NoPathlib(('Trying to decode a map which appears to represent a '
						'pathlib.Path data structure, but pathlib support '
						'is not enabled.'))
	return dct


class EnumInstanceHook(ClassInstanceHookBase):
	"""
	This hook tries to convert json encoded by enum_instance_encode back to it's original instance.
	It only works if the environment is the same, e.g. the enum is similarly importable and hasn't changed.
	"""
	def __call__(self, dct, properties=None):
		if not isinstance(dct, dict):
			return dct
		if '__enum__' not in dct:
			return dct
		cls_lookup_map = properties.get('cls_lookup_map', {})
		mod, name = dct['__enum__']['__enum_instance_type__']
		Cls = self.get_cls_from_instance_type(mod, name, cls_lookup_map=cls_lookup_map)
		return Cls[dct['__enum__']['name']]


class ClassInstanceHook(ClassInstanceHookBase):
	"""
	This hook tries to convert json encoded by class_instance_encoder back to it's original instance.
	It only works if the environment is the same, e.g. the class is similarly importable and hasn't changed.
	"""
	def __call__(self, dct, properties=None):
		if not isinstance(dct, dict):
			return dct
		if '__instance_type__' not in dct:
			return dct
		cls_lookup_map = properties.get('cls_lookup_map', {}) or {}
		mod, name = dct['__instance_type__']
		Cls = self.get_cls_from_instance_type(mod, name, cls_lookup_map=cls_lookup_map)
		try:
			obj = Cls.__new__(Cls)
		except TypeError:
			raise TypeError(('problem while decoding instance of "{0:s}"; this instance has a special '
				'__new__ method and can\'t be restored').format(name))
		if hasattr(obj, '__json_decode__'):
			properties = {}
			if 'slots' in dct:
				properties.update(dct['slots'])
			if 'attributes' in dct:
				properties.update(dct['attributes'])
			obj.__json_decode__(**properties)
		else:
			if 'slots' in dct:
				for slot,value in dct['slots'].items():
					setattr(obj, slot, value)
			if 'attributes' in dct:
				obj.__dict__ = dict(dct['attributes'])
		return obj


def json_set_hook(dct):
	"""
	Return an encoded set to it's python representation.
	"""
	if not isinstance(dct, dict):
		return dct
	if '__set__' not in dct:
		return dct
	return set((tuple(item) if isinstance(item, list) else item) for item in dct['__set__'])


def pandas_hook(dct):
	if not isinstance(dct, dict):
		return dct
	if '__pandas_dataframe__' not in dct and '__pandas_series__' not in dct:
		return dct
	if '__pandas_dataframe__' in dct:
		try:
			from pandas import DataFrame
		except ImportError:
			raise NoPandasException('Trying to decode a map which appears to repr esent a pandas data structure, but pandas appears not to be installed.')
		from numpy import dtype, array
		meta = dct.pop('__pandas_dataframe__')
		indx = dct.pop('index') if 'index' in dct else None
		dtypes = dict((colname, dtype(tp)) for colname, tp in zip(meta['column_order'], meta['types']))
		data = OrderedDict()
		for name, col in dct.items():
			data[name] = array(col, dtype=dtypes[name])
		return DataFrame(
			data=data,
			index=indx,
			columns=meta['column_order'],
			# mixed `dtypes` argument not supported, so use duct of numpy arrays
		)
	elif '__pandas_series__' in dct:
		from pandas import Series
		from numpy import dtype, array
		meta = dct.pop('__pandas_series__')
		indx = dct.pop('index') if 'index' in dct else None
		return Series(
			data=dct['data'],
			index=indx,
			name=meta['name'],
			dtype=dtype(meta['type']),
		)
	return dct	# impossible


def nopandas_hook(dct):
	if isinstance(dct, dict) and ('__pandas_dataframe__' in dct or '__pandas_series__' in dct):
		raise NoPandasException(('Trying to decode a map which appears to represent a pandas '
			'data structure, but pandas support is not enabled, perhaps it is not installed.'))
	return dct


def json_numpy_obj_hook(dct):
	"""
	Replace any numpy arrays previously encoded by NumpyEncoder to their proper
	shape, data type and data.

	:param dct: (dict) json encoded ndarray
	:return: (ndarray) if input was an encoded ndarray
	"""
	if not isinstance(dct, dict):
		return dct
	if not '__ndarray__' in dct:
		return dct
	try:
		import numpy
	except ImportError:
		raise NoNumpyException('Trying to decode a map which appears to represent a numpy '
			'array, but numpy appears not to be installed.')
	order = None
	if 'Corder' in dct:
		order = 'C' if dct['Corder'] else 'F'
	data_json = dct['__ndarray__']
	shape = tuple(dct['shape'])
	nptype = dct['dtype']
	if shape:
		if nptype == 'object':
			return _lists_of_obj_to_ndarray(data_json, order, shape, nptype)
		if isinstance(data_json, str_type):
			return _bin_str_to_ndarray(data_json, order, shape, nptype)
		else:
			return _lists_of_numbers_to_ndarray(data_json, order, shape, nptype)
	else:
		return _scalar_to_numpy(data_json, nptype)


def _bin_str_to_ndarray(data, order, shape, dtype):
	"""
	From base64 encoded, gzipped binary data to ndarray.
	"""
	from base64 import standard_b64decode
	from numpy import frombuffer

	assert order in [None, 'C'], 'specifying different memory order is not (yet) supported ' \
		'for binary numpy format (got order = {})'.format(order)
	if data.startswith('b64.gz:'):
		data = standard_b64decode(data[7:])
		data = gzip_decompress(data)
	elif data.startswith('b64:'):
		data = standard_b64decode(data[4:])
	else:
		raise ValueError('found numpy array buffer, but did not understand header; supported: b64 or b64.gz')
	data = frombuffer(data, dtype=dtype)
	return data.reshape(shape)


def _lists_of_numbers_to_ndarray(data, order, shape, dtype):
	"""
	From nested list of numbers to ndarray.
	"""
	from numpy import asarray
	arr = asarray(data, dtype=dtype, order=order)
	if 0 in shape:
		return arr.reshape(shape)
	if shape != arr.shape:
		warnings.warn('size mismatch decoding numpy array: expected {}, got {}'.format(shape, arr.shape))
	return arr


def _lists_of_obj_to_ndarray(data, order, shape, dtype):
	"""
	From nested list of objects (that aren't native numpy numbers) to ndarray.
	"""
	from numpy import empty, ndindex
	arr = empty(shape, dtype=dtype, order=order)
	dec_data = data
	for indx in ndindex(arr.shape):
		arr[indx] = nested_index(dec_data, indx)
	return arr


def _scalar_to_numpy(data, dtype):
	"""
	From scalar value to numpy type.
	"""
	import numpy as nptypes
	dtype = getattr(nptypes, dtype)
	return dtype(data)


def json_nonumpy_obj_hook(dct):
	"""
	This hook has no effect except to check if you're trying to decode numpy arrays without support, and give you a useful message.
	"""
	if isinstance(dct, dict) and '__ndarray__' in dct:
		raise NoNumpyException(('Trying to decode a map which appears to represent a numpy array, '
			'but numpy support is not enabled, perhaps it is not installed.'))
	return dct


