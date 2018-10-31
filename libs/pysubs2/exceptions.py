class Pysubs2Error(Exception):
    """Base class for pysubs2 exceptions."""

class UnknownFPSError(Pysubs2Error):
    """Framerate was not specified and couldn't be inferred otherwise."""

class UnknownFileExtensionError(Pysubs2Error):
    """File extension does not pertain to any known subtitle format."""

class UnknownFormatIdentifierError(Pysubs2Error):
    """Unknown subtitle format identifier (ie. string like ``"srt"``)."""

class FormatAutodetectionError(Pysubs2Error):
    """Subtitle format is ambiguous or unknown."""
