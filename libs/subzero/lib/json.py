# coding=utf-8
from gzip import GzipFile

from json_tricks import TricksEncoder
from json_tricks.nonp import DEFAULT_ENCODERS, ENCODING, is_py3, BytesIO


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
    #if not is_py3 and isinstance(txt, str):
    #    txt = unicode(txt, ENCODING)
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
