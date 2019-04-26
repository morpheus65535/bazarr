from __future__ import unicode_literals
import six


#Undefined
class PyJsUndefined(object):
    TYPE = 'Undefined'
    Class = 'Undefined'


undefined = PyJsUndefined()


#Null
class PyJsNull(object):
    TYPE = 'Null'
    Class = 'Null'


null = PyJsNull()

Infinity = float('inf')
NaN = float('nan')

UNDEFINED_TYPE = PyJsUndefined
NULL_TYPE = PyJsNull
STRING_TYPE = unicode if six.PY2 else str
NUMBER_TYPE = float
BOOLEAN_TYPE = bool

# exactly 5 simplexes!
PRIMITIVES = frozenset(
    [UNDEFINED_TYPE, NULL_TYPE, STRING_TYPE, NUMBER_TYPE, BOOLEAN_TYPE])

TYPE_NAMES = {
    UNDEFINED_TYPE: 'Undefined',
    NULL_TYPE: 'Null',
    STRING_TYPE: 'String',
    NUMBER_TYPE: 'Number',
    BOOLEAN_TYPE: 'Boolean',
}


def Type(x):
    # Any -> Str
    return TYPE_NAMES.get(type(x), 'Object')


def GetClass(x):
    # Any -> Str
    cand = TYPE_NAMES.get(type(x))
    if cand is None:
        return x.Class
    return cand


def is_undefined(self):
    return self is undefined


def is_null(self):
    return self is null


def is_primitive(self):
    return type(self) in PRIMITIVES


def is_object(self):
    return not is_primitive(self)


def is_callable(self):
    return hasattr(self, 'call')


def is_infinity(self):
    return self == float('inf') or self == -float('inf')


def is_nan(self):
    return self != self  # nan!=nan evaluates to True


def is_finite(self):
    return not (is_nan(self) or is_infinity(self))


class JsException(Exception):
    def __init__(self, typ=None, message=None, throw=None):
        if typ is None and message is None and throw is None:
            # it means its the trasnlator based error (old format), do nothing
            self._translator_based = True
        else:
            assert throw is None or (typ is None
                                     and message is None), (throw, typ,
                                                            message)
            self._translator_based = False
            self.typ = typ
            self.message = message
            self.throw = throw

    def get_thrown_value(self, space):
        if self.throw is not None:
            return self.throw
        else:
            return space.NewError(self.typ, self.message)

    def __str__(self):
        if self._translator_based:
            if self.mes.Class == 'Error':
                return self.mes.callprop('toString').value
            else:
                return self.mes.to_string().value
        else:
            if self.throw is not None:
                from conversions import to_string
                return to_string(self.throw)
            else:
                return self.typ + ': ' + self.message


def MakeError(typ, message=u'no info', throw=None):
    return JsException(typ,
                       unicode(message) if message is not None else message,
                       throw)


def value_from_js_exception(js_exception, space):
    if js_exception.throw is not None:
        return js_exception.throw
    else:
        return space.NewError(js_exception.typ, js_exception.message)
