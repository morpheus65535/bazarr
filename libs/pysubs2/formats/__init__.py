from typing import Dict, Type

from .base import FormatBase
from .microdvd import MicroDVDFormat
from .subrip import SubripFormat
from .jsonformat import JSONFormat
from .substation import SubstationFormat
from .mpl2 import MPL2Format
from .tmp import TmpFormat
from .webvtt import WebVTTFormat
from ..exceptions import UnknownFormatIdentifierError, UnknownFileExtensionError, FormatAutodetectionError

#: Dict mapping file extensions to format identifiers.
FILE_EXTENSION_TO_FORMAT_IDENTIFIER: Dict[str, str] = {
    ".srt": "srt",
    ".ass": "ass",
    ".ssa": "ssa",
    ".sub": "microdvd",
    ".json": "json",
    ".txt": "tmp",
    ".vtt": "vtt",
}

#: Dict mapping format identifiers to implementations (FormatBase subclasses).
FORMAT_IDENTIFIER_TO_FORMAT_CLASS: Dict[str, Type[FormatBase]] = {
    "srt": SubripFormat,
    "ass": SubstationFormat,
    "ssa": SubstationFormat,
    "microdvd": MicroDVDFormat,
    "json": JSONFormat,
    "mpl2": MPL2Format,
    "tmp": TmpFormat,
    "vtt": WebVTTFormat,
}

FORMAT_IDENTIFIERS = list(FORMAT_IDENTIFIER_TO_FORMAT_CLASS.keys())


def get_format_class(format_: str) -> Type[FormatBase]:
    """Format identifier -> format class (ie. subclass of FormatBase)"""
    try:
        return FORMAT_IDENTIFIER_TO_FORMAT_CLASS[format_]
    except KeyError:
        raise UnknownFormatIdentifierError(format_)


def get_format_identifier(ext: str) -> str:
    """File extension -> format identifier"""
    try:
        return FILE_EXTENSION_TO_FORMAT_IDENTIFIER[ext]
    except KeyError:
        raise UnknownFileExtensionError(ext)


def get_file_extension(format_: str) -> str:
    """Format identifier -> file extension"""
    if format_ not in FORMAT_IDENTIFIER_TO_FORMAT_CLASS:
        raise UnknownFormatIdentifierError(format_)

    for ext, f in FILE_EXTENSION_TO_FORMAT_IDENTIFIER.items():
        if f == format_:
            return ext

    raise RuntimeError(f"No file extension for format {format_!r}")


def autodetect_format(content: str) -> str:
    """Return format identifier for given fragment or raise FormatAutodetectionError."""
    formats = set()
    for impl in FORMAT_IDENTIFIER_TO_FORMAT_CLASS.values():
        guess = impl.guess_format(content)
        if guess is not None:
            formats.add(guess)

    if len(formats) == 1:
        return formats.pop()
    elif not formats:
        raise FormatAutodetectionError(content=content, formats=[])
    else:
        raise FormatAutodetectionError(content=content, formats=list(formats))
