from typing import List


__all__ = [
    "Pysubs2Error",
    "UnknownFPSError",
    "UnknownFileExtensionError",
    "UnknownFormatIdentifierError",
    "FormatAutodetectionError",
]


class Pysubs2Error(Exception):
    """Base class for pysubs2 exceptions."""


class UnknownFPSError(Pysubs2Error):
    """Framerate was not specified and couldn't be inferred otherwise."""


class UnknownFileExtensionError(Pysubs2Error):
    """
    File extension does not pertain to any known subtitle format.

    This exception is raised by `SSAFile.save()` when the ``format_`` parameter
    is not specified. It will try to guess the desired format from output filename
    and raise this exception when it fails.

    Attributes:
        ext (str): File extension
    """

    def __init__(self, ext: str) -> None:
        self.ext = ext
        msg = f"File extension {ext!r} does not match any supported subtitle format"
        super().__init__(msg)


class UnknownFormatIdentifierError(Pysubs2Error):
    """
    Unknown subtitle format identifier (ie. string like ``"srt"``).

    This exception is used when interpreting ``format_`` parameter fails,
    eg. in `SSAFile.save()`.

    Attributes:
        format_ (str): Format identifier
    """

    def __init__(self, format_: str) -> None:
        self.format_ = format_
        msg = f"Format identifier {format_!r} does not match any supported subtitle format"
        super().__init__(msg)


class FormatAutodetectionError(Pysubs2Error):
    """
    Subtitle format is ambiguous or unknown based on analysis of file fragment

    This exception is raised by `SSAFile.load()` and related methods
    when the ``format_`` parameter is not specified. It will try to guess
    the input format based on reading first few kilobytes of the input file
    and raise this exception if the format cannot be uniquely determined.

    Attributes:
        content (str): Analyzed subtitle file content
        formats (list[str]): Format identifiers for detected formats
    """
    def __init__(self, content: str, formats: List[str]) -> None:
        self.content = content
        self.formats = formats
        if not formats:
            msg = "No suitable formats"
        else:
            msg = f"Multiple suitable formats ({formats!r})"
        super().__init__(msg)
