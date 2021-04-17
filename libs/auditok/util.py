"""
.. autosummary::
    :toctree: generated/

    AudioEnergyValidator
    AudioReader
    Recorder
    make_duration_formatter
    make_channel_selector
"""
from abc import ABC, abstractmethod
import warnings
from functools import partial
from .io import (
    AudioIOError,
    AudioSource,
    from_file,
    BufferAudioSource,
    PyAudioSource,
    get_audio_source,
)
from .exceptions import (
    DuplicateArgument,
    TooSamllBlockDuration,
    TimeFormatError,
)

try:
    from . import signal_numpy as signal
except ImportError:
    from . import signal


__all__ = [
    "make_duration_formatter",
    "make_channel_selector",
    "DataSource",
    "DataValidator",
    "StringDataSource",
    "ADSFactory",
    "AudioDataSource",
    "AudioReader",
    "Recorder",
    "AudioEnergyValidator",
]


def make_duration_formatter(fmt):
    """
    Make and return a function used to format durations in seconds. Accepted
    format directives are:

    - ``%S`` : absolute number of seconds with 3 decimals. This direction should
      be used alone.
    - ``%i`` : milliseconds
    - ``%s`` : seconds
    - ``%m`` : minutes
    - ``%h`` : hours

    These last 4 directives should all be specified. They can be placed anywhere
    in the input string.

    Parameters
    ----------
    fmt : str
        duration format.

    Returns
    -------
    formatter : callable
        a function that takes a duration in seconds (float) and returns a string
        that corresponds to that duration.

    Raises
    ------
    TimeFormatError
        if the format contains an unknown directive.

    Examples
    --------

    Using ``%S``:

    .. code:: python

        formatter = make_duration_formatter("%S")
        formatter(123.589)
        '123.589'
        formatter(123)
        '123.000'

    Using the other directives:

    .. code:: python

        formatter = make_duration_formatter("%h:%m:%s.%i")
        formatter(3600+120+3.25)
        '01:02:03.250'

        formatter = make_duration_formatter("%h hrs, %m min, %s sec and %i ms")
        formatter(3600+120+3.25)
        '01 hrs, 02 min, 03 sec and 250 ms'

        # omitting one of the 4 directives might result in a wrong duration
        formatter = make_duration_formatter("%m min, %s sec and %i ms")
        formatter(3600+120+3.25)
        '02 min, 03 sec and 250 ms'
    """
    if fmt == "%S":

        def fromatter(seconds):
            return "{:.3f}".format(seconds)

    elif fmt == "%I":

        def fromatter(seconds):
            return "{0}".format(int(seconds * 1000))

    else:
        fmt = fmt.replace("%h", "{hrs:02d}")
        fmt = fmt.replace("%m", "{mins:02d}")
        fmt = fmt.replace("%s", "{secs:02d}")
        fmt = fmt.replace("%i", "{millis:03d}")
        try:
            i = fmt.index("%")
            raise TimeFormatError(
                "Unknown time format directive '{0}'".format(fmt[i : i + 2])
            )
        except ValueError:
            pass

        def fromatter(seconds):
            millis = int(seconds * 1000)
            hrs, millis = divmod(millis, 3600000)
            mins, millis = divmod(millis, 60000)
            secs, millis = divmod(millis, 1000)
            return fmt.format(hrs=hrs, mins=mins, secs=secs, millis=millis)

    return fromatter


def make_channel_selector(sample_width, channels, selected=None):
    """Create and return a callable used for audio channel selection. The
    returned selector can be used as `selector(audio_data)` and returns data
    that contains selected channel only.

    Importantly, if `selected` is None or equals "any", `selector(audio_data)`
    will separate and return a list of available channels:
    `[data_channe_1, data_channe_2, ...].`

    Note also that returned `selector` expects `bytes` format for input data but
    does notnecessarily return a `bytes` object. In fact, in order to extract
    the desired channel (or compute the average channel if `selected` = "avg"),
    it first converts input data into a `array.array` (or `numpy.ndarray`)
    object. After channel of interst is selected/computed, it is returned as
    such, without any reconversion to `bytes`. This behavior is wanted for
    efficiency purposes because returned objects can be directly used as buffers
    of bytes. In any case, returned objects can be converted back to `bytes`
    using `bytes(obj)`.

    Exception to this is the special case where `channels` = 1 in which input
    data is returned without any processing.


    Parameters
    ----------
    sample_width : int
        number of bytes used to encode one audio sample, should be 1, 2 or 4.
    channels : int
        number of channels of raw audio data that the returned selector should
        expect.
    selected : int or str, default: None
        audio channel to select and return when calling `selector(raw_data)`. It
        should be an int >= `-channels` and < `channels`. If one of "mix",
        "avg" or "average" is passed then `selector` will return the average
        channel of audio data. If None or "any", return a list of all available
        channels at each call.

    Returns
    -------
    selector : callable
        a callable that can be used as `selector(audio_data)` and returns data
        that contains channel of interst.

    Raises
    ------
    ValueError
        if `sample_width` is not one of 1, 2 or 4, or if `selected` has an
        unexpected value.
    """
    fmt = signal.FORMAT.get(sample_width)
    if fmt is None:
        err_msg = "'sample_width' must be 1, 2 or 4, given: {}"
        raise ValueError(err_msg.format(sample_width))
    if channels == 1:
        return lambda x: x

    if isinstance(selected, int):
        if selected < 0:
            selected += channels
        if selected < 0 or selected >= channels:
            err_msg = "Selected channel must be >= -channels and < channels"
            err_msg += ", given: {}"
            raise ValueError(err_msg.format(selected))
        return partial(
            signal.extract_single_channel,
            fmt=fmt,
            channels=channels,
            selected=selected,
        )

    if selected in ("mix", "avg", "average"):
        if channels == 2:
            # when data is stereo, using audioop when possible is much faster
            return partial(
                signal.compute_average_channel_stereo,
                sample_width=sample_width,
            )

        return partial(
            signal.compute_average_channel, fmt=fmt, channels=channels
        )

    if selected in (None, "any"):
        return partial(signal.separate_channels, fmt=fmt, channels=channels)

    raise ValueError(
        "Selected channel must be an integer, None (alias 'any') or 'average' "
        "(alias 'avg' or 'mix')"
    )


class DataSource(ABC):
    """
    Base class for objects passed to :func:`StreamTokenizer.tokenize`.
    Subclasses should implement a :func:`DataSource.read` method.
    """

    @abstractmethod
    def read(self):
        """
        Read a block (i.e., window) of data read from this source.
        If no more data is available, return None.
        """


class DataValidator(ABC):
    """
    Base class for a validator object used by :class:`.core.StreamTokenizer`
    to check if read data is valid.
    Subclasses should implement :func:`is_valid` method.
    """

    @abstractmethod
    def is_valid(self, data):
        """
        Check whether `data` is valid
        """


class AudioEnergyValidator(DataValidator):
    """
    A validator based on audio signal energy. For an input window of `N` audio
    samples (see :func:`AudioEnergyValidator.is_valid`), the energy is computed
    as:

    .. math:: energy = 20 \log(\sqrt({1}/{N}\sum_{i}^{N}{a_i}^2))  % # noqa: W605

    where `a_i` is the i-th audio sample.

    Parameters
    ----------
    energy_threshold : float
        minimum energy that audio window should have to be valid.
    sample_width : int
        size in bytes of one audio sample.
    channels : int
        number of channels of audio data.
    use_channel : {None, "any", "mix", "avg", "average"} or int
        channel to use for energy computation. The following values are
        accepted:

        - None (alias "any") : compute energy for each of the channels and return
          the maximum value.
        - "mix" (alias "avg" or "average") : compute the average channel then
          compute its energy.
        - int (>= 0 , < `channels`) : compute the energy of the specified channel
          and ignore the other ones.

    Returns
    -------
    energy : float
        energy of the audio window.
    """

    def __init__(
        self, energy_threshold, sample_width, channels, use_channel=None
    ):
        self._sample_width = sample_width
        self._selector = make_channel_selector(
            sample_width, channels, use_channel
        )
        if channels == 1 or use_channel not in (None, "any"):
            self._energy_fn = signal.calculate_energy_single_channel
        else:
            self._energy_fn = signal.calculate_energy_multichannel
        self._energy_threshold = energy_threshold

    def is_valid(self, data):
        """

        Parameters
        ----------
        data : bytes-like
            array of raw audio data

        Returns
        -------
        bool
            True if the energy of audio data is >= threshold, False otherwise.
        """
        log_energy = self._energy_fn(self._selector(data), self._sample_width)
        return log_energy >= self._energy_threshold


class StringDataSource(DataSource):
    """
    Class that represent a :class:`DataSource` as a string buffer.
    Each call to :func:`DataSource.read` returns on character and moves one
    step forward. If the end of the buffer is reached, :func:`read` returns
    None.

    Parameters
    ----------
    data : str
        a string object used as data.

    """

    def __init__(self, data):

        self._data = None
        self._current = 0
        self.set_data(data)

    def read(self):
        """
        Read one character from buffer.

        Returns
        -------
        char : str
            current character or None if end of buffer is reached.
        """

        if self._current >= len(self._data):
            return None
        self._current += 1
        return self._data[self._current - 1]

    def set_data(self, data):
        """
        Set a new data buffer.

        Parameters
        ----------
        data : str
            new data buffer.
        """

        if not isinstance(data, str):
            raise ValueError("data must an instance of str")
        self._data = data
        self._current = 0


class ADSFactory:
    """
    .. deprecated:: 2.0.0
          `ADSFactory` will be removed in auditok 2.0.1, use instances of
          :class:`AudioReader` instead.

    Factory class that makes it easy to create an
    :class:`AudioDataSource` object that implements
    :class:`DataSource` and can therefore be passed to
    :func:`auditok.core.StreamTokenizer.tokenize`.

    Whether you read audio data from a file, the microphone or a memory buffer,
    this factory instantiates and returns the right
    :class:`AudioDataSource` object.

    There are many other features you want a :class:`AudioDataSource` object to
    have, such as: memorize all read audio data so that you can rewind and reuse
    it (especially useful when reading data from the microphone), read a fixed
    amount of data (also useful when reading from the microphone), read
    overlapping audio frames (often needed when dosing a spectral analysis of
    data).

    :func:`ADSFactory.ads` automatically creates and return object with the
    desired behavior according to the supplied keyword arguments.
    """

    @staticmethod  # noqa: C901
    def _check_normalize_args(kwargs):

        for k in kwargs:
            if k not in [
                "block_dur",
                "hop_dur",
                "block_size",
                "hop_size",
                "max_time",
                "record",
                "audio_source",
                "filename",
                "data_buffer",
                "frames_per_buffer",
                "sampling_rate",
                "sample_width",
                "channels",
                "sr",
                "sw",
                "ch",
                "asrc",
                "fn",
                "fpb",
                "db",
                "mt",
                "rec",
                "bd",
                "hd",
                "bs",
                "hs",
            ]:
                raise ValueError("Invalid argument: {0}".format(k))

        if "block_dur" in kwargs and "bd" in kwargs:
            raise DuplicateArgument(
                "Either 'block_dur' or 'bd' must be specified, not both"
            )

        if "hop_dur" in kwargs and "hd" in kwargs:
            raise DuplicateArgument(
                "Either 'hop_dur' or 'hd' must be specified, not both"
            )

        if "block_size" in kwargs and "bs" in kwargs:
            raise DuplicateArgument(
                "Either 'block_size' or 'bs' must be specified, not both"
            )

        if "hop_size" in kwargs and "hs" in kwargs:
            raise DuplicateArgument(
                "Either 'hop_size' or 'hs' must be specified, not both"
            )

        if "max_time" in kwargs and "mt" in kwargs:
            raise DuplicateArgument(
                "Either 'max_time' or 'mt' must be specified, not both"
            )

        if "audio_source" in kwargs and "asrc" in kwargs:
            raise DuplicateArgument(
                "Either 'audio_source' or 'asrc' must be specified, not both"
            )

        if "filename" in kwargs and "fn" in kwargs:
            raise DuplicateArgument(
                "Either 'filename' or 'fn' must be specified, not both"
            )

        if "data_buffer" in kwargs and "db" in kwargs:
            raise DuplicateArgument(
                "Either 'filename' or 'db' must be specified, not both"
            )

        if "frames_per_buffer" in kwargs and "fbb" in kwargs:
            raise DuplicateArgument(
                "Either 'frames_per_buffer' or 'fpb' must be specified, not "
                "both"
            )

        if "sampling_rate" in kwargs and "sr" in kwargs:
            raise DuplicateArgument(
                "Either 'sampling_rate' or 'sr' must be specified, not both"
            )

        if "sample_width" in kwargs and "sw" in kwargs:
            raise DuplicateArgument(
                "Either 'sample_width' or 'sw' must be specified, not both"
            )

        if "channels" in kwargs and "ch" in kwargs:
            raise DuplicateArgument(
                "Either 'channels' or 'ch' must be specified, not both"
            )

        if "record" in kwargs and "rec" in kwargs:
            raise DuplicateArgument(
                "Either 'record' or 'rec' must be specified, not both"
            )

        kwargs["bd"] = kwargs.pop("block_dur", None) or kwargs.pop("bd", None)
        kwargs["hd"] = kwargs.pop("hop_dur", None) or kwargs.pop("hd", None)
        kwargs["bs"] = kwargs.pop("block_size", None) or kwargs.pop("bs", None)
        kwargs["hs"] = kwargs.pop("hop_size", None) or kwargs.pop("hs", None)
        kwargs["mt"] = kwargs.pop("max_time", None) or kwargs.pop("mt", None)
        kwargs["asrc"] = kwargs.pop("audio_source", None) or kwargs.pop(
            "asrc", None
        )
        kwargs["fn"] = kwargs.pop("filename", None) or kwargs.pop("fn", None)
        kwargs["db"] = kwargs.pop("data_buffer", None) or kwargs.pop("db", None)

        record = kwargs.pop("record", False)
        if not record:
            record = kwargs.pop("rec", False)
            if not isinstance(record, bool):
                raise TypeError("'record' must be a boolean")

        kwargs["rec"] = record

        # keep long names for arguments meant for BufferAudioSource
        # and PyAudioSource
        if "frames_per_buffer" in kwargs or "fpb" in kwargs:
            kwargs["frames_per_buffer"] = kwargs.pop(
                "frames_per_buffer", None
            ) or kwargs.pop("fpb", None)

        if "sampling_rate" in kwargs or "sr" in kwargs:
            kwargs["sampling_rate"] = kwargs.pop(
                "sampling_rate", None
            ) or kwargs.pop("sr", None)

        if "sample_width" in kwargs or "sw" in kwargs:
            kwargs["sample_width"] = kwargs.pop(
                "sample_width", None
            ) or kwargs.pop("sw", None)

        if "channels" in kwargs or "ch" in kwargs:
            kwargs["channels"] = kwargs.pop("channels", None) or kwargs.pop(
                "ch", None
            )

    @staticmethod
    def ads(**kwargs):
        """
        Create an return an :class:`AudioDataSource`. The type and
        behavior of the object is the result
        of the supplied parameters. Called without any parameters, the class
        will read audio data from the available built-in microphone with the
        default parameters.

        Parameters
        ----------
        sampling_rate, sr : int, default: 16000
            number of audio samples per second of input audio stream.
        sample_width, sw : int, default: 2
            number of bytes per sample, must be one of 1, 2 or 4
        channels, ch : int, default: 1
            number of audio channels, only a value of 1 is currently accepted.
        frames_per_buffer, fpb : int, default: 1024
            number of samples of PyAudio buffer.
        audio_source, asrc : `AudioSource`
            `AudioSource` to read data from
        filename, fn : str
            create an `AudioSource` object using this file
        data_buffer, db : str
            build an `io.BufferAudioSource` using data in `data_buffer`.
            If this keyword is used,
            `sampling_rate`, `sample_width` and `channels` are passed to
            `io.BufferAudioSource` constructor and used instead of default
            values.
        max_time, mt : float
            maximum time (in seconds) to read. Default behavior: read until
            there is no more data
            available.
        record, rec : bool, default = False
            save all read data in cache. Provide a navigable object which has a
            `rewind` method.
        block_dur, bd : float
            processing block duration in seconds. This represents the quantity
            of audio data to return each time the :func:`read` method is
            invoked. If `block_dur` is 0.025 (i.e. 25 ms) and the sampling rate
            is 8000 and the sample width is 2 bytes, :func:`read` returns a
            buffer of 0.025 * 8000 * 2 = 400 bytes at most. This parameter will
            be looked for (and used if available) before `block_size`. If
            neither parameter is given, `block_dur` will be set to 0.01 second
            (i.e. 10 ms)
        hop_dur, hd : float
            quantity of data to skip from current processing window. if
            `hop_dur` is supplied then there will be an overlap of `block_dur`
            - `hop_dur` between two adjacent blocks. This parameter will be
            looked for (and used if available) before `hop_size`.
            If neither parameter is given, `hop_dur` will be set to `block_dur`
            which means that there will be no overlap between two consecutively
            read blocks.
        block_size, bs : int
            number of samples to read each time the `read` method is called.
            Default: a block size that represents a window of 10ms, so for a
            sampling rate of 16000, the default `block_size` is 160 samples,
            for a rate of 44100, `block_size` = 441 samples, etc.
        hop_size, hs : int
            determines the number of overlapping samples between two adjacent
            read windows. For a `hop_size` of value *N*, the overlap is
            `block_size` - *N*. Default : `hop_size` = `block_size`, means that
            there is no overlap.

        Returns
        -------
        audio_data_source : AudioDataSource
            an `AudioDataSource` object build with input parameters.
        """
        warnings.warn(
            "'ADSFactory' is deprecated and will be removed in a future "
            "release. Please use AudioReader class instead.",
            DeprecationWarning,
        )

        # check and normalize keyword arguments
        ADSFactory._check_normalize_args(kwargs)

        block_dur = kwargs.pop("bd")
        hop_dur = kwargs.pop("hd")
        block_size = kwargs.pop("bs")
        hop_size = kwargs.pop("hs")
        max_time = kwargs.pop("mt")
        audio_source = kwargs.pop("asrc")
        filename = kwargs.pop("fn")
        data_buffer = kwargs.pop("db")
        record = kwargs.pop("rec")

        # Case 1: an audio source is supplied
        if audio_source is not None:
            if (filename, data_buffer) != (None, None):
                raise Warning(
                    "You should provide one of 'audio_source', 'filename' or \
                    'data_buffer' keyword parameters. 'audio_source' will be \
                    used"
                )

        # Case 2: a file name is supplied
        elif filename is not None:
            if data_buffer is not None:
                raise Warning(
                    "You should provide one of 'filename' or 'data_buffer'\
                 keyword parameters. 'filename' will be used"
                )
            audio_source = from_file(filename)

        # Case 3: a data_buffer is supplied
        elif data_buffer is not None:
            audio_source = BufferAudioSource(data=data_buffer, **kwargs)

        # Case 4: try to access native audio input
        else:
            audio_source = PyAudioSource(**kwargs)

        if block_dur is not None:
            if block_size is not None:
                raise DuplicateArgument(
                    "Either 'block_dur' or 'block_size' can be specified, not \
                    both"
                )
        elif block_size is not None:
            block_dur = block_size / audio_source.sr
        else:
            block_dur = 0.01  # 10 ms

        # Read overlapping blocks of data
        if hop_dur is not None:
            if hop_size is not None:
                raise DuplicateArgument(
                    "Either 'hop_dur' or 'hop_size' can be specified, not both"
                )
        elif hop_size is not None:
            hop_dur = hop_size / audio_source.sr

        ads = AudioDataSource(
            audio_source,
            block_dur=block_dur,
            hop_dur=hop_dur,
            record=record,
            max_read=max_time,
        )
        return ads


class _AudioReadingProxy:
    def __init__(self, audio_source):

        self._audio_source = audio_source

    def rewind(self):
        if self.rewindable:
            self._audio_source.rewind()
        else:
            raise AudioIOError("Audio stream is not rewindable")

    def rewindable(self):
        try:
            return self._audio_source.rewindable
        except AttributeError:
            return False

    def is_open(self):
        return self._audio_source.is_open()

    def open(self):
        self._audio_source.open()

    def close(self):
        self._audio_source.close()

    def read(self, size):
        return self._audio_source.read(size)

    @property
    def data(self):
        err_msg = "This AudioReader is not a recorder, no recorded data can "
        err_msg += "be retrieved"
        raise AttributeError(err_msg)

    def __getattr__(self, name):
        return getattr(self._audio_source, name)


class _Recorder(_AudioReadingProxy):
    """
    Class for `AudioReader` objects that can record all data they read. Useful
    when reading data from microphone.
    """

    def __init__(self, audio_source):
        super(_Recorder, self).__init__(audio_source)
        self._cache = []
        self._read_block = self._read_and_cache
        self._read_from_cache = False
        self._data = None

    def read(self, size):
        return self._read_block(size)

    @property
    def data(self):
        if self._data is None:
            err_msg = "Unrewinded recorder. `rewind` should be called before "
            err_msg += "accessing recorded data"
            raise RuntimeError(err_msg)
        return self._data

    def rewindable(self):
        return True

    def rewind(self):
        if self._read_from_cache:
            self._audio_source.rewind()
        else:
            self._data = b"".join(self._cache)
            self._cache = None
            self._audio_source = BufferAudioSource(
                self._data, self.sr, self.sw, self.ch
            )
            self._read_block = self._audio_source.read
            self.open()
            self._read_from_cache = True

    def _read_and_cache(self, size):
        # Read and save read data
        block = self._audio_source.read(size)
        if block is not None:
            self._cache.append(block)
        return block


class _Limiter(_AudioReadingProxy):
    """
    Class for `AudioReader` objects that can read a fixed amount of data.
    This can be useful when reading data from the microphone or from large
    audio files.
    """

    def __init__(self, audio_source, max_read):
        super(_Limiter, self).__init__(audio_source)
        self._max_read = max_read
        self._max_samples = round(max_read * self.sr)
        self._bytes_per_sample = self.sw * self.ch
        self._read_samples = 0

    @property
    def data(self):
        data = self._audio_source.data
        max_read_bytes = self._max_samples * self._bytes_per_sample
        return data[:max_read_bytes]

    @property
    def max_read(self):
        return self._max_read

    def read(self, size):
        size = min(self._max_samples - self._read_samples, size)
        if size <= 0:
            return None
        block = self._audio_source.read(size)
        if block is None:
            return None
        self._read_samples += len(block) // self._bytes_per_sample
        return block

    def rewind(self):
        super(_Limiter, self).rewind()
        self._read_samples = 0


class _FixedSizeAudioReader(_AudioReadingProxy):
    """
    Class to read fixed-size audio windows from source.
    """

    def __init__(self, audio_source, block_dur):
        super(_FixedSizeAudioReader, self).__init__(audio_source)

        if block_dur <= 0:
            raise ValueError(
                "block_dur must be > 0, given: {}".format(block_dur)
            )

        self._block_size = int(block_dur * self.sr)
        if self._block_size == 0:
            err_msg = "Too small block_dur ({0:f}) for sampling rate ({1}). "
            err_msg += "block_dur should cover at least one sample "
            err_msg += "(i.e. 1/{1})"
            raise TooSamllBlockDuration(
                err_msg.format(block_dur, self.sr), block_dur, self.sr
            )

    def read(self):
        return self._audio_source.read(self._block_size)

    @property
    def block_size(self):
        return self._block_size

    @property
    def block_dur(self):
        return self._block_size / self.sr

    def __getattr__(self, name):
        return getattr(self._audio_source, name)


class _OverlapAudioReader(_FixedSizeAudioReader):
    """
    Class for `AudioReader` objects that can read and return overlapping audio
    windows.
    """

    def __init__(self, audio_source, block_dur, hop_dur):

        if hop_dur >= block_dur:
            raise ValueError('"hop_dur" should be < "block_dur"')

        super(_OverlapAudioReader, self).__init__(audio_source, block_dur)

        self._hop_size = int(hop_dur * self.sr)
        self._blocks = self._iter_blocks_with_overlap()

    def _iter_blocks_with_overlap(self):
        while not self.is_open():
            yield AudioIOError
        block = self._audio_source.read(self._block_size)
        if block is None:
            yield None

        _hop_size_bytes = (
            self._hop_size * self._audio_source.sw * self._audio_source.ch
        )
        cache = block[_hop_size_bytes:]
        yield block

        while True:
            block = self._audio_source.read(self._hop_size)
            if block:
                block = cache + block
                cache = block[_hop_size_bytes:]
                yield block
                continue
            yield None

    def read(self):
        try:
            block = next(self._blocks)
            if block == AudioIOError:
                raise AudioIOError("Audio Stream is not open.")
            return block
        except StopIteration:
            return None

    def rewind(self):
        super(_OverlapAudioReader, self).rewind()
        self._blocks = self._iter_blocks_with_overlap()

    @property
    def hop_size(self):
        return self._hop_size

    @property
    def hop_dur(self):
        return self._hop_size / self.sr

    def __getattr__(self, name):
        return getattr(self._audio_source, name)


class AudioReader(DataSource):
    """
    Class to read fixed-size chunks of audio data from a source. A source can
    be a file on disk, standard input (with `input` = "-") or microphone. This
    is normally used by tokenization algorithms that expect source objects with
    a `read` function that returns a windows of data of the same size at each
    call expect when remaining data does not make up a full window.

    Objects of this class can be set up to return audio windows with a given
    overlap and to record the whole stream for later access (useful when
    reading data from the microphone). They can also have
    a limit for the maximum amount of data to read.

    Parameters
    ----------
    input : str, bytes, AudioSource, AudioReader, AudioRegion or None
        input audio data. If the type of the passed argument is `str`, it should
        be a path to an existing audio file. "-" is interpreted as standardinput.
        If the type is `bytes`, input is considered as a buffer of raw audio
        data. If None, read audio from microphone. Every object that is not an
        :class:`AudioReader` will be transformed, when possible, into an
        :class:`AudioSource` before processing. If it is an `str` that refers to
        a raw audio file, `bytes` or None, audio parameters should be provided
        using kwargs (i.e., `samplig_rate`, `sample_width` and `channels` or
        their alias).
    block_dur: float, default: 0.01
        length in seconds of audio windows to return at each `read` call.
    hop_dur: float, default: None
        length in seconds of data amount to skip from previous window. If
        defined, it is used to compute the temporal overlap between previous and
        current window (nameply `overlap = block_dur - hop_dur`). Default, None,
        means that consecutive windows do not overlap.
    record: bool, default: False
        whether to record read audio data for later access. If True, audio data
        can be retrieved by first calling `rewind()`, then using the `data`
        property. Note that once `rewind()` is called, no new data will be read
        from source (subsequent `read()` call will read data from cache) and
        that there's no need to call `rewind()` again to access `data` property.
    max_read: float, default: None
        maximum amount of audio data to read in seconds. Default is None meaning
        that data will be read until end of stream is reached or, when reading
        from microphone a Ctrl-C is sent.

    When `input` is None, of type bytes or a raw audio files some of the
    follwing kwargs are mandatory.

    Other Parameters
    ----------------
    audio_format, fmt : str
        type of audio data (e.g., wav, ogg, flac, raw, etc.). This will only be
        used if `input` is a string path to an audio file. If not given, audio
        type will be guessed from file name extension or from file header.
    sampling_rate, sr : int
        sampling rate of audio data. Required if `input` is a raw audio file, is
        a bytes object or None (i.e., read from microphone).
    sample_width, sw : int
        number of bytes used to encode one audio sample, typically 1, 2 or 4.
        Required for raw data, see `sampling_rate`.
    channels, ch : int
        number of channels of audio data. Required for raw data, see
        `sampling_rate`.
    use_channel, uc : {None, "any", "mix", "avg", "average"} or int
        which channel to use for split if `input` has multiple audio channels.
        Regardless of which channel is used for splitting, returned audio events
        contain data from *all* the channels of `input`. The following values
        are accepted:

        - None (alias "any"): accept audio activity from any channel, even if
          other channels are silent. This is the default behavior.

        - "mix" (alias "avg" or "average"): mix down all channels (i.e., compute
          average channel) and split the resulting channel.

        - int (>= 0 , < `channels`): use one channel, specified by its integer
          id, for split.

    large_file : bool, default: False
        If True, AND if `input` is a path to a *wav* of a *raw* audio file
        (and only these two formats) then audio data is lazily loaded to memory
        (i.e., one analysis window a time). Otherwise the whole file is loaded
        to memory before split. Set to True if the size of the file is larger
        than available memory.
    """

    def __init__(
        self,
        input,
        block_dur=0.01,
        hop_dur=None,
        record=False,
        max_read=None,
        **kwargs
    ):
        if not isinstance(input, AudioSource):
            input = get_audio_source(input, **kwargs)
        self._record = record
        if record:
            input = _Recorder(input)
        if max_read is not None:
            input = _Limiter(input, max_read)
            self._max_read = max_read
        if hop_dur is not None:
            input = _OverlapAudioReader(input, block_dur, hop_dur)
        else:
            input = _FixedSizeAudioReader(input, block_dur)
        self._audio_source = input

    def __repr__(self):
        block_dur, hop_dur, max_read = None, None, None
        if self.block_dur is not None:
            block_dur = "{:.3f}".format(self.block_dur)
        if self.hop_dur is not None:
            hop_dur = "{:.3f}".format(self.hop_dur)
        if self.max_read is not None:
            max_read = "{:.3f}".format(self.max_read)
        return (
            "{cls}(block_dur={block_dur}, "
            "hop_dur={hop_dur}, record={rewindable}, "
            "max_read={max_read})"
        ).format(
            cls=self.__class__.__name__,
            block_dur=block_dur,
            hop_dur=hop_dur,
            rewindable=self._record,
            max_read=max_read,
        )

    @property
    def rewindable(self):
        return self._record

    @property
    def block_dur(self):
        return self._audio_source.block_size / self._audio_source.sr

    @property
    def hop_dur(self):
        if hasattr(self._audio_source, "hop_dur"):
            return self._audio_source.hop_size / self._audio_source.sr
        return self.block_dur

    @property
    def hop_size(self):
        if hasattr(self._audio_source, "hop_size"):
            return self._audio_source.hop_size
        return self.block_size

    @property
    def max_read(self):
        try:
            return self._audio_source.max_read
        except AttributeError:
            return None

    def read(self):
        return self._audio_source.read()

    def __getattr__(self, name):
        if name in ("data", "rewind") and not self.rewindable:
            raise AttributeError(
                "'AudioReader' has no attribute '{}'".format(name)
            )
        try:
            return getattr(self._audio_source, name)
        except AttributeError:
            raise AttributeError(
                "'AudioReader' has no attribute '{}'".format(name)
            )


# Keep AudioDataSource for compatibility
# Remove in a future version when ADSFactory is removed
AudioDataSource = AudioReader


class Recorder(AudioReader):
    """Class to read fixed-size chunks of audio data from a source and keeps
    data in a cache. Using this class is equivalent to initializing
    :class:`AudioReader` with `record=True`. For more information about the
    other parameters see :class:`AudioReader`.

    Once the desired amount of data is read, you can call the :func:`rewind`
    method then get the recorded data via the :attr:`data` attribute. You can also
    re-read cached data one window a time by calling :func:`read`.
    """

    def __init__(
        self, input, block_dur=0.01, hop_dur=None, max_read=None, **kwargs
    ):
        super().__init__(
            input,
            block_dur=block_dur,
            hop_dur=hop_dur,
            record=True,
            max_read=max_read,
            **kwargs
        )
