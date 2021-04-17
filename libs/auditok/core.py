"""
.. autosummary::
    :toctree: generated/

    load
    split
    AudioRegion
    StreamTokenizer
"""
import os
import math
from .util import AudioReader, DataValidator, AudioEnergyValidator
from .io import check_audio_data, to_file, player_for, get_audio_source
from .exceptions import TooSamllBlockDuration

try:
    from . import signal_numpy as signal
except ImportError:
    from . import signal

__all__ = ["load", "split", "AudioRegion", "StreamTokenizer"]


DEFAULT_ANALYSIS_WINDOW = 0.05
DEFAULT_ENERGY_THRESHOLD = 50
_EPSILON = 1e-10


def load(input, skip=0, max_read=None, **kwargs):
    """Load audio data from a source and return it as an :class:`AudioRegion`.

    Parameters
    ----------
    input : None, str, bytes, AudioSource
        source to read audio data from. If `str`, it should be a path to a
        valid audio file. If `bytes`, it is used as raw audio data. If it is
        "-", raw data will be read from stdin. If None, read audio data from
        the microphone using PyAudio. If of type `bytes` or is a path to a
        raw audio file then `sampling_rate`, `sample_width` and `channels`
        parameters (or their alias) are required. If it's an
        :class:`AudioSource` object it's used directly to read data.
    skip : float, default: 0
        amount, in seconds, of audio data to skip from source. If read from
        a microphone, `skip` must be 0, otherwise a `ValueError` is raised.
    max_read : float, default: None
        amount, in seconds, of audio data to read from source. If read from
        microphone, `max_read` should not be None, otherwise a `ValueError` is
        raised.
    audio_format, fmt : str
        type of audio data (e.g., wav, ogg, flac, raw, etc.). This will only
        be used if `input` is a string path to an audio file. If not given,
        audio type will be guessed from file name extension or from file
        header.
    sampling_rate, sr : int
        sampling rate of audio data. Required if `input` is a raw audio file,
        a `bytes` object or None (i.e., read from microphone).
    sample_width, sw : int
        number of bytes used to encode one audio sample, typically 1, 2 or 4.
        Required for raw data, see `sampling_rate`.
    channels, ch : int
        number of channels of audio data. Required for raw data, see
        `sampling_rate`.
    large_file : bool, default: False
        If True, AND if `input` is a path to a *wav* of a *raw* audio file
        (and **only** these two formats) then audio file is not fully loaded to
        memory in order to create the region (but the portion of data needed to
        create the region is of course loaded to memory). Set to True if
        `max_read` is significantly smaller then the size of a large audio file
        that shouldn't be entirely loaded to memory.

    Returns
    -------
    region: AudioRegion

    Raises
    ------
    ValueError
        raised if `input` is None (i.e., read data from microphone) and `skip`
        != 0 or `input` is None `max_read` is None (meaning that when reading
        from the microphone, no data should be skipped, and maximum amount of
        data to read should be explicitly provided).
    """
    return AudioRegion.load(input, skip, max_read, **kwargs)


def split(
    input,
    min_dur=0.2,
    max_dur=5,
    max_silence=0.3,
    drop_trailing_silence=False,
    strict_min_dur=False,
    **kwargs
):
    """
    Split audio data and return a generator of AudioRegions

    Parameters
    ----------
    input : str, bytes, AudioSource, AudioReader, AudioRegion or None
        input audio data. If str, it should be a path to an existing audio file.
        "-" is interpreted as standard input. If bytes, input is considered as
        raw audio data. If None, read audio from microphone.
        Every object that is not an `AudioReader` will be transformed into an
        `AudioReader` before processing. If it is an `str` that refers to a raw
        audio file, `bytes` or None, audio parameters should be provided using
        kwargs (i.e., `samplig_rate`, `sample_width` and `channels` or their
        alias).
        If `input` is str then audio format will be guessed from file extension.
        `audio_format` (alias `fmt`) kwarg can also be given to specify audio
        format explicitly. If none of these options is available, rely on
        backend (currently only pydub is supported) to load data.
    min_dur : float, default: 0.2
        minimun duration in seconds of a detected audio event. By using large
        values for `min_dur`, very short audio events (e.g., very short 1-word
        utterances like 'yes' or 'no') can be mis detected. Using very short
        values might result in a high number of short, unuseful audio events.
    max_dur : float, default: 5
        maximum duration in seconds of a detected audio event. If an audio event
        lasts more than `max_dur` it will be truncated. If the continuation of a
        truncated audio event is shorter than `min_dur` then this continuation
        is accepted as a valid audio event if `strict_min_dur` is False.
        Otherwise it is rejected.
    max_silence : float, default: 0.3
        maximum duration of continuous silence within an audio event. There
        might be many silent gaps of this duration within one audio event. If
        the continuous silence happens at the end of the event than it's kept as
        part of the event if `drop_trailing_silence` is False (default).
    drop_trailing_silence : bool, default: False
        Whether to remove trailing silence from detected events. To avoid abrupt
        cuts in speech, trailing silence should be kept, therefore this
        parameter should be False.
    strict_min_dur : bool, default: False
        strict minimum duration. Do not accept an audio event if it is shorter
        than `min_dur` even if it is contiguous to the latest valid event. This
        happens if the the latest detected event had reached `max_dur`.

    Other Parameters
    ----------------
    analysis_window, aw : float, default: 0.05 (50 ms)
        duration of analysis window in seconds. A value between 0.01 (10 ms) and
        0.1 (100 ms) should be good for most use-cases.
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
    use_channel, uc : {None, "mix"} or int
        which channel to use for split if `input` has multiple audio channels.
        Regardless of which channel is used for splitting, returned audio events
        contain data from *all* channels, just as `input`.
        The following values are accepted:

        - None (alias "any"): accept audio activity from any channel, even if
          other channels are silent. This is the default behavior.

        - "mix" ("avg" or "average"): mix down all channels (i.e. compute
          average channel) and split the resulting channel.

        - int (0 <=, > `channels`): use one channel, specified by integer id,
          for split.

    large_file : bool, default: False
        If True, AND if `input` is a path to a *wav* of a *raw* audio file
        (and only these two formats) then audio data is lazily loaded to memory
        (i.e., one analysis window a time). Otherwise the whole file is loaded
        to memory before split. Set to True if the size of the file is larger
        than available memory.
    max_read, mr : float, default: None, read until end of stream
        maximum data to read from source in seconds.
    validator, val : callable, DataValidator
        custom data validator. If `None` (default), an `AudioEnergyValidor` is
        used with the given energy threshold. Can be a callable or an instance
        of `DataValidator` that implements `is_valid`. In either case, it'll be
        called with with a window of audio data as the first parameter.
    energy_threshold, eth : float, default: 50
        energy threshold for audio activity detection. Audio regions that have
        enough windows of with a signal energy equal to or above this threshold
        are considered valid audio events. Here we are referring to this amount
        as the energy of the signal but to be more accurate, it is the log
        energy of computed as: `20 * log10(sqrt(dot(x, x) / len(x)))` (see
        :class:`AudioEnergyValidator` and
        :func:`calculate_energy_single_channel`). If `validator` is given, this
        argument is ignored.

    Yields
    ------
    AudioRegion
        a generator of detected :class:`AudioRegion` s.
    """
    if min_dur <= 0:
        raise ValueError("'min_dur' ({}) must be > 0".format(min_dur))
    if max_dur <= 0:
        raise ValueError("'max_dur' ({}) must be > 0".format(max_dur))
    if max_silence < 0:
        raise ValueError("'max_silence' ({}) must be >= 0".format(max_silence))

    if isinstance(input, AudioReader):
        source = input
        analysis_window = source.block_dur
    else:
        analysis_window = kwargs.get(
            "analysis_window", kwargs.get("aw", DEFAULT_ANALYSIS_WINDOW)
        )
        if analysis_window <= 0:
            raise ValueError(
                "'analysis_window' ({}) must be > 0".format(analysis_window)
            )

        params = kwargs.copy()
        params["max_read"] = params.get("max_read", params.get("mr"))
        params["audio_format"] = params.get("audio_format", params.get("fmt"))
        if isinstance(input, AudioRegion):
            params["sampling_rate"] = input.sr
            params["sample_width"] = input.sw
            params["channels"] = input.ch
            input = bytes(input)
        try:
            source = AudioReader(input, block_dur=analysis_window, **params)
        except TooSamllBlockDuration as exc:
            err_msg = "Too small 'analysis_windows' ({0}) for sampling rate "
            err_msg += "({1}). Analysis windows should at least be 1/{1} to "
            err_msg += "cover one single data sample"
            raise ValueError(err_msg.format(exc.block_dur, exc.sampling_rate))

    validator = kwargs.get("validator", kwargs.get("val"))
    if validator is None:
        energy_threshold = kwargs.get(
            "energy_threshold", kwargs.get("eth", DEFAULT_ENERGY_THRESHOLD)
        )
        use_channel = kwargs.get("use_channel", kwargs.get("uc"))
        validator = AudioEnergyValidator(
            energy_threshold, source.sw, source.ch, use_channel=use_channel
        )
    mode = StreamTokenizer.DROP_TRAILING_SILENCE if drop_trailing_silence else 0
    if strict_min_dur:
        mode |= StreamTokenizer.STRICT_MIN_LENGTH
    min_length = _duration_to_nb_windows(min_dur, analysis_window, math.ceil)
    max_length = _duration_to_nb_windows(
        max_dur, analysis_window, math.floor, _EPSILON
    )
    max_continuous_silence = _duration_to_nb_windows(
        max_silence, analysis_window, math.floor, _EPSILON
    )

    err_msg = "({0} sec.) results in {1} analysis window(s) "
    err_msg += "({1} == {6}({0} / {2})) which is {5} the number "
    err_msg += "of analysis window(s) for 'max_dur' ({3} == floor({4} / {2}))"
    if min_length > max_length:
        err_msg = "'min_dur' " + err_msg
        raise ValueError(
            err_msg.format(
                min_dur,
                min_length,
                analysis_window,
                max_length,
                max_dur,
                "higher than",
                "ceil",
            )
        )

    if max_continuous_silence >= max_length:
        err_msg = "'max_silence' " + err_msg
        raise ValueError(
            err_msg.format(
                max_silence,
                max_continuous_silence,
                analysis_window,
                max_length,
                max_dur,
                "higher or equal to",
                "floor",
            )
        )

    tokenizer = StreamTokenizer(
        validator, min_length, max_length, max_continuous_silence, mode=mode
    )
    source.open()
    token_gen = tokenizer.tokenize(source, generator=True)
    region_gen = (
        _make_audio_region(
            token[0],
            token[1],
            source.block_dur,
            source.sr,
            source.sw,
            source.ch,
        )
        for token in token_gen
    )
    return region_gen


def _duration_to_nb_windows(
    duration, analysis_window, round_fn=round, epsilon=0
):
    """
    Converts a given duration into a positive integer of analysis windows.
    if `duration / analysis_window` is not an integer, the result will be
    rounded to the closest bigger integer. If `duration == 0`, returns `0`.
    If `duration < analysis_window`, returns 1.
    `duration` and `analysis_window` can be in seconds or milliseconds but
    must be in the same unit.

    Parameters
    ----------
    duration : float
        a given duration in seconds or ms.
    analysis_window: float
        size of analysis window, in the same unit as `duration`.
    round_fn : callable
        function called to round the result. Default: `round`.
    epsilon : float
        small value to add to the division result before rounding.
        E.g., `0.3 / 0.1 = 2.9999999999999996`, when called with
        `round_fn=math.floor` returns `2` instead of `3`. Adding a small value
        to `0.3 / 0.1` avoids this error.

    Returns
    -------
    nb_windows : int
        minimum number of `analysis_window`'s to cover `durartion`. That means
        that `analysis_window * nb_windows >= duration`.
    """
    if duration < 0 or analysis_window <= 0:
        err_msg = "'duration' ({}) must be >= 0 and 'analysis_window' ({}) > 0"
        raise ValueError(err_msg.format(duration, analysis_window))
    if duration == 0:
        return 0
    return int(round_fn(duration / analysis_window + epsilon))


def _make_audio_region(
    data_frames,
    start_frame,
    frame_duration,
    sampling_rate,
    sample_width,
    channels,
):
    """
    Helper function to create an `AudioRegion` from parameters returned by
    tokenization object. It takes care of setting up region `start` and `end`
    in metadata.

    Parameters
    ----------
    frame_duration: float
        duration of analysis window in seconds
    start_frame : int
        index of the fisrt analysis window
    samling_rate : int
        sampling rate of audio data
    sample_width : int
        number of bytes of one audio sample
    channels : int
        number of channels of audio data

    Returns
    -------
    audio_region : AudioRegion
        AudioRegion whose start time is calculeted as:
        `1000 * start_frame * frame_duration`
    """
    start = start_frame * frame_duration
    data = b"".join(data_frames)
    duration = len(data) / (sampling_rate * sample_width * channels)
    meta = {"start": start, "end": start + duration}
    return AudioRegion(data, sampling_rate, sample_width, channels, meta)


def _read_chunks_online(max_read, **kwargs):
    """
    Helper function to read audio data from an online blocking source
    (i.e., microphone). Used to build an `AudioRegion` and can intercept
    KeyboardInterrupt so that reading stops as soon as this exception is
    raised. Makes building `AudioRegion`s on [i]python sessions and jupyter
    notebooks more user friendly.

    Parameters
    ----------
    max_read : float
        maximum amount of data to read in seconds.
    kwargs :
        audio parameters (sampling_rate, sample_width and channels).

    See also
    --------
    `AudioRegion.build`
    """
    reader = AudioReader(None, block_dur=0.5, max_read=max_read, **kwargs)
    reader.open()
    data = []
    try:
        while True:
            frame = reader.read()
            if frame is None:
                break
            data.append(frame)
    except KeyboardInterrupt:
        # Stop data acquisition from microphone when pressing
        # Ctrl+C on a [i]python session or a notebook
        pass
    reader.close()
    return (
        b"".join(data),
        reader.sampling_rate,
        reader.sample_width,
        reader.channels,
    )


def _read_offline(input, skip=0, max_read=None, **kwargs):
    """
    Helper function to read audio data from an offline (i.e., file). Used to
    build `AudioRegion`s.

    Parameters
    ----------
    input : str, bytes
        path to audio file (if str), or a bytes object representing raw audio
        data.
    skip : float, default 0
        amount of data to skip from the begining of audio source.
    max_read : float, default: None
        maximum amount of audio data to read. Default: None, means read until
        end of stream.
    kwargs :
        audio parameters (sampling_rate, sample_width and channels).

    See also
    --------
    `AudioRegion.build`

    """
    audio_source = get_audio_source(input, **kwargs)
    audio_source.open()
    if skip is not None and skip > 0:
        skip_samples = round(skip * audio_source.sampling_rate)
        audio_source.read(skip_samples)
    if max_read is not None:
        if max_read < 0:
            max_read = None
        else:
            max_read = round(max_read * audio_source.sampling_rate)
    data = audio_source.read(max_read)
    audio_source.close()
    return (
        data,
        audio_source.sampling_rate,
        audio_source.sample_width,
        audio_source.channels,
    )


def _check_convert_index(index, types, err_msg):
    if not isinstance(index, slice) or index.step is not None:
        raise TypeError(err_msg)
    start = index.start if index.start is not None else 0
    stop = index.stop
    for index in (start, stop):
        if index is not None and not isinstance(index, types):
            raise TypeError(err_msg)
    return start, stop


class _SecondsView:
    """A class to create a view of `AudioRegion` that can be sliced using
    indices in seconds.
    """

    def __init__(self, region):
        self._region = region

    def __getitem__(self, index):
        err_msg = "Slicing AudioRegion by seconds requires indices of type "
        err_msg += "'int' or 'float' without a step (e.g. region.sec[7.5:10])"
        start_s, stop_s = _check_convert_index(index, (int, float), err_msg)
        sr = self._region.sampling_rate
        start_sample = int(start_s * sr)
        stop_sample = None if stop_s is None else round(stop_s * sr)
        return self._region[start_sample:stop_sample]

    @property
    def len(self):
        """
        Return region duration in seconds.
        """
        return self._region.duration


class _MillisView(_SecondsView):
    """A class to create a view of `AudioRegion` that can be sliced using
    indices in milliseconds.
    """

    def __getitem__(self, index):
        err_msg = (
            "Slicing AudioRegion by milliseconds requires indices of type "
        )
        err_msg += "'int' without a step (e.g. region.sec[500:1500])"
        start_ms, stop_ms = _check_convert_index(index, (int), err_msg)
        start_sec = start_ms / 1000
        stop_sec = None if stop_ms is None else stop_ms / 1000
        index = slice(start_sec, stop_sec)
        return super(_MillisView, self).__getitem__(index)

    def __len__(self):
        """
        Return region duration in milliseconds.
        """
        return round(self._region.duration * 1000)

    @property
    def len(self):
        """
        Return region duration in milliseconds.
        """
        return len(self)


class _AudioRegionMetadata(dict):
    """A class to store `AudioRegion`'s metadata."""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            err_msg = "AudioRegion metadata has no entry '{}'"
            raise AttributeError(err_msg.format(name))

    def __setattr__(self, name, value):
        self[name] = value

    def __str__(self):
        return "\n".join("{}: {}".format(k, v) for k, v in self.items())

    def __repr__(self):
        return str(self)


class AudioRegion(object):
    """
    AudioRegion encapsulates raw audio data and provides an interface to
    perform simple operations on it. Use `AudioRegion.load` to build an
    `AudioRegion` from different types of objects.

    Parameters
    ----------
    data : bytes
        raw audio data as a bytes object
    sampling_rate : int
        sampling rate of audio data
    sample_width : int
        number of bytes of one audio sample
    channels : int
        number of channels of audio data
    meta : dict, default: None
        any collection of <key:value> elements used to build metadata for
        this `AudioRegion`. Meta data can be accessed via `region.meta.key`
        if `key` is a valid python attribute name, or via `region.meta[key]`
        if not. Note that the :func:`split` function (or the
        :meth:`AudioRegion.split` method) returns `AudioRegions` with a ``start``
        and a ``stop`` meta values that indicate the location in seconds of the
        region in original audio data.

    See also
    --------
    AudioRegion.load

    """

    def __init__(self, data, sampling_rate, sample_width, channels, meta=None):
        check_audio_data(data, sample_width, channels)
        self._data = data
        self._sampling_rate = sampling_rate
        self._sample_width = sample_width
        self._channels = channels
        self._samples = None
        self.splitp = self.split_and_plot

        if meta is not None:
            self._meta = _AudioRegionMetadata(meta)
        else:
            self._meta = None

        self._seconds_view = _SecondsView(self)
        self.sec = self.seconds
        self.s = self.seconds

        self._millis_view = _MillisView(self)
        self.ms = self.millis

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, new_meta):
        """Meta data of audio region."""
        self._meta = _AudioRegionMetadata(new_meta)

    @classmethod
    def load(cls, input, skip=0, max_read=None, **kwargs):
        """
        Create an `AudioRegion` by loading data from `input`. See :func:`load`
        for parameters descripion.

        Returns
        -------
        region: AudioRegion

        Raises
        ------
        ValueError
            raised if `input` is None and `skip` != 0 or `max_read` is None.
        """
        if input is None:
            if skip > 0:
                raise ValueError(
                    "'skip' should be 0 when reading from microphone"
                )
            if max_read is None or max_read < 0:
                raise ValueError(
                    "'max_read' should not be None when reading from "
                    "microphone"
                )
            data, sampling_rate, sample_width, channels = _read_chunks_online(
                max_read, **kwargs
            )
        else:
            data, sampling_rate, sample_width, channels = _read_offline(
                input, skip=skip, max_read=max_read, **kwargs
            )

        return cls(data, sampling_rate, sample_width, channels)

    @property
    def seconds(self):
        """
        A view to slice audio region by seconds (using ``region.seconds[start:end]``).
        """
        return self._seconds_view

    @property
    def millis(self):
        """A view to slice audio region by milliseconds (using ``region.millis[start:end]``)."""
        return self._millis_view

    @property
    def duration(self):
        """
        Returns region duration in seconds.
        """
        return len(self._data) / (
            self.sampling_rate * self.sample_width * self.channels
        )

    @property
    def sampling_rate(self):
        """Samling rate of audio data."""
        return self._sampling_rate

    @property
    def sr(self):
        """Samling rate of audio data, alias for `sampling_rate`."""
        return self._sampling_rate

    @property
    def sample_width(self):
        """Number of bytes per sample, one channel considered."""
        return self._sample_width

    @property
    def sw(self):
        """Number of bytes per sample, alias for `sampling_rate`."""
        return self._sample_width

    @property
    def channels(self):
        """Number of channels of audio data."""
        return self._channels

    @property
    def ch(self):
        """Number of channels of audio data, alias for `channels`."""
        return self._channels

    def play(self, progress_bar=False, player=None, **progress_bar_kwargs):
        """
        Play audio region.

        Parameters
        ----------
        progress_bar : bool, default: False
            whether to use a progress bar while playing audio. Default: False.
            `progress_bar` requires `tqdm`, if not installed, no progress bar
            will be shown.
        player : AudioPalyer, default: None
            audio player to use. if None (default), use `player_for()`
            to get a new audio player.
        progress_bar_kwargs : kwargs
            keyword arguments to pass to `tqdm` progress_bar builder (e.g.,
            use `leave=False` to clean up the screen when play finishes).
        """
        if player is None:
            player = player_for(self)
        player.play(
            self._data, progress_bar=progress_bar, **progress_bar_kwargs
        )

    def save(self, file, audio_format=None, exists_ok=True, **audio_parameters):
        """
        Save audio region to file.

        Parameters
        ----------
        file : str
            path to output audio file. May contain `{duration}` placeholder
            as well as any place holder that this region's metadata might
            contain (e.g., regions returned by `split` contain metadata with
            `start` and `end` attributes that can be used to build output file
            name as `{meta.start}` and `{meta.end}`. See examples using
            placeholders with formatting.

        audio_format : str, default: None
            format used to save audio data. If None (default), format is guessed
            from file name's extension. If file name has no extension, audio
            data is saved as a raw (headerless) audio file.
        exists_ok : bool, default: True
            If True, overwrite `file` if a file with the same name exists.
            If False, raise an `IOError` if `file` exists.
        audio_parameters: dict
            any keyword arguments to be passed to audio saving backend.

        Returns
        -------
        file: str
            name of output file with replaced placehoders.
        Raises
            IOError if `file` exists and `exists_ok` is False.


        Examples
        --------
        >>> region = AudioRegion(b'\\0' * 2 * 24000,
        >>>                      sampling_rate=16000,
        >>>                      sample_width=2,
        >>>                      channels=1)
        >>> region.meta.start = 2.25
        >>> region.meta.end = 2.25 + region.duration
        >>> region.save('audio_{meta.start}-{meta.end}.wav')
        >>> audio_2.25-3.75.wav
        >>> region.save('region_{meta.start:.3f}_{duration:.3f}.wav')
        audio_2.250_1.500.wav
        """
        if isinstance(file, str):
            file = file.format(duration=self.duration, meta=self.meta)
            if not exists_ok and os.path.exists(file):
                raise FileExistsError("file '{file}' exists".format(file=file))
        to_file(
            self._data,
            file,
            audio_format,
            sr=self.sr,
            sw=self.sw,
            ch=self.ch,
            audio_parameters=audio_parameters,
        )
        return file

    def split(
        self,
        min_dur=0.2,
        max_dur=5,
        max_silence=0.3,
        drop_trailing_silence=False,
        strict_min_dur=False,
        **kwargs
    ):
        """Split audio region. See :func:`auditok.split()` for a comprehensive
        description of split parameters.
        See Also :meth:`AudioRegio.split_and_plot`.
        """
        if kwargs.get("max_read", kwargs.get("mr")) is not None:
            warn_msg = "'max_read' (or 'mr') should not be used with "
            warn_msg += "AudioRegion.split_and_plot(). You should rather "
            warn_msg += "slice audio region before calling this method"
            raise RuntimeWarning(warn_msg)
        return split(
            self,
            min_dur=min_dur,
            max_dur=max_dur,
            max_silence=max_silence,
            drop_trailing_silence=drop_trailing_silence,
            strict_min_dur=strict_min_dur,
            **kwargs
        )

    def plot(
        self,
        scale_signal=True,
        show=True,
        figsize=None,
        save_as=None,
        dpi=120,
        theme="auditok",
    ):
        """Plot audio region, one sub-plot for each channel.

        Parameters
        ----------
        scale_signal : bool, default: True
            if true, scale signal by subtracting its mean and dividing by its
            standard deviation before plotting.
        show : bool
            whether to show plotted signal right after the call.
        figsize : tuple, default: None
            width and height of the figure to pass to `matplotlib`.
        save_as : str, default None.
            if provided, also save plot to file.
        dpi : int, default: 120
            plot dpi to pass to `matplotlib`.
        theme : str or dict, default: "auditok"
            plot theme to use. Currently only "auditok" theme is implemented. To
            provide you own them see :attr:`auditok.plotting.AUDITOK_PLOT_THEME`.
        """
        try:
            from auditok.plotting import plot

            plot(
                self,
                scale_signal=scale_signal,
                show=show,
                figsize=figsize,
                save_as=save_as,
                dpi=dpi,
                theme=theme,
            )
        except ImportError:
            raise RuntimeWarning("Plotting requires matplotlib")

    def split_and_plot(
        self,
        min_dur=0.2,
        max_dur=5,
        max_silence=0.3,
        drop_trailing_silence=False,
        strict_min_dur=False,
        scale_signal=True,
        show=True,
        figsize=None,
        save_as=None,
        dpi=120,
        theme="auditok",
        **kwargs
    ):
        """Split region and plot signal and detections. Alias: :meth:`splitp`.
        See :func:`auditok.split()` for a comprehensive description of split
        parameters. Also see :meth:`plot` for plot parameters.
        """
        try:
            from auditok.plotting import plot

            regions = self.split(
                min_dur=min_dur,
                max_dur=max_dur,
                max_silence=max_silence,
                drop_trailing_silence=drop_trailing_silence,
                strict_min_dur=strict_min_dur,
                **kwargs
            )
            regions = list(regions)
            detections = ((reg.meta.start, reg.meta.end) for reg in regions)
            eth = kwargs.get(
                "energy_threshold", kwargs.get("eth", DEFAULT_ENERGY_THRESHOLD)
            )
            plot(
                self,
                scale_signal=scale_signal,
                detections=detections,
                energy_threshold=eth,
                show=show,
                figsize=figsize,
                save_as=save_as,
                dpi=dpi,
                theme=theme,
            )
            return regions
        except ImportError:
            raise RuntimeWarning("Plotting requires matplotlib")

    def __array__(self):
        return self.samples

    @property
    def samples(self):
        """Audio region as arrays of samples, one array per channel."""
        if self._samples is None:
            self._samples = signal.to_array(
                self._data, self.sample_width, self.channels
            )
        return self._samples

    def __len__(self):
        """
        Return region length in number of samples.
        """
        return len(self._data) // (self.sample_width * self.channels)

    @property
    def len(self):
        """
        Return region length in number of samples.
        """
        return len(self)

    def __bytes__(self):
        return self._data

    def __str__(self):
        return (
            "AudioRegion(duration={:.3f}, "
            "sampling_rate={}, sample_width={}, channels={})".format(
                self.duration, self.sr, self.sw, self.ch
            )
        )

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        """
        Concatenates this region and `other` and return a new region.
        Both regions must have the same sampling rate, sample width
        and number of channels. If not, raises a `ValueError`.
        """
        if not isinstance(other, AudioRegion):
            raise TypeError(
                "Can only concatenate AudioRegion, "
                'not "{}"'.format(type(other))
            )
        if other.sr != self.sr:
            raise ValueError(
                "Can only concatenate AudioRegions of the same "
                "sampling rate ({} != {})".format(self.sr, other.sr)
            )
        if other.sw != self.sw:
            raise ValueError(
                "Can only concatenate AudioRegions of the same "
                "sample width ({} != {})".format(self.sw, other.sw)
            )
        if other.ch != self.ch:
            raise ValueError(
                "Can only concatenate AudioRegions of the same "
                "number of channels ({} != {})".format(self.ch, other.ch)
            )
        data = self._data + other._data
        return AudioRegion(data, self.sr, self.sw, self.ch)

    def __radd__(self, other):
        """
        Concatenates `other` and this region. `other` should be an
        `AudioRegion` with the same audio parameters as this region
        but can exceptionally be `0` to make it possible to concatenate
        many regions with `sum`.
        """
        if other == 0:
            return self
        return other.add(self)

    def __mul__(self, n):
        if not isinstance(n, int):
            err_msg = "Can't multiply AudioRegion by a non-int of type '{}'"
            raise TypeError(err_msg.format(type(n)))
        data = self._data * n
        return AudioRegion(data, self.sr, self.sw, self.ch)

    def __rmul__(self, n):
        return self * n

    def __truediv__(self, n):
        if not isinstance(n, int) or n <= 0:
            raise TypeError("AudioRegion can only be divided by a positive int")
        samples_per_sub_region, rest = divmod(len(self), n)
        onset = 0
        sub_regions = []
        while onset < len(self):
            offset = 0
            if rest > 0:
                offset = 1
                rest -= 1
            offset += onset + samples_per_sub_region
            sub_regions.append(self[onset:offset])
            onset = offset
        return sub_regions

    def __eq__(self, other):
        if other is self:
            return True
        if not isinstance(other, AudioRegion):
            return False
        return (
            (self._data == other._data)
            and (self.sr == other.sr)
            and (self.sw == other.sw)
            and (self.ch == other.ch)
        )

    def __getitem__(self, index):
        err_msg = "Slicing AudioRegion by samples requires indices of type "
        err_msg += "'int' without a step (e.g. region.sec[1600:3200])"
        start_sample, stop_sample = _check_convert_index(index, (int), err_msg)

        bytes_per_sample = self.sample_width * self.channels
        len_samples = len(self._data) // bytes_per_sample

        if start_sample < 0:
            start_sample = max(start_sample + len_samples, 0)
        onset = start_sample * bytes_per_sample

        if stop_sample is not None:
            if stop_sample < 0:
                stop_sample = max(stop_sample + len_samples, 0)
            offset = index.stop * bytes_per_sample
        else:
            offset = None

        data = self._data[onset:offset]
        return AudioRegion(data, self.sr, self.sw, self.ch)


class StreamTokenizer:
    """
    Class for stream tokenizers. It implements a 4-state automaton scheme
    to extract sub-sequences of interest on the fly.

    Parameters
    ----------
    validator : callable, DataValidator (must implement `is_valid`)
        called with each data frame read from source. Should take one positional
        argument and return True or False for valid and invalid frames
        respectively.

    min_length : int
        Minimum number of frames of a valid token. This includes all
        tolerated non valid frames within the token.

    max_length : int
        Maximum number of frames of a valid token. This includes all
        tolerated non valid frames within the token.

    max_continuous_silence : int
        Maximum number of consecutive non-valid frames within a token.
        Note that, within a valid token, there may be many tolerated
        *silent* regions that contain each a number of non valid frames up
        to `max_continuous_silence`

    init_min : int
        Minimum number of consecutive valid frames that must be
        **initially** gathered before any sequence of non valid frames can
        be tolerated. This option is not always needed, it can be used to
        drop non-valid tokens as early as possible. **Default = 0** means
        that the option is by default ineffective.

    init_max_silence : int
        Maximum number of tolerated consecutive non-valid frames if the
        number already gathered valid frames has not yet reached
        'init_min'.This argument is normally used if `init_min` is used.
        **Default = 0**, by default this argument is not taken into
        consideration.

    mode : int
        mode can be one of the following:

            -1 `StreamTokenizer.NORMAL` : do not drop trailing silence, and
            accept a token shorter than `min_length` if it is the continuation
            of the latest delivered token.

            -2 `StreamTokenizer.STRICT_MIN_LENGTH`: if token `i` is delivered
            because `max_length` is reached, and token `i+1` is immediately
            adjacent to token `i` (i.e. token `i` ends at frame `k` and token
            `i+1` starts at frame `k+1`) then accept token `i+1` only of it has
            a size of at least `min_length`. The default behavior is to accept
            token `i+1` event if it is shorter than `min_length` (provided that
            the above conditions are fulfilled of course).

            -3 `StreamTokenizer.DROP_TRAILING_SILENCE`: drop all tailing
            non-valid frames from a token to be delivered if and only if it
            is not **truncated**. This can be a bit tricky. A token is actually
            delivered if:

                - `max_continuous_silence` is reached.

                - Its length reaches `max_length`. This is referred to as a
                  **truncated** token.

            In the current implementation, a `StreamTokenizer`'s decision is only
            based on already seen data and on incoming data. Thus, if a token is
            truncated at a non-valid but tolerated frame (`max_length` is reached
            but `max_continuous_silence` not yet) any tailing silence will be kept
            because it can potentially be part of valid token (if `max_length` was
            bigger). But if `max_continuous_silence` is reached before
            `max_length`, the delivered token will not be considered as truncated
            but a result of *normal* end of detection (i.e. no more valid data).
            In that case the trailing silence can be removed if you use the
            `StreamTokenizer.DROP_TRAILING_SILENCE` mode.

            -4 `(StreamTokenizer.STRICT_MIN_LENGTH | StreamTokenizer.DROP_TRAILING_SILENCE)`:
            use both options. That means: first remove tailing silence, then
            check if the token still has a length of at least `min_length`.




    Examples
    --------

    In the following code, without `STRICT_MIN_LENGTH`, the 'BB' token is
    accepted although it is shorter than `min_length` (3), because it
    immediately follows the latest delivered token:

    >>> from auditok.core import StreamTokenizer
    >>> from StringDataSource, DataValidator

    >>> class UpperCaseChecker(DataValidator):
    >>>     def is_valid(self, frame):
                return frame.isupper()
    >>> dsource = StringDataSource("aaaAAAABBbbb")
    >>> tokenizer = StreamTokenizer(validator=UpperCaseChecker(),
                                    min_length=3,
                                    max_length=4,
                                    max_continuous_silence=0)
    >>> tokenizer.tokenize(dsource)
    [(['A', 'A', 'A', 'A'], 3, 6), (['B', 'B'], 7, 8)]


    The following tokenizer will however reject the 'BB' token:

    >>> dsource = StringDataSource("aaaAAAABBbbb")
    >>> tokenizer = StreamTokenizer(validator=UpperCaseChecker(),
                                    min_length=3, max_length=4,
                                    max_continuous_silence=0,
                                    mode=StreamTokenizer.STRICT_MIN_LENGTH)
    >>> tokenizer.tokenize(dsource)
    [(['A', 'A', 'A', 'A'], 3, 6)]



    >>> tokenizer = StreamTokenizer(
    >>>                validator=UpperCaseChecker(),
    >>>                min_length=3,
    >>>                max_length=6,
    >>>                max_continuous_silence=3,
    >>>                mode=StreamTokenizer.DROP_TRAILING_SILENCE
    >>>                )
    >>> dsource = StringDataSource("aaaAAAaaaBBbbbb")
    >>> tokenizer.tokenize(dsource)
    [(['A', 'A', 'A', 'a', 'a', 'a'], 3, 8), (['B', 'B'], 9, 10)]

    The first token is delivered with its tailing silence because it is
    truncated while the second one has its tailing frames removed.

    Without `StreamTokenizer.DROP_TRAILING_SILENCE` the output would be:

    .. code:: python

        [
            (['A', 'A', 'A', 'a', 'a', 'a'], 3, 8),
            (['B', 'B', 'b', 'b', 'b'], 9, 13)
        ]

    """

    SILENCE = 0
    POSSIBLE_SILENCE = 1
    POSSIBLE_NOISE = 2
    NOISE = 3
    NORMAL = 0
    STRICT_MIN_LENGTH = 2
    DROP_TRAILING_SILENCE = 4

    def __init__(
        self,
        validator,
        min_length,
        max_length,
        max_continuous_silence,
        init_min=0,
        init_max_silence=0,
        mode=0,
    ):
        if callable(validator):
            self._is_valid = validator
        elif isinstance(validator, DataValidator):
            self._is_valid = validator.is_valid
        else:
            raise TypeError(
                "'validator' must be a callable or an instance of "
                "DataValidator"
            )

        if max_length <= 0:
            raise ValueError(
                "'max_length' must be > 0 (value={0})".format(max_length)
            )

        if min_length <= 0 or min_length > max_length:
            err_msg = "'min_length' must be > 0 and <= 'max_length' (value={0})"
            raise ValueError(err_msg.format(min_length))

        if max_continuous_silence >= max_length:
            err_msg = "'max_continuous_silence' must be < 'max_length' "
            err_msg += "(value={0})"
            raise ValueError(err_msg.format(max_continuous_silence))

        if init_min >= max_length:
            raise ValueError(
                "'init_min' must be < 'max_length' (value={0})".format(
                    max_continuous_silence
                )
            )

        self.validator = validator
        self.min_length = min_length
        self.max_length = max_length
        self.max_continuous_silence = max_continuous_silence
        self.init_min = init_min
        self.init_max_silent = init_max_silence
        self._set_mode(mode)
        self._deliver = None
        self._tokens = None
        self._state = None
        self._data = None
        self._contiguous_token = False
        self._init_count = 0
        self._silence_length = 0
        self._start_frame = 0
        self._current_frame = 0

    def _set_mode(self, mode):
        strict_min_and_drop_trailing = StreamTokenizer.STRICT_MIN_LENGTH
        strict_min_and_drop_trailing |= StreamTokenizer.DROP_TRAILING_SILENCE
        if mode not in [
            StreamTokenizer.NORMAL,
            StreamTokenizer.STRICT_MIN_LENGTH,
            StreamTokenizer.DROP_TRAILING_SILENCE,
            strict_min_and_drop_trailing,
        ]:
            raise ValueError("Wrong value for mode")
        self._mode = mode
        self._strict_min_length = (mode & self.STRICT_MIN_LENGTH) != 0
        self._drop_trailing_silence = (mode & self.DROP_TRAILING_SILENCE) != 0

    def _reinitialize(self):
        self._contiguous_token = False
        self._data = []
        self._tokens = []
        self._state = self.SILENCE
        self._current_frame = -1
        self._deliver = self._append_token

    def tokenize(self, data_source, callback=None, generator=False):
        """
        Read data from `data_source`, one frame a time, and process the read
        frames in order to detect sequences of frames that make up valid
        tokens.

        :Parameters:
           `data_source` : instance of the :class:`DataSource` class that
               implements a `read` method. 'read' should return a slice of
               signal, i.e. frame (of whatever type as long as it can be
               processed by validator) and None if there is no more signal.

           `callback` : an optional 3-argument function.
               If a `callback` function is given, it will be called each time
               a valid token is found.


        :Returns:
           A list of tokens if `callback` is None. Each token is tuple with the
           following elements:

            .. code python

                (data, start, end)

           where `data` is a list of read frames, `start`: index of the first
           frame in the original data and `end` : index of the last frame.
        """
        token_gen = self._iter_tokens(data_source)
        if callback:
            for token in token_gen:
                callback(*token)
            return
        if generator:
            return token_gen
        return list(token_gen)

    def _iter_tokens(self, data_source):
        self._reinitialize()
        while True:
            frame = data_source.read()
            self._current_frame += 1
            if frame is None:
                token = self._post_process()
                if token is not None:
                    yield token
                break
            token = self._process(frame)
            if token is not None:
                yield token

    def _process(self, frame):  # noqa: C901

        frame_is_valid = self._is_valid(frame)

        if self._state == self.SILENCE:

            if frame_is_valid:
                # seems we got a valid frame after a silence
                self._init_count = 1
                self._silence_length = 0
                self._start_frame = self._current_frame
                self._data.append(frame)

                if self._init_count >= self.init_min:
                    self._state = self.NOISE
                    if len(self._data) >= self.max_length:
                        return self._process_end_of_detection(True)
                else:
                    self._state = self.POSSIBLE_NOISE

        elif self._state == self.POSSIBLE_NOISE:

            if frame_is_valid:
                self._silence_length = 0
                self._init_count += 1
                self._data.append(frame)
                if self._init_count >= self.init_min:
                    self._state = self.NOISE
                    if len(self._data) >= self.max_length:
                        return self._process_end_of_detection(True)

            else:
                self._silence_length += 1
                if (
                    self._silence_length > self.init_max_silent
                    or len(self._data) + 1 >= self.max_length
                ):
                    # either init_max_silent or max_length is reached
                    # before _init_count, back to silence
                    self._data = []
                    self._state = self.SILENCE
                else:
                    self._data.append(frame)

        elif self._state == self.NOISE:

            if frame_is_valid:
                self._data.append(frame)
                if len(self._data) >= self.max_length:
                    return self._process_end_of_detection(True)

            elif self.max_continuous_silence <= 0:
                # max token reached at this frame will _deliver if
                # _contiguous_token and not _strict_min_length
                self._state = self.SILENCE
                return self._process_end_of_detection()
            else:
                # this is the first silent frame following a valid one
                # and it is tolerated
                self._silence_length = 1
                self._data.append(frame)
                self._state = self.POSSIBLE_SILENCE
                if len(self._data) == self.max_length:
                    return self._process_end_of_detection(True)
                    # don't reset _silence_length because we still
                    # need to know the total number of silent frames

        elif self._state == self.POSSIBLE_SILENCE:

            if frame_is_valid:
                self._data.append(frame)
                self._silence_length = 0
                self._state = self.NOISE
                if len(self._data) >= self.max_length:
                    return self._process_end_of_detection(True)

            else:
                if self._silence_length >= self.max_continuous_silence:
                    self._state = self.SILENCE
                    if self._silence_length < len(self._data):
                        # _deliver only gathered frames aren't all silent
                        return self._process_end_of_detection()
                    self._data = []
                    self._silence_length = 0
                else:
                    self._data.append(frame)
                    self._silence_length += 1
                    if len(self._data) >= self.max_length:
                        return self._process_end_of_detection(True)
                        # don't reset _silence_length because we still
                        # need to know the total number of silent frames

    def _post_process(self):
        if self._state == self.NOISE or self._state == self.POSSIBLE_SILENCE:
            if len(self._data) > 0 and len(self._data) > self._silence_length:
                return self._process_end_of_detection()

    def _process_end_of_detection(self, truncated=False):

        if (
            not truncated
            and self._drop_trailing_silence
            and self._silence_length > 0
        ):
            # happens if max_continuous_silence is reached
            # or max_length is reached at a silent frame
            self._data = self._data[0 : -self._silence_length]

        if (len(self._data) >= self.min_length) or (
            len(self._data) > 0
            and not self._strict_min_length
            and self._contiguous_token
        ):

            start_frame = self._start_frame
            end_frame = self._start_frame + len(self._data) - 1
            data = self._data
            self._data = []
            token = (data, start_frame, end_frame)

            if truncated:
                # next token (if any) will start at _current_frame + 1
                self._start_frame = self._current_frame + 1
                # remember that it is contiguous with the just delivered one
                self._contiguous_token = True
            else:
                self._contiguous_token = False
            return token
        else:
            self._contiguous_token = False

        self._data = []

    def _append_token(self, data, start, end):
        self._tokens.append((data, start, end))
