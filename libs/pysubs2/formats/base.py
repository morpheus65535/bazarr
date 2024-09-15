from typing import Optional, Any, TextIO
from ..ssafile import SSAFile


class FormatBase:
    """
    Base class for subtitle format implementations.

    How to implement a new subtitle format:

    1. Create a subclass of FormatBase and override the methods you want to support.
    2. Decide on a format identifier, like the ``"srt"`` or ``"microdvd"`` already used in the library.
    3. Add your identifier and class to :data:`pysubs2.formats.FORMAT_IDENTIFIER_TO_FORMAT_CLASS`.
    4. (optional) Add your file extension and class to :data:`pysubs2.formats.FILE_EXTENSION_TO_FORMAT_IDENTIFIER`.

    After finishing these steps, you can call :meth:`SSAFile.load()` and :meth:`SSAFile.save()` with your
    format, including autodetection from content and file extension (if you provided these).

    """
    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        Load subtitle file into an empty SSAFile.

        If the parser autodetects framerate, set it as ``subs.fps``.

        Arguments:
            subs (SSAFile): An empty :class:`SSAFile`.
            fp (file object): Text file object, the subtitle file.
            format_ (str): Format identifier. Used when one format class
                implements multiple formats (see :class:`SubstationFormat`).
            kwargs: Extra options, eg. `fps`.

        Returns:
            None

        Raises:
            pysubs2.exceptions.UnknownFPSError: Framerate was not provided and cannot
                be detected.
        """
        raise NotImplementedError("Parsing is not supported for this format")

    @classmethod
    def to_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        Write SSAFile into a file.

        If you need framerate and it is not passed in keyword arguments,
        use ``subs.fps``.

        Arguments:
            subs (SSAFile): Subtitle file to write.
            fp (file object): Text file object used as output.
            format_ (str): Format identifier of desired output format.
                Used when one format class implements multiple formats
                (see :class:`SubstationFormat`).
            kwargs: Extra options, eg. `fps`.

        Returns:
            None

        Raises:
            pysubs2.exceptions.UnknownFPSError: Framerate was not provided and
                ``subs.fps is None``.
        """
        raise NotImplementedError("Writing is not supported for this format")

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """
        Return format identifier of recognized format, or None.

        Arguments:
            text (str): Content of subtitle file. When the file is long,
                this may be only its first few thousand characters.

        Returns:
            format identifier (eg. ``"srt"``) or None (unknown format)
        """
        return None
