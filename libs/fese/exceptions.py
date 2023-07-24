# -*- coding: utf-8 -*-


class FeseError(Exception):
    pass


class ExtractionError(FeseError):
    pass


class InvalidFile(FeseError):
    pass


class InvalidStream(FeseError):
    pass


class InvalidSource(FeseError):
    pass


class ConversionError(FeseError):
    pass


class LanguageNotFound(FeseError):
    pass


class UnsupportedCodec(FeseError):
    pass
