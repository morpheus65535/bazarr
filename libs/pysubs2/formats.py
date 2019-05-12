from .formatbase import FormatBase
from .microdvd import MicroDVDFormat
from .subrip import SubripFormat
from .jsonformat import JSONFormat
from .substation import SubstationFormat
from .mpl2 import MPL2Format
from .exceptions import *

#: Dict mapping file extensions to format identifiers.
FILE_EXTENSION_TO_FORMAT_IDENTIFIER = {
    ".srt": "srt",
    ".ass": "ass",
    ".ssa": "ssa",
    ".sub": "microdvd",
    ".json": "json",
}

#: Dict mapping format identifiers to implementations (FormatBase subclasses).
FORMAT_IDENTIFIER_TO_FORMAT_CLASS = {
    "srt": SubripFormat,
    "ass": SubstationFormat,
    "ssa": SubstationFormat,
    "microdvd": MicroDVDFormat,
    "json": JSONFormat,
    "mpl2": MPL2Format,
}

def get_format_class(format_):
    """Format identifier -> format class (ie. subclass of FormatBase)"""
    try:
        return FORMAT_IDENTIFIER_TO_FORMAT_CLASS[format_]
    except KeyError:
        raise UnknownFormatIdentifierError(format_)

def get_format_identifier(ext):
    """File extension -> format identifier"""
    try:
        return FILE_EXTENSION_TO_FORMAT_IDENTIFIER[ext]
    except KeyError:
        raise UnknownFileExtensionError(ext)

def get_file_extension(format_):
    """Format identifier -> file extension"""
    if format_ not in FORMAT_IDENTIFIER_TO_FORMAT_CLASS:
        raise UnknownFormatIdentifierError(format_)

    for ext, f in FILE_EXTENSION_TO_FORMAT_IDENTIFIER.items():
        if f == format_:
            return ext

    raise RuntimeError("No file extension for format %r" % format_)

def autodetect_format(content):
    """Return format identifier for given fragment or raise FormatAutodetectionError."""
    formats = set()
    for impl in FORMAT_IDENTIFIER_TO_FORMAT_CLASS.values():
        guess = impl.guess_format(content)
        if guess is not None:
            formats.add(guess)

    if len(formats) == 1:
        return formats.pop()
    elif not formats:
        raise FormatAutodetectionError("No suitable formats")
    else:
        raise FormatAutodetectionError("Multiple suitable formats (%r)" % formats)
