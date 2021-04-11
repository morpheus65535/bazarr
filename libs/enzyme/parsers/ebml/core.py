# -*- coding: utf-8 -*-
from ...exceptions import ReadError
from .readers import *
from pkg_resources import resource_stream  # @UnresolvedImport
from xml.dom import minidom
import logging


__all__ = ['INTEGER', 'UINTEGER', 'FLOAT', 'STRING', 'UNICODE', 'DATE', 'MASTER', 'BINARY',
           'SPEC_TYPES', 'READERS', 'Element', 'MasterElement', 'parse', 'parse_element',
           'get_matroska_specs']
logger = logging.getLogger(__name__)


# EBML types
INTEGER, UINTEGER, FLOAT, STRING, UNICODE, DATE, MASTER, BINARY = range(8)

# Spec types to EBML types mapping
SPEC_TYPES = {
    'integer': INTEGER,
    'uinteger': UINTEGER,
    'float': FLOAT,
    'string': STRING,
    'utf-8': UNICODE,
    'date': DATE,
    'master': MASTER,
    'binary': BINARY
}

# Readers to use per EBML type
READERS = {
    INTEGER: read_element_integer,
    UINTEGER: read_element_uinteger,
    FLOAT: read_element_float,
    STRING: read_element_string,
    UNICODE: read_element_unicode,
    DATE: read_element_date,
    BINARY: read_element_binary
}


class Element(object):
    """Base object of EBML

    :param int id: id of the element, best represented as hexadecimal (0x18538067 for Matroska Segment element)
    :param type: type of the element
    :type type: :data:`INTEGER`, :data:`UINTEGER`, :data:`FLOAT`, :data:`STRING`, :data:`UNICODE`, :data:`DATE`, :data:`MASTER` or :data:`BINARY`
    :param string name: name of the element
    :param int level: level of the element
    :param int position: position of element's data
    :param int size: size of element's data
    :param data: data as read by the corresponding :data:`READERS`

    """
    def __init__(self, id=None, type=None, name=None, level=None, position=None, size=None, data=None):  # @ReservedAssignment
        self.id = id
        self.type = type
        self.name = name
        self.level = level
        self.position = position
        self.size = size
        self.data = data

    def __repr__(self):
        return '<%s [%s, %r]>' % (self.__class__.__name__, self.name, self.data)


class MasterElement(Element):
    """Element of type :data:`MASTER` that has a list of :class:`Element` as its data

    :param int id: id of the element, best represented as hexadecimal (0x18538067 for Matroska Segment element)
    :param string name: name of the element
    :param int level: level of the element
    :param int position: position of element's data
    :param int size: size of element's data
    :param data: child elements
    :type data: list of :class:`Element`

    :class:`MasterElement` implements some magic methods to ease manipulation. Thus, a MasterElement supports
    the `in` keyword to test for the presence of a child element by its name and gives access to it
    with a container getter::

        >>> ebml_element = parse(open('test1.mkv', 'rb'), get_matroska_specs())[0]
        >>> 'EBMLVersion' in ebml_element
        False
        >>> 'DocType' in ebml_element
        True
        >>> ebml_element['DocType']
        Element(DocType, u'matroska')

    """
    def __init__(self, id=None, name=None, level=None, position=None, size=None, data=None):  # @ReservedAssignment
        super(MasterElement, self).__init__(id, MASTER, name, level, position, size, data)

    def load(self, stream, specs, ignore_element_types=None, ignore_element_names=None, max_level=None):
        """Load children :class:`Elements <Element>` with level lower or equal to the `max_level`
        from the `stream` according to the `specs`

        :param stream: file-like object from which to read
        :param dict specs: see :ref:`specs`
        :param int max_level: maximum level for children elements
        :param list ignore_element_types: list of element types to ignore
        :param list ignore_element_names: list of element names to ignore
        :param int max_level: maximum level of elements

        """
        self.data = parse(stream, specs, self.size, ignore_element_types, ignore_element_names, max_level)

    def get(self, name, default=None):
        """Convenience method for ``master_element[name].data if name in master_element else default``

        :param string name: the name of the child to get
        :param default: default value if `name` is not in the :class:`MasterElement`
        :return: the data of the child :class:`Element` or `default`

        """
        if name not in self:
            return default
        element = self[name]
        if element.type == MASTER:
            raise ValueError('%s is a MasterElement' % name)
        return element.data

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.data[key]
        children = [e for e in self.data if e.name == key]
        if not children:
            raise KeyError(key)
        if len(children) > 1:
            raise KeyError('More than 1 child with key %s (%d)' % (key, len(children)))
        return children[0]

    def __contains__(self, item):
        return len([e for e in self.data if e.name == item]) > 0

    def __iter__(self):
        return iter(self.data)


def parse(stream, specs, size=None, ignore_element_types=None, ignore_element_names=None, max_level=None):
    """Parse a stream for `size` bytes according to the `specs`

    :param stream: file-like object from which to read
    :param size: maximum number of bytes to read, None to read all the stream
    :type size: int or None
    :param dict specs: see :ref:`specs`
    :param list ignore_element_types: list of element types to ignore
    :param list ignore_element_names: list of element names to ignore
    :param int max_level: maximum level of elements
    :return: parsed data as a tree of :class:`~enzyme.parsers.ebml.core.Element`
    :rtype: list

    .. note::
        If `size` is reached in a middle of an element, reading will continue
        until the element is fully parsed.

    """
    ignore_element_types = ignore_element_types if ignore_element_types is not None else []
    ignore_element_names = ignore_element_names if ignore_element_names is not None else []
    start = stream.tell()
    elements = []
    while size is None or stream.tell() - start < size:
        try:
            element = parse_element(stream, specs)
            if element is None:
                continue
            logger.debug('%s %s parsed', element.__class__.__name__, element.name)
            if element.type in ignore_element_types or element.name in ignore_element_names:
                logger.info('%s %s ignored', element.__class__.__name__, element.name)
                if element.type == MASTER:
                    stream.seek(element.size, 1)
                continue
            if element.type == MASTER:
                if max_level is not None and element.level >= max_level:
                    logger.info('Maximum level %d reached for children of %s %s', max_level, element.__class__.__name__, element.name)
                    stream.seek(element.size, 1)
                else:
                    logger.debug('Loading child elements for %s %s with size %d', element.__class__.__name__, element.name, element.size)
                    element.data = parse(stream, specs, element.size, ignore_element_types, ignore_element_names, max_level)
            elements.append(element)
        except ReadError:
            if size is not None:
                raise
            break
    return elements


def parse_element(stream, specs, load_children=False, ignore_element_types=None, ignore_element_names=None, max_level=None):
    """Extract a single :class:`Element` from the `stream` according to the `specs`

    :param stream: file-like object from which to read
    :param dict specs: see :ref:`specs`
    :param bool load_children: load children elements if the parsed element is a :class:`MasterElement`
    :param list ignore_element_types: list of element types to ignore
    :param list ignore_element_names: list of element names to ignore
    :param int max_level: maximum level for children elements
    :return: the parsed element
    :rtype: :class:`Element`

    """
    ignore_element_types = ignore_element_types if ignore_element_types is not None else []
    ignore_element_names = ignore_element_names if ignore_element_names is not None else []
    element_id = read_element_id(stream)
    if element_id is None:
        raise ReadError('Cannot read element id')
    element_size = read_element_size(stream)
    if element_size is None:
        raise ReadError('Cannot read element size')
    if element_id not in specs:
        logger.error('Element with id 0x%x is not in the specs' % element_id)
        stream.seek(element_size, 1)
        return None
    element_type, element_name, element_level = specs[element_id]
    if element_type == MASTER:
        element = MasterElement(element_id, element_name, element_level, stream.tell(), element_size)
        if load_children:
            element.data = parse(stream, specs, element.size, ignore_element_types, ignore_element_names, max_level)
    else:
        element = Element(element_id, element_type, element_name, element_level, stream.tell(), element_size)
        element.data = READERS[element_type](stream, element_size)
    return element


def get_matroska_specs(webm_only=False):
    """Get the Matroska specs

    :param bool webm_only: load *only* WebM specs
    :return: the specs in the appropriate format. See :ref:`specs`
    :rtype: dict

    """
    specs = {}
    with resource_stream(__name__, 'specs/matroska.xml') as resource:
        xmldoc = minidom.parse(resource)
        for element in xmldoc.getElementsByTagName('element'):
            if not webm_only or element.hasAttribute('webm') and element.getAttribute('webm') == '1':
                specs[int(element.getAttribute('id'), 16)] = (SPEC_TYPES[element.getAttribute('type')], element.getAttribute('name'), int(element.getAttribute('level')))
    return specs
