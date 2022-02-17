"""
Module for low-level audio input-output operations.

.. autosummary::
    :toctree: generated/

    AudioSource
    Rewindable
    BufferAudioSource
    WaveAudioSource
    PyAudioSource
    StdinAudioSource
    PyAudioPlayer
    from_file
    to_file
    player_for
"""
import os
import sys
import wave
import warnings
from abc import ABC, abstractmethod
from functools import partial
from .exceptions import AudioIOError, AudioParameterError

try:
    from pydub import AudioSegment

    _WITH_PYDUB = True
except ImportError:
    _WITH_PYDUB = False

try:
    from tqdm import tqdm as _tqdm

    DEFAULT_BAR_FORMAT_TQDM = "|" + "{bar}" + "|" + "[{elapsed}/{duration}]"
    DEFAULT_NCOLS_TQDM = 30
    DEFAULT_NCOLS_TQDM = 30
    DEFAULT_MIN_INTERVAL_TQDM = 0.05
    _WITH_TQDM = True
except ImportError:
    _WITH_TQDM = False


__all__ = [
    "AudioSource",
    "Rewindable",
    "BufferAudioSource",
    "RawAudioSource",
    "WaveAudioSource",
    "PyAudioSource",
    "StdinAudioSource",
    "PyAudioPlayer",
    "from_file",
    "to_file",
    "player_for",
]

DEFAULT_SAMPLING_RATE = 16000
DEFAULT_SAMPLE_WIDTH = 2
DEFAULT_NB_CHANNELS = 1


def check_audio_data(data, sample_width, channels):
    sample_size_bytes = int(sample_width * channels)
    nb_samples = len(data) // sample_size_bytes
    if nb_samples * sample_size_bytes != len(data):
        raise AudioParameterError(
            "The length of audio data must be an integer "
            "multiple of `sample_width * channels`"
        )


def _guess_audio_format(fmt, filename):
    if fmt is None:
        extension = os.path.splitext(filename.lower())[1][1:]
        if extension:
            fmt = extension
        else:
            return None
    fmt = fmt.lower()
    if fmt == "wave":
        fmt = "wav"
    return fmt


def _get_audio_parameters(param_dict):
    """
    Get audio parameters from a dictionary of parameters. An audio parameter can
    have a long name or a short name. If the long name is present, the short
    name will be ignored. If neither is present then `AudioParameterError` is
    raised.

    Expected parameters are:

        - `sampling_rate`, `sr` : int, sampling rate.

        - `sample_width`, `sw` : int, sample size in bytes.

        - `channels`, `ch` : int, number of channels.

    Returns
    -------
    audio_parameters : tuple
        a tuple for audio parameters as (sampling_rate, sample_width, channels).
    """
    err_message = (
        "'{ln}' (or '{sn}') must be a positive integer, found: '{val}'"
    )
    parameters = []
    for (long_name, short_name) in (
        ("sampling_rate", "sr"),
        ("sample_width", "sw"),
        ("channels", "ch"),
    ):
        param = param_dict.get(long_name, param_dict.get(short_name))
        if param is None or not isinstance(param, int) or param <= 0:
            raise AudioParameterError(
                err_message.format(ln=long_name, sn=short_name, val=param)
            )
        parameters.append(param)
    sampling_rate, sample_width, channels = parameters
    return sampling_rate, sample_width, channels


class AudioSource(ABC):
    """
    Base class for audio source objects.

    Subclasses should implement methods to open/close and audio stream
    and read the desired amount of audio samples.

    Parameters
    ----------
    sampling_rate : int
        number of samples per second of audio data.
    sample_width : int
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int
        number of channels of audio data.
    """

    def __init__(
        self, sampling_rate, sample_width, channels,
    ):

        if sample_width not in (1, 2, 4):
            raise AudioParameterError(
                "Sample width must be one of: 1, 2 or 4 (bytes)"
            )

        self._sampling_rate = sampling_rate
        self._sample_width = sample_width
        self._channels = channels

    @abstractmethod
    def is_open(self):
        """Return True if audio source is open, False otherwise."""

    @abstractmethod
    def open(self):
        """Open audio source."""

    @abstractmethod
    def close(self):
        """Close audio source."""

    @abstractmethod
    def read(self, size):
        """
        Read and return `size` audio samples at most.

        Parameters
        -----------
        size : int
            Number of samples to read.

        Returns
        -------
        data : bytes
            Audio data as a bytes object of length `N * sample_width * channels`
            where `N` equals:

            - `size` if `size` <= remaining samples

            - remaining samples if `size` > remaining samples
        """

    @property
    def sampling_rate(self):
        """Number of samples per second of audio stream."""
        return self._sampling_rate

    @property
    def sr(self):
        """Number of samples per second of audio stream (alias for
        `sampling_rate)`."""
        return self._sampling_rate

    @property
    def sample_width(self):
        """Number of bytes used to represent one audio sample."""
        return self._sample_width

    @property
    def sw(self):
        """Number of bytes used to represent one audio sample (alias for
        `sample_width`)."""
        return self._sample_width

    @property
    def channels(self):
        """Number of channels in audio stream."""
        return self._channels

    @property
    def ch(self):
        """Number of channels in audio stream (alias for `channels`)."""
        return self.channels


class Rewindable(AudioSource):
    """
    Base class for rewindable audio streams.

    Subclasses should implement a method to return back to the start of an the
    stream (`rewind`), as well as a property getter/setter named `position` that
    reads/sets stream position expressed in number of samples.
    """

    @abstractmethod
    def rewind(self):
        """Go back to the beginning of audio stream."""

    @property
    @abstractmethod
    def position(self):
        """Return stream position in number of samples."""

    @position.setter
    @abstractmethod
    def position(self, position):
        """Set stream position in number of samples."""

    @property
    def position_s(self):
        """Return stream position in seconds."""
        return self.position / self.sampling_rate

    @position_s.setter
    def position_s(self, position_s):
        """Set stream position in seconds."""
        self.position = int(self.sampling_rate * position_s)

    @property
    def position_ms(self):
        """Return stream position in milliseconds."""
        return (self.position * 1000) // self.sampling_rate

    @position_ms.setter
    def position_ms(self, position_ms):
        """Set stream position in milliseconds."""
        if not isinstance(position_ms, int):
            raise ValueError("position_ms should be an int")
        self.position = int(self.sampling_rate * position_ms / 1000)


class BufferAudioSource(Rewindable):
    """
    An `AudioSource` that encapsulates and reads data from a memory buffer.

    This class implements the `Rewindable` interface.
    Parameters
    ----------
    data : bytes
        audio data
    sampling_rate : int, default: 16000
        number of samples per second of audio data.
    sample_width : int, default: 2
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int, default: 1
        number of channels of audio data.
    """

    def __init__(
        self, data, sampling_rate=16000, sample_width=2, channels=1,
    ):
        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        check_audio_data(data, sample_width, channels)
        self._data = data
        self._sample_size_all_channels = sample_width * channels
        self._current_position_bytes = 0
        self._is_open = False

    def is_open(self):
        return self._is_open

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False
        self.rewind()

    def read(self, size):
        if not self._is_open:
            raise AudioIOError("Stream is not open")
        if size is None or size < 0:
            offset = None
        else:
            bytes_to_read = self._sample_size_all_channels * size
            offset = self._current_position_bytes + bytes_to_read
        data = self._data[self._current_position_bytes : offset]
        if data:
            self._current_position_bytes += len(data)
            return data
        return None

    @property
    def data(self):
        """Get raw audio data as a `bytes` object."""
        return self._data

    def rewind(self):
        self.position = 0

    @property
    def position(self):
        """Get stream position in number of samples"""
        return self._current_position_bytes // self._sample_size_all_channels

    @position.setter
    def position(self, position):
        """Set stream position in number of samples."""
        position *= self._sample_size_all_channels
        if position < 0:
            position += len(self.data)
        if position < 0 or position > len(self.data):
            raise IndexError("Position out of range")
        self._current_position_bytes = position

    @property
    def position_ms(self):
        """Get stream position in milliseconds."""
        return (self._current_position_bytes * 1000) // (
            self._sample_size_all_channels * self.sampling_rate
        )

    @position_ms.setter
    def position_ms(self, position_ms):
        """Set stream position in milliseconds."""
        if not isinstance(position_ms, int):
            raise ValueError("position_ms should be an int")
        self.position = int(self.sampling_rate * position_ms / 1000)


class FileAudioSource(AudioSource):
    """
    Base class `AudioSource`s that read audio data from a file.

    Parameters
    ----------
    sampling_rate : int, default: 16000
        number of samples per second of audio data.
    sample_width : int, default: 2
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int, default: 1
        number of channels of audio data.
    """

    def __init__(self, sampling_rate, sample_width, channels):
        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._audio_stream = None

    def __del__(self):
        if self.is_open():
            self.close()

    def is_open(self):
        return self._audio_stream is not None

    def close(self):
        if self._audio_stream is not None:
            self._audio_stream.close()
            self._audio_stream = None

    @abstractmethod
    def _read_from_stream(self, size):
        """Read data from stream"""

    def read(self, size):
        if not self.is_open():
            raise AudioIOError("Audio stream is not open")
        data = self._read_from_stream(size)
        if not data:
            return None
        return data


class RawAudioSource(FileAudioSource):
    """
    A class for an `AudioSource` that reads data from a raw (headerless) audio
    file.

    This class should be used for large raw audio files to avoid loading the
    whole data to memory.

    Parameters
    ----------
    filename : str
        path to a raw audio file.
    sampling_rate : int
        Number of samples per second of audio data.
    sample_width : int
        Size in bytes of one audio sample. Possible values : 1, 2, 4.
    channels : int
        Number of channels of audio data.
    """

    def __init__(self, file, sampling_rate, sample_width, channels):
        FileAudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._file = file
        self._audio_stream = None
        self._sample_size = sample_width * channels

    def open(self):
        if self._audio_stream is None:
            self._audio_stream = open(self._file, "rb")

    def _read_from_stream(self, size):
        if size is None or size < 0:
            bytes_to_read = None
        else:
            bytes_to_read = size * self._sample_size
        data = self._audio_stream.read(bytes_to_read)
        return data


class WaveAudioSource(FileAudioSource):
    """
    A class for an `AudioSource` that reads data from a wave file.

    This class should be used for large wave files to avoid loading the whole
    data to memory.

    Parameters
    ----------
    filename : str
        path to a valid wave file.
    """

    def __init__(self, filename):
        self._filename = filename
        self._audio_stream = None
        stream = wave.open(self._filename, "rb")
        FileAudioSource.__init__(
            self,
            stream.getframerate(),
            stream.getsampwidth(),
            stream.getnchannels(),
        )
        stream.close()

    def open(self):
        if self._audio_stream is None:
            self._audio_stream = wave.open(self._filename)

    def _read_from_stream(self, size):
        if size is None or size < 0:
            size = -1
        return self._audio_stream.readframes(size)


class PyAudioSource(AudioSource):
    """
    A class for an `AudioSource` that reads data from built-in microphone using
    PyAudio (https://people.csail.mit.edu/hubert/pyaudio/).

    Parameters
    ----------
    sampling_rate : int, default: 16000
        number of samples per second of audio data.
    sample_width : int, default: 2
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int, default: 1
        number of channels of audio data.
    frames_per_buffer : int, default: 1024
        PyAudio number of frames per buffer.
    input_device_index: None or int, default: None
        PyAudio index of audio device to read audio data from. If None default
        device is used.
    """

    def __init__(
        self,
        sampling_rate=16000,
        sample_width=2,
        channels=1,
        frames_per_buffer=1024,
        input_device_index=None,
    ):

        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._chunk_size = frames_per_buffer
        self.input_device_index = input_device_index

        import pyaudio

        self._pyaudio_object = pyaudio.PyAudio()
        self._pyaudio_format = self._pyaudio_object.get_format_from_width(
            self.sample_width
        )
        self._audio_stream = None

    def is_open(self):
        return self._audio_stream is not None

    def open(self):
        self._audio_stream = self._pyaudio_object.open(
            format=self._pyaudio_format,
            channels=self.channels,
            rate=self.sampling_rate,
            input=True,
            output=False,
            input_device_index=self.input_device_index,
            frames_per_buffer=self._chunk_size,
        )

    def close(self):
        if self._audio_stream is not None:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
            self._audio_stream = None

    def read(self, size):
        if self._audio_stream is None:
            raise IOError("Stream is not open")
        if self._audio_stream.is_active():
            data = self._audio_stream.read(size)
            if data is None or len(data) < 1:
                return None
            return data
        return None


class StdinAudioSource(FileAudioSource):
    """
    A class for an `AudioSource` that reads data from standard input.

    Parameters
    ----------
    sampling_rate : int, default: 16000
        number of samples per second of audio data.
    sample_width : int, default: 2
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int, default: 1
        number of channels of audio data.
    """

    def __init__(
        self, sampling_rate=16000, sample_width=2, channels=1,
    ):
        FileAudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._is_open = False
        self._sample_size = sample_width * channels
        self._stream = sys.stdin.buffer

    def is_open(self):
        return self._is_open

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def _read_from_stream(self, size):
        bytes_to_read = size * self._sample_size
        data = self._stream.read(bytes_to_read)
        if data:
            return data
        return None


def _make_tqdm_progress_bar(iterable, total, duration, **tqdm_kwargs):
    fmt = tqdm_kwargs.get("bar_format", DEFAULT_BAR_FORMAT_TQDM)
    fmt = fmt.replace("{duration}", "{:.3f}".format(duration))
    tqdm_kwargs["bar_format"] = fmt

    tqdm_kwargs["ncols"] = tqdm_kwargs.get("ncols", DEFAULT_NCOLS_TQDM)
    tqdm_kwargs["mininterval"] = tqdm_kwargs.get(
        "mininterval", DEFAULT_MIN_INTERVAL_TQDM
    )
    return _tqdm(iterable, total=total, **tqdm_kwargs)


class PyAudioPlayer:
    """
    A class for audio playback using Pyaudio
    (https://people.csail.mit.edu/hubert/pyaudio/).

    Parameters
    ----------
    sampling_rate : int, default: 16000
        number of samples per second of audio data.
    sample_width : int, default: 2
        size in bytes of one audio sample. Possible values: 1, 2 or 4.
    channels : int, default: 1
        number of channels of audio data.
    """

    def __init__(
        self, sampling_rate=16000, sample_width=2, channels=1,
    ):
        if sample_width not in (1, 2, 4):
            raise ValueError("Sample width in bytes must be one of 1, 2 or 4")

        self.sampling_rate = sampling_rate
        self.sample_width = sample_width
        self.channels = channels

        import pyaudio

        self._p = pyaudio.PyAudio()
        self.stream = self._p.open(
            format=self._p.get_format_from_width(self.sample_width),
            channels=self.channels,
            rate=self.sampling_rate,
            input=False,
            output=True,
        )

    def play(self, data, progress_bar=False, **progress_bar_kwargs):
        chunk_gen, nb_chunks = self._chunk_data(data)
        if progress_bar and _WITH_TQDM:
            duration = len(data) / (
                self.sampling_rate * self.sample_width * self.channels
            )
            chunk_gen = _make_tqdm_progress_bar(
                chunk_gen,
                total=nb_chunks,
                duration=duration,
                **progress_bar_kwargs
            )
        if self.stream.is_stopped():
            self.stream.start_stream()
        try:
            for chunk in chunk_gen:
                self.stream.write(chunk)
        except KeyboardInterrupt:
            pass
        self.stream.stop_stream()

    def stop(self):
        if not self.stream.is_stopped():
            self.stream.stop_stream()
        self.stream.close()
        self._p.terminate()

    def _chunk_data(self, data):
        # make audio chunks of 100 ms to allow interruption (like ctrl+c)
        bytes_1_sec = self.sampling_rate * self.sample_width * self.channels
        chunk_size = bytes_1_sec // 10
        # make sure chunk_size is a multiple of sample_width * channels
        chunk_size -= chunk_size % (self.sample_width * self.channels)
        nb_chunks, rest = divmod(len(data), chunk_size)
        if rest > 0:
            nb_chunks += 1
        chunk_gen = (
            data[i : i + chunk_size] for i in range(0, len(data), chunk_size)
        )
        return chunk_gen, nb_chunks


def player_for(source):
    """
    Return an `AudioPlayer` compatible with `source` (i.e., has the same
    sampling rate, sample width and number of channels).

    Parameters
    ----------
    source : AudioSource
        An object that has `sampling_rate`, `sample_width` and `sample_width`
        attributes.

    Returns
    -------
    player : PyAudioPlayer
        An audio player that has the same sampling rate, sample width
        and number of channels as `source`.
    """
    return PyAudioPlayer(
        source.sampling_rate, source.sample_width, source.channels
    )


def get_audio_source(input=None, **kwargs):
    """
    Create and return an AudioSource from input.

    Parameters
    ----------
    input : str, bytes, "-" or None (default)
        source to read audio data from. If `str`, it should be a path to a valid
        audio file. If `bytes`, it is used as raw audio data. If it is "-",
        raw data will be read from stdin. If None, read audio data from the
        microphone using PyAudio.
    kwargs
        audio parameters used to build the `AudioSource` object. Depending on
        the nature of `input`, theses may be omitted (e.g., when `input` is an
        audio file in a popular audio format such as wav, ogg, flac, etc.) or
        include parameters such as `sampling_rate`, `sample_width`, `channels`
        (or their respective short name versions `sr`, `sw` and `ch`) if `input`
        is a path to a raw (headerless) audio file, a bytes object for raw audio
        data or None (to read data from built-in microphone). See the respective
        `AudioSource` classes from more information about possible parameters.

    Returns
    -------
    source : AudioSource
        audio source created from input parameters
    """
    if input == "-":
        return StdinAudioSource(*_get_audio_parameters(kwargs))

    if isinstance(input, bytes):
        return BufferAudioSource(input, *_get_audio_parameters(kwargs))

    # read data from a file
    if input is not None:
        return from_file(filename=input, **kwargs)

    # read data from microphone via pyaudio
    else:
        frames_per_buffer = kwargs.get("frames_per_buffer", 1024)
        input_device_index = kwargs.get("input_device_index")
        return PyAudioSource(
            *_get_audio_parameters(kwargs),
            frames_per_buffer=frames_per_buffer,
            input_device_index=input_device_index
        )


def _load_raw(file, sampling_rate, sample_width, channels, large_file=False):
    """
    Load a raw audio file with standard Python. If `large_file` is True, return
    a `RawAudioSource` object that reads data lazily from disk, otherwise load
    all data to memory and return a `BufferAudioSource` object.

    Parameters
    ----------
    file : str
        path to a raw audio data file.
    sampling_rate : int
        sampling rate of audio data.
    sample_width : int
        size in bytes of one audio sample.
    channels : int
        number of channels of audio data.
    large_file : bool
        if True, return a `RawAudioSource` otherwise a `BufferAudioSource`
        object.

    Returns
    -------
    source : RawAudioSource or BufferAudioSource
        an `AudioSource` that reads data from input file.
    """
    if None in (sampling_rate, sample_width, channels):
        raise AudioParameterError(
            "All audio parameters are required for raw audio files"
        )

    if large_file:
        return RawAudioSource(
            file,
            sampling_rate=sampling_rate,
            sample_width=sample_width,
            channels=channels,
        )

    with open(file, "rb") as fp:
        data = fp.read()
    return BufferAudioSource(
        data,
        sampling_rate=sampling_rate,
        sample_width=sample_width,
        channels=channels,
    )


def _load_wave(file, large_file=False):
    """
    Load a wave audio file with standard Python. If `large_file` is True, return
    a `WaveAudioSource` object that reads data lazily from disk, otherwise load
    all data to memory and return a `BufferAudioSource` object.

    Parameters
    ----------
    file : str
        path to a wav audio data file
    large_file : bool
        if True, return a `WaveAudioSource` otherwise a `BufferAudioSource`
        object.

    Returns
    -------
    source : WaveAudioSource or BufferAudioSource
        an `AudioSource` that reads data from input file.
    """
    if large_file:
        return WaveAudioSource(file)
    with wave.open(file) as fp:
        channels = fp.getnchannels()
        srate = fp.getframerate()
        swidth = fp.getsampwidth()
        data = fp.readframes(-1)
    return BufferAudioSource(
        data, sampling_rate=srate, sample_width=swidth, channels=channels
    )


def _load_with_pydub(file, audio_format=None):
    """
    Open compressed audio or video file using pydub. If a video file
    is passed, its audio track(s) are extracted and loaded.

    Parameters
    ----------
    file : str
        path to audio file.
    audio_format : str, default: None
        string, audio/video file format if known (e.g. raw, webm, wav, ogg)

    Returns
    -------
    source : BufferAudioSource
        an `AudioSource` that reads data from input file.
    """
    func_dict = {
        "mp3": AudioSegment.from_mp3,
        "ogg": AudioSegment.from_ogg,
        "flv": AudioSegment.from_flv,
    }
    open_function = func_dict.get(audio_format, AudioSegment.from_file)
    segment = open_function(file)
    return BufferAudioSource(
        data=segment.raw_data,
        sampling_rate=segment.frame_rate,
        sample_width=segment.sample_width,
        channels=segment.channels,
    )


def from_file(filename, audio_format=None, large_file=False, **kwargs):
    """
    Read audio data from `filename` and return an `AudioSource` object.
    if `audio_format` is None, the appropriate `AudioSource` class is guessed
    from file's extension. `filename` can be a compressed audio or video file.
    This will require installing `pydub` (https://github.com/jiaaro/pydub).

    The normal behavior is to load all audio data to memory from which a
    :class:`BufferAudioSource` object is created. This should be convenient
    most     of the time unless audio file is very large. In that case, and
    in order to load audio data in lazy manner (i.e. read data from disk each
    time :func:`AudioSource.read` is called), `large_file` should be True.

    Note that the current implementation supports only wave and raw formats for
    lazy audio loading.

    If an audio format is `raw`, the following keyword arguments are required:

        - `sampling_rate`, `sr`: int,  sampling rate of audio data.
        - `sample_width`, `sw`: int, size in bytes of one audio sample.
        - `channels`, `ch`: int, number of channels of audio data.

    See also
    --------
    :func:`to_file`.

    Parameters
    ----------
    filename : str
        path to input audio or video file.
    audio_format : str
        audio format used to save data  (e.g. raw, webm, wav, ogg).
    large_file : bool, default: False
        if True, audio won't fully be loaded to memory but only when a window
        is read from disk.


    Other Parameters
    ----------------
    sampling_rate, sr: int
        sampling rate of audio data
    sample_width : int
        sample width (i.e. number of bytes used to represent one audio sample)
    channels : int
        number of channels of audio data

    Returns
    -------
    audio_source : AudioSource
        an :class:`AudioSource` object that reads data from input file.

    Raises
    ------
    `AudioIOError`
        raised if audio data cannot be read in the given
        format or if `format` is `raw` and one or more audio parameters are missing.
    """
    audio_format = _guess_audio_format(audio_format, filename)

    if audio_format == "raw":
        srate, swidth, channels = _get_audio_parameters(kwargs)
        return _load_raw(filename, srate, swidth, channels, large_file)

    if audio_format in ["wav", "wave"]:
        return _load_wave(filename, large_file)
    if large_file:
        err_msg = "if 'large_file` is True file format should be raw or wav"
        raise AudioIOError(err_msg)
    if _WITH_PYDUB:
        return _load_with_pydub(filename, audio_format=audio_format)
    else:
        raise AudioIOError(
            "pydub is required for audio formats other than raw or wav"
        )


def _save_raw(data, file):
    """
    Saves audio data as a headerless (i.e. raw) file.
    See also :func:`to_file`.
    """
    with open(file, "wb") as fp:
        fp.write(data)


def _save_wave(data, file, sampling_rate, sample_width, channels):
    """
    Saves audio data to a wave file.
    See also :func:`to_file`.
    """
    if None in (sampling_rate, sample_width, channels):
        raise AudioParameterError(
            "All audio parameters are required to save wave audio files"
        )
    with wave.open(file, "w") as fp:
        fp.setframerate(sampling_rate)
        fp.setsampwidth(sample_width)
        fp.setnchannels(channels)
        fp.writeframes(data)


def _save_with_pydub(
    data, file, audio_format, sampling_rate, sample_width, channels
):
    """
    Saves audio data with pydub (https://github.com/jiaaro/pydub).
    See also :func:`to_file`.
    """
    segment = AudioSegment(
        data,
        frame_rate=sampling_rate,
        sample_width=sample_width,
        channels=channels,
    )
    with open(file, "wb") as fp:
        segment.export(fp, format=audio_format)


def to_file(data, file, audio_format=None, **kwargs):
    """
    Writes audio data to file. If `audio_format` is `None`, output
    audio format will be guessed from extension. If `audio_format`
    is `None` and `file` comes without an extension then audio
    data will be written as a raw audio file.

    Parameters
    ----------
    data : bytes-like
        audio data to be written. Can be a `bytes`, `bytearray`,
        `memoryview`, `array` or `numpy.ndarray` object.
    file : str
        path to output audio file.
    audio_format : str
        audio format used to save data (e.g. raw, webm, wav, ogg)
    kwargs: dict
        If an audio format other than `raw` is used, the following keyword
        arguments are required:

        - `sampling_rate`, `sr`: int,  sampling rate of audio data.
        - `sample_width`, `sw`: int, size in bytes of one audio sample.
        - `channels`, `ch`: int, number of channels of audio data.

    Raises
    ------
    `AudioParameterError` if output format is different than raw and one or more
    audio parameters are missing. `AudioIOError` if audio data cannot be written
    in the desired format.
    """
    audio_format = _guess_audio_format(audio_format, file)
    if audio_format in (None, "raw"):
        _save_raw(data, file)
        return
    try:
        sampling_rate, sample_width, channels = _get_audio_parameters(kwargs)
    except AudioParameterError as exc:
        err_message = "All audio parameters are required to save formats "
        "other than raw. Error detail: {}".format(exc)
        raise AudioParameterError(err_message)
    if audio_format in ("wav", "wave"):
        _save_wave(data, file, sampling_rate, sample_width, channels)
    elif _WITH_PYDUB:
        _save_with_pydub(
            data, file, audio_format, sampling_rate, sample_width, channels
        )
    else:
        err_message = "cannot write file format {} (file name: {})"
        raise AudioIOError(err_message.format(audio_format, file))
