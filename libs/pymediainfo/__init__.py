# vim: set fileencoding=utf-8 :
"""
This module is a wrapper around the MediaInfo library.
"""
import ctypes
import json
import os
import pathlib
import re
import sys
import warnings
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata  # type: ignore

try:
    __version__ = metadata.version("pymediainfo")
except metadata.PackageNotFoundError:
    __version__ = ""


class Track:
    """
    An object associated with a media file track.

    Each :class:`Track` attribute corresponds to attributes parsed from MediaInfo's output.
    All attributes are lower case. Attributes that are present several times such as `Duration`
    yield a second attribute starting with `other_` which is a list of all alternative
    attribute values.

    When a non-existing attribute is accessed, `None` is returned.

    Example:

    >>> t = mi.tracks[0]
    >>> t
    <Track track_id='None', track_type='General'>
    >>> t.duration
    3000
    >>> t.other_duration
    ['3 s 0 ms', '3 s 0 ms', '3 s 0 ms',
        '00:00:03.000', '00:00:03.000']
    >>> type(t.non_existing)
    NoneType

    All available attributes can be obtained by calling :func:`to_data`.
    """

    def __eq__(self, other):  # type: ignore
        return self.__dict__ == other.__dict__

    def __getattribute__(self, name):  # type: ignore
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass
        return None

    def __getstate__(self):  # type: ignore
        return self.__dict__

    def __setstate__(self, state):  # type: ignore
        self.__dict__ = state

    def __init__(self, xml_dom_fragment: ET.Element):
        self.track_type = xml_dom_fragment.attrib["type"]
        repeated_attributes = []
        for elem in xml_dom_fragment:
            node_name = elem.tag.lower().strip().strip("_")
            if node_name == "id":
                node_name = "track_id"
            node_value = elem.text
            if getattr(self, node_name) is None:
                setattr(self, node_name, node_value)
            else:
                other_node_name = f"other_{node_name}"
                repeated_attributes.append((node_name, other_node_name))
                if getattr(self, other_node_name) is None:
                    setattr(self, other_node_name, [node_value])
                else:
                    getattr(self, other_node_name).append(node_value)

        for primary_key, other_key in repeated_attributes:
            try:
                # Attempt to convert the main value to int
                # Usually, if an attribute is repeated, one of its value
                # is an int and others are human-readable formats
                setattr(self, primary_key, int(getattr(self, primary_key)))
            except ValueError:
                # If it fails, try to find a secondary value
                # that is an int and swap it with the main value
                for other_value in getattr(self, other_key):
                    try:
                        current = getattr(self, primary_key)
                        # Set the main value to an int
                        setattr(self, primary_key, int(other_value))
                        # Append its previous value to other values
                        getattr(self, other_key).append(current)
                        break
                    except ValueError:
                        pass

    def __repr__(self):  # type: ignore
        return "<Track track_id='{}', track_type='{}'>".format(self.track_id, self.track_type)

    def to_data(self) -> Dict[str, Any]:
        """
        Returns a dict representation of the track attributes.

        Example:

        >>> sorted(track.to_data().keys())[:3]
        ['codec', 'codec_extensions_usually_used', 'codec_url']
        >>> t.to_data()["file_size"]
        5988


        :rtype: dict
        """
        return self.__dict__


class MediaInfo:
    """
    An object containing information about a media file.


    :class:`MediaInfo` objects can be created by directly calling code from
    libmediainfo (in this case, the library must be present on the system):

    >>> pymediainfo.MediaInfo.parse("/path/to/file.mp4")

    Alternatively, objects may be created from MediaInfo's XML output.
    Such output can be obtained using the ``XML`` output format on versions older than v17.10
    and the ``OLDXML`` format on newer versions.

    Using such an XML file, we can create a :class:`MediaInfo` object:

    >>> with open("output.xml") as f:
    ...     mi = pymediainfo.MediaInfo(f.read())

    :param str xml: XML output obtained from MediaInfo.
    :param str encoding_errors: option to pass to :func:`str.encode`'s `errors`
        parameter before parsing `xml`.
    :raises xml.etree.ElementTree.ParseError: if passed invalid XML.
    :var tracks: A list of :py:class:`Track` objects which the media file contains.
        For instance:

        >>> mi = pymediainfo.MediaInfo.parse("/path/to/file.mp4")
        >>> for t in mi.tracks:
        ...     print(t)
        <Track track_id='None', track_type='General'>
        <Track track_id='1', track_type='Text'>
    """

    def __eq__(self, other):  # type: ignore
        return self.tracks == other.tracks

    def __init__(self, xml: str, encoding_errors: str = "strict"):
        xml_dom = ET.fromstring(xml.encode("utf-8", encoding_errors))
        self.tracks = []
        # This is the case for libmediainfo < 18.03
        # https://github.com/sbraz/pymediainfo/issues/57
        # https://github.com/MediaArea/MediaInfoLib/commit/575a9a32e6960ea34adb3bc982c64edfa06e95eb
        if xml_dom.tag == "File":
            xpath = "track"
        else:
            xpath = "File/track"
        for xml_track in xml_dom.iterfind(xpath):
            self.tracks.append(Track(xml_track))

    def _tracks(self, track_type: str) -> List[Track]:
        return [track for track in self.tracks if track.track_type == track_type]

    @property
    def general_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``General``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("General")

    @property
    def video_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Video``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Video")

    @property
    def audio_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Audio``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Audio")

    @property
    def text_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Text``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Text")

    @property
    def other_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Other``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Other")

    @property
    def image_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Image``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Image")

    @property
    def menu_tracks(self) -> List[Track]:
        """
        :return: All :class:`Track`\\s of type ``Menu``.
        :rtype: list of :class:`Track`\\s
        """
        return self._tracks("Menu")

    @staticmethod
    def _normalize_filename(filename: Any) -> Any:
        if hasattr(os, "PathLike") and isinstance(filename, os.PathLike):
            return os.fspath(filename)
        if pathlib is not None and isinstance(filename, pathlib.PurePath):
            return str(filename)
        return filename

    @classmethod
    def _define_library_prototypes(cls, lib: Any) -> Any:
        lib.MediaInfo_Inform.restype = ctypes.c_wchar_p
        lib.MediaInfo_New.argtypes = []
        lib.MediaInfo_New.restype = ctypes.c_void_p
        lib.MediaInfo_Option.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
        ]
        lib.MediaInfo_Option.restype = ctypes.c_wchar_p
        lib.MediaInfo_Inform.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        lib.MediaInfo_Inform.restype = ctypes.c_wchar_p
        lib.MediaInfo_Open.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        lib.MediaInfo_Open.restype = ctypes.c_size_t
        lib.MediaInfo_Open_Buffer_Init.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_uint64,
        ]
        lib.MediaInfo_Open_Buffer_Init.restype = ctypes.c_size_t
        lib.MediaInfo_Open_Buffer_Continue.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        lib.MediaInfo_Open_Buffer_Continue.restype = ctypes.c_size_t
        lib.MediaInfo_Open_Buffer_Continue_GoTo_Get.argtypes = [ctypes.c_void_p]
        lib.MediaInfo_Open_Buffer_Continue_GoTo_Get.restype = ctypes.c_uint64
        lib.MediaInfo_Open_Buffer_Finalize.argtypes = [ctypes.c_void_p]
        lib.MediaInfo_Open_Buffer_Finalize.restype = ctypes.c_size_t
        lib.MediaInfo_Delete.argtypes = [ctypes.c_void_p]
        lib.MediaInfo_Delete.restype = None
        lib.MediaInfo_Close.argtypes = [ctypes.c_void_p]
        lib.MediaInfo_Close.restype = None

    @staticmethod
    def _get_library_paths(os_is_nt: bool) -> Tuple[str]:
        if os_is_nt:
            library_paths = ("MediaInfo.dll",)
        elif sys.platform == "darwin":
            library_paths = ("libmediainfo.0.dylib", "libmediainfo.dylib")
        else:
            library_paths = ("libmediainfo.so.0",)
        script_dir = os.path.dirname(__file__)
        # Look for the library file in the script folder
        for library in library_paths:
            absolute_library_path = os.path.join(script_dir, library)
            if os.path.isfile(absolute_library_path):
                # If we find it, don't try any other filename
                library_paths = (absolute_library_path,)
                break
        return library_paths

    @classmethod
    def _get_library(
        cls,
        library_file: Optional[str] = None,
    ) -> Tuple[Any, Any, str, Tuple[int, ...]]:
        os_is_nt = os.name in ("nt", "dos", "os2", "ce")
        if os_is_nt:
            lib_type = ctypes.WinDLL  # type: ignore
        else:
            lib_type = ctypes.CDLL
        if library_file is None:
            library_paths = cls._get_library_paths(os_is_nt)
        else:
            library_paths = (library_file,)
        exceptions = []
        for library_path in library_paths:
            try:
                lib = lib_type(library_path)
                cls._define_library_prototypes(lib)
                # Without a handle, there might be problems when using concurrent threads
                # https://github.com/sbraz/pymediainfo/issues/76#issuecomment-574759621
                handle = lib.MediaInfo_New()
                version = lib.MediaInfo_Option(handle, "Info_Version", "")
                match = re.search(r"^MediaInfoLib - v(\S+)", version)
                if match:
                    lib_version_str = match.group(1)
                    lib_version = tuple(int(_) for _ in lib_version_str.split("."))
                else:
                    raise RuntimeError("Could not determine library version")
                return (lib, handle, lib_version_str, lib_version)
            except OSError as exc:
                exceptions.append(str(exc))
        raise OSError(
            "Failed to load library from {} - {}".format(
                ", ".join(library_paths), ", ".join(exceptions)
            )
        )

    @classmethod
    def can_parse(cls, library_file: Optional[str] = None) -> bool:
        """
        Checks whether media files can be analyzed using libmediainfo.

        :param str library_file: path to the libmediainfo library, this should only be used if
            the library cannot be auto-detected.
        :rtype: bool
        """
        try:
            lib, handle = cls._get_library(library_file)[:2]
            lib.MediaInfo_Close(handle)
            lib.MediaInfo_Delete(handle)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    @classmethod
    def parse(
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches, too-many-locals, too-many-arguments
        cls,
        filename: Any,
        library_file: Optional[str] = None,
        cover_data: bool = False,
        encoding_errors: str = "strict",
        parse_speed: float = 0.5,
        full: bool = True,
        legacy_stream_display: bool = False,
        mediainfo_options: Optional[Dict[str, str]] = None,
        output: Optional[str] = None,
    ) -> Union[str, "MediaInfo"]:
        """
        Analyze a media file using libmediainfo.

        .. note::
            Because of the way the underlying library works, this method should not
            be called simultaneously from multiple threads *with different arguments*.
            Doing so will cause inconsistencies or failures by changing
            library options that are shared across threads.

        :param filename: path to the media file or file-like object which will be analyzed.
            A URL can also be used if libmediainfo was compiled
            with CURL support.
        :param str library_file: path to the libmediainfo library, this should only be used if
            the library cannot be auto-detected.
        :param bool cover_data: whether to retrieve cover data as base64.
        :param str encoding_errors: option to pass to :func:`str.encode`'s `errors`
            parameter before parsing MediaInfo's XML output.
        :param float parse_speed: passed to the library as `ParseSpeed`,
            this option takes values between 0 and 1.
            A higher value will yield more precise results in some cases
            but will also increase parsing time.
        :param bool full: display additional tags, including computer-readable values
            for sizes and durations.
        :param bool legacy_stream_display: display additional information about streams.
        :param dict mediainfo_options: additional options that will be passed to the
            `MediaInfo_Option` function, for example: ``{"Language": "raw"}``.
            Do not use this parameter when running the method simultaneously from multiple threads,
            it will trigger a reset of all options which will cause inconsistencies or failures.
        :param str output: custom output format for MediaInfo, corresponds to the CLI's
            ``--Output`` parameter. Setting this causes the method to
            return a `str` instead of a :class:`MediaInfo` object.

            Useful values include:
                * the empty `str` ``""`` (corresponds to the default
                  text output, obtained when running ``mediainfo`` with no
                  additional parameters)

                * ``"XML"``

                * ``"JSON"``

                * ``%``-delimited templates (see ``mediainfo --Info-Parameters``)
        :type filename: str or pathlib.Path or os.PathLike or file-like object.
        :rtype: str if `output` is set.
        :rtype: :class:`MediaInfo` otherwise.
        :raises FileNotFoundError: if passed a non-existent file.
        :raises ValueError: if passed a file-like object opened in text mode.
        :raises OSError: if the library file could not be loaded.
        :raises RuntimeError: if parsing fails, this should not
            happen unless libmediainfo itself fails.

        Examples:
            >>> pymediainfo.MediaInfo.parse("tests/data/sample.mkv")
                <pymediainfo.MediaInfo object at 0x7fa83a3db240>

            >>> import json
            >>> mi = pymediainfo.MediaInfo.parse("tests/data/sample.mkv",
            ...     output="JSON")
            >>> json.loads(mi)["media"]["track"][0]
                {'@type': 'General', 'TextCount': '1', 'FileExtension': 'mkv',
                    'FileSize': '5904',  … }


        """
        lib, handle, lib_version_str, lib_version = cls._get_library(library_file)
        # The XML option was renamed starting with version 17.10
        if lib_version >= (17, 10):
            xml_option = "OLDXML"
        else:
            xml_option = "XML"
        # Cover_Data is not extracted by default since version 18.03
        # See https://github.com/MediaArea/MediaInfoLib/commit/d8fd88a1
        if lib_version >= (18, 3):
            lib.MediaInfo_Option(handle, "Cover_Data", "base64" if cover_data else "")
        lib.MediaInfo_Option(handle, "CharSet", "UTF-8")
        lib.MediaInfo_Option(handle, "Inform", xml_option if output is None else output)
        lib.MediaInfo_Option(handle, "Complete", "1" if full else "")
        lib.MediaInfo_Option(handle, "ParseSpeed", str(parse_speed))
        lib.MediaInfo_Option(handle, "LegacyStreamDisplay", "1" if legacy_stream_display else "")
        if mediainfo_options is not None:
            if lib_version < (19, 9):
                warnings.warn(
                    "This version of MediaInfo (v{}) does not support resetting all "
                    "options to their default values, passing it custom options is not recommended "
                    "and may result in unpredictable behavior, see "
                    "https://github.com/MediaArea/MediaInfoLib/issues/1128".format(lib_version_str),
                    RuntimeWarning,
                )
            for option_name, option_value in mediainfo_options.items():
                lib.MediaInfo_Option(handle, option_name, option_value)
        try:
            filename.seek(0, 2)
            file_size = filename.tell()
            filename.seek(0)
        except AttributeError:  # filename is not a file-like object
            file_size = None

        if file_size is not None:  # We have a file-like object, use the buffer protocol:
            # Some file-like objects do not have a mode
            if "b" not in getattr(filename, "mode", "b"):
                raise ValueError("File should be opened in binary mode")
            lib.MediaInfo_Open_Buffer_Init(handle, file_size, 0)
            while True:
                buffer = filename.read(64 * 1024)
                if buffer:
                    # https://github.com/MediaArea/MediaInfoLib/blob/v20.09/Source/MediaInfo/File__Analyze.h#L1429
                    # 4th bit = finished
                    if lib.MediaInfo_Open_Buffer_Continue(handle, buffer, len(buffer)) & 0x08:
                        break
                    # Ask MediaInfo if we need to seek
                    seek = lib.MediaInfo_Open_Buffer_Continue_GoTo_Get(handle)
                    # https://github.com/MediaArea/MediaInfoLib/blob/v20.09/Source/MediaInfoDLL/MediaInfoJNI.cpp#L127
                    if seek != ctypes.c_uint64(-1).value:
                        filename.seek(seek)
                        # Inform MediaInfo we have sought
                        lib.MediaInfo_Open_Buffer_Init(handle, file_size, filename.tell())
                else:
                    break
            lib.MediaInfo_Open_Buffer_Finalize(handle)
        else:  # We have a filename, simply pass it:
            filename = cls._normalize_filename(filename)
            # If an error occured
            if lib.MediaInfo_Open(handle, filename) == 0:
                lib.MediaInfo_Close(handle)
                lib.MediaInfo_Delete(handle)
                # If filename doesn't look like a URL and doesn't exist
                if "://" not in filename and not os.path.exists(filename):
                    raise FileNotFoundError(filename)
                # We ran into another kind of error
                raise RuntimeError(
                    "An error occured while opening {}" " with libmediainfo".format(filename)
                )
        info: str = lib.MediaInfo_Inform(handle, 0)
        # Reset all options to their defaults so that they aren't
        # retained when the parse method is called several times
        # https://github.com/MediaArea/MediaInfoLib/issues/1128
        # Do not call it when it is not required because it breaks threads
        # https://github.com/sbraz/pymediainfo/issues/76#issuecomment-575245093
        if mediainfo_options is not None and lib_version >= (19, 9):
            lib.MediaInfo_Option(handle, "Reset", "")
        # Delete the handle
        lib.MediaInfo_Close(handle)
        lib.MediaInfo_Delete(handle)
        if output is None:
            return cls(info, encoding_errors)
        return info

    def to_data(self) -> Dict[str, Any]:
        """
        Returns a dict representation of the object's :py:class:`Tracks <Track>`.

        :rtype: dict
        """
        return {"tracks": [_.to_data() for _ in self.tracks]}

    def to_json(self) -> str:
        """
        Returns a JSON representation of the object's :py:class:`Tracks <Track>`.

        :rtype: str
        """
        return json.dumps(self.to_data())
