# -*- coding: utf-8 -*-
__all__ = ['Error', 'MalformedMKVError', 'ParserError', 'ReadError', 'SizeError']


class Error(Exception):
    """Base class for enzyme exceptions"""
    pass


class MalformedMKVError(Error):
    """Wrong or malformed element found"""
    pass


class ParserError(Error):
    """Base class for exceptions in parsers"""
    pass


class ReadError(ParserError):
    """Unable to correctly read"""
    pass


class SizeError(ParserError):
    """Mismatch between the type of the element and the size of its data"""
    pass
