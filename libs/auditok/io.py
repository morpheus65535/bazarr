"""
Module for low-level audio input-output operations.

Class summary
=============

.. autosummary::

        AudioSource
        Rewindable
        BufferAudioSource
        WaveAudioSource
        PyAudioSource
        StdinAudioSource
        PyAudioPlayer
        

Function summary
================

.. autosummary::

        from_file
        player_for
"""

from abc import ABCMeta, abstractmethod
import wave
import sys

__all__ = ["AudioSource", "Rewindable", "BufferAudioSource", "WaveAudioSource",
           "PyAudioSource", "StdinAudioSource", "PyAudioPlayer", "from_file", "player_for"]

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_SAMPLE_WIDTH = 2
DEFAULT_NB_CHANNELS = 1


class AudioSource():
    """ 
    Base class for audio source objects.

    Subclasses should implement methods to open/close and audio stream 
    and read the desired amount of audio samples.

    :Parameters:

        `sampling_rate` : int
            Number of samples per second of audio stream. Default = 16000.

        `sample_width` : int
            Size in bytes of one audio sample. Possible values : 1, 2, 4.
            Default = 2.

        `channels` : int
            Number of channels of audio stream. The current version supports
            only mono audio streams (i.e. one channel).
    """

    __metaclass__ = ABCMeta

    def __init__(self, sampling_rate=DEFAULT_SAMPLE_RATE,
                 sample_width=DEFAULT_SAMPLE_WIDTH,
                 channels=DEFAULT_NB_CHANNELS):

        if not sample_width in (1, 2, 4):
            raise ValueError("Sample width must be one of: 1, 2 or 4 (bytes)")

        if channels != 1:
            raise ValueError("Only mono audio is currently handled")

        self._sampling_rate = sampling_rate
        self._sample_width = sample_width
        self._channels = channels

    @abstractmethod
    def is_open(self):
        """ Return True if audio source is open, False otherwise """

    @abstractmethod
    def open(self):
        """ Open audio source """

    @abstractmethod
    def close(self):
        """ Close audio source """

    @abstractmethod
    def read(self, size):
        """
        Read and return `size` audio samples at most.

        :Parameters:

            `size` : int
                the number of samples to read.

        :Returns:

            Audio data as a string of length 'N' * 'sample_width' * 'channels', where 'N' is:

            - `size` if `size` < 'left_samples'

            - 'left_samples' if `size` > 'left_samples' 
        """

    def get_sampling_rate(self):
        """ Return the number of samples per second of audio stream """
        return self.sampling_rate

    @property
    def sampling_rate(self):
        """ Number of samples per second of audio stream """
        return self._sampling_rate

    @property
    def sr(self):
        """ Number of samples per second of audio stream """
        return self._sampling_rate

    def get_sample_width(self):
        """ Return the number of bytes used to represent one audio sample """
        return self.sample_width

    @property
    def sample_width(self):
        """ Number of bytes used to represent one audio sample """
        return self._sample_width

    @property
    def sw(self):
        """ Number of bytes used to represent one audio sample """
        return self._sample_width

    def get_channels(self):
        """ Return the number of channels of this audio source """
        return self.channels

    @property
    def channels(self):
        """ Number of channels of this audio source """
        return self._channels

    @property
    def ch(self):
        """ Return the number of channels of this audio source """
        return self.channels


class Rewindable():
    """
    Base class for rewindable audio streams.
    Subclasses should implement methods to return to the beginning of an
    audio stream as well as method to move to an absolute audio position
    expressed in time or in number of samples. 
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def rewind(self):
        """ Go back to the beginning of audio stream """
        pass

    @abstractmethod
    def get_position(self):
        """ Return the total number of already read samples """

    @abstractmethod
    def get_time_position(self):
        """ Return the total duration in seconds of already read data """

    @abstractmethod
    def set_position(self, position):
        """ Move to an absolute position 

        :Parameters:

            `position` : int
                number of samples to skip from the start of the stream
        """

    @abstractmethod
    def set_time_position(self, time_position):
        """ Move to an absolute position expressed in seconds

        :Parameters:

            `time_position` : float
                seconds to skip from the start of the stream
        """
        pass


class BufferAudioSource(AudioSource, Rewindable):
    """
    An :class:`AudioSource` that encapsulates and reads data from a memory buffer.
    It implements methods from :class:`Rewindable` and is therefore a navigable :class:`AudioSource`.
    """

    def __init__(self, data_buffer,
                 sampling_rate=DEFAULT_SAMPLE_RATE,
                 sample_width=DEFAULT_SAMPLE_WIDTH,
                 channels=DEFAULT_NB_CHANNELS):

        if len(data_buffer) % (sample_width * channels) != 0:
            raise ValueError("length of data_buffer must be a multiple of (sample_width * channels)")

        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._buffer = data_buffer
        self._index = 0
        self._left = 0 if self._buffer is None else len(self._buffer)
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
            raise IOError("Stream is not open")

        if self._left > 0:

            to_read = size * self.sample_width * self.channels
            if to_read > self._left:
                to_read = self._left

            data = self._buffer[self._index: self._index + to_read]
            self._index += to_read
            self._left -= to_read

            return data

        return None

    def get_data_buffer(self):
        """ Return all audio data as one string buffer. """
        return self._buffer

    def set_data(self, data_buffer):
        """ Set new data for this audio stream. 

        :Parameters:

            `data_buffer` : str, basestring, Bytes
                a string buffer with a length multiple of (sample_width * channels)
        """
        if len(data_buffer) % (self.sample_width * self.channels) != 0:
            raise ValueError("length of data_buffer must be a multiple of (sample_width * channels)")
        self._buffer = data_buffer
        self._index = 0
        self._left = 0 if self._buffer is None else len(self._buffer)

    def append_data(self, data_buffer):
        """ Append data to this audio stream

        :Parameters:

            `data_buffer` : str, basestring, Bytes
                a buffer with a length multiple of (sample_width * channels)
        """

        if len(data_buffer) % (self.sample_width * self.channels) != 0:
            raise ValueError("length of data_buffer must be a multiple of (sample_width * channels)")

        self._buffer += data_buffer
        self._left += len(data_buffer)

    def rewind(self):
        self.set_position(0)

    def get_position(self):
        return self._index / self.sample_width

    def get_time_position(self):
        return float(self._index) / (self.sample_width * self.sampling_rate)

    def set_position(self, position):
        if position < 0:
            raise ValueError("position must be >= 0")

        if self._buffer is None:
            self._index = 0
            self._left = 0
            return

        position *= self.sample_width
        self._index = position if position < len(self._buffer) else len(self._buffer)
        self._left = len(self._buffer) - self._index

    def set_time_position(self, time_position):  # time in seconds
        position = int(self.sampling_rate * time_position)
        self.set_position(position)


class WaveAudioSource(AudioSource):
    """
    A class for an `AudioSource` that reads data from a wave file.

    :Parameters:

        `filename` :
            path to a valid wave file
    """

    def __init__(self, filename):

        self._filename = filename
        self._audio_stream = None

        stream = wave.open(self._filename)
        AudioSource.__init__(self, stream.getframerate(),
                             stream.getsampwidth(),
                             stream.getnchannels())
        stream.close()

    def is_open(self):
        return self._audio_stream is not None

    def open(self):
        if(self._audio_stream is None):
            self._audio_stream = wave.open(self._filename)

    def close(self):
        if self._audio_stream is not None:
            self._audio_stream.close()
            self._audio_stream = None

    def read(self, size):
        if self._audio_stream is None:
            raise IOError("Stream is not open")
        else:
            data = self._audio_stream.readframes(size)
            if data is None or len(data) < 1:
                return None
            return data


class PyAudioSource(AudioSource):
    """
    A class for an `AudioSource` that reads data the built-in microphone using PyAudio. 
    """

    def __init__(self, sampling_rate=DEFAULT_SAMPLE_RATE,
                 sample_width=DEFAULT_SAMPLE_WIDTH,
                 channels=DEFAULT_NB_CHANNELS,
                 frames_per_buffer=1024,
                 input_device_index=None):

        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._chunk_size = frames_per_buffer
        self.input_device_index = input_device_index

        import pyaudio
        self._pyaudio_object = pyaudio.PyAudio()
        self._pyaudio_format = self._pyaudio_object.get_format_from_width(self.sample_width)
        self._audio_stream = None

    def is_open(self):
        return self._audio_stream is not None

    def open(self):
        self._audio_stream = self._pyaudio_object.open(format=self._pyaudio_format,
                                                       channels=self.channels,
                                                       rate=self.sampling_rate,
                                                       input=True,
                                                       output=False,
                                                       input_device_index=self.input_device_index,
                                                       frames_per_buffer=self._chunk_size)

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


class StdinAudioSource(AudioSource):
    """
    A class for an :class:`AudioSource` that reads data from standard input.
    """

    def __init__(self, sampling_rate=DEFAULT_SAMPLE_RATE,
                 sample_width=DEFAULT_SAMPLE_WIDTH,
                 channels=DEFAULT_NB_CHANNELS):

        AudioSource.__init__(self, sampling_rate, sample_width, channels)
        self._is_open = False

    def is_open(self):
        return self._is_open

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def read(self, size):
        if not self._is_open:
            raise IOError("Stream is not open")

        to_read = size * self.sample_width * self.channels
        if sys.version_info >= (3, 0):
            data = sys.stdin.buffer.read(to_read)
        else:
            data = sys.stdin.read(to_read)

        if data is None or len(data) < 1:
            return None

        return data


class PyAudioPlayer():
    """
    A class for audio playback using Pyaudio
    """

    def __init__(self, sampling_rate=DEFAULT_SAMPLE_RATE,
                 sample_width=DEFAULT_SAMPLE_WIDTH,
                 channels=DEFAULT_NB_CHANNELS):
        if not sample_width in (1, 2, 4):
            raise ValueError("Sample width must be one of: 1, 2 or 4 (bytes)")

        self.sampling_rate = sampling_rate
        self.sample_width = sample_width
        self.channels = channels

        import pyaudio
        self._p = pyaudio.PyAudio()
        self.stream = self._p.open(format=self._p.get_format_from_width(self.sample_width),
                                   channels=self.channels, rate=self.sampling_rate,
                                   input=False, output=True)

    def play(self, data):
        if self.stream.is_stopped():
            self.stream.start_stream()

        for chunk in self._chunk_data(data):
            self.stream.write(chunk)

        self.stream.stop_stream()

    def stop(self):
        if not self.stream.is_stopped():
            self.stream.stop_stream()
        self.stream.close()
        self._p.terminate()

    def _chunk_data(self, data):
        # make audio chunks of 100 ms to allow interruption (like ctrl+c)
        chunk_size = int((self.sampling_rate * self.sample_width * self.channels) / 10)
        start = 0
        while start < len(data):
            yield data[start: start + chunk_size]
            start += chunk_size


def from_file(filename):
    """
    Create an `AudioSource` object using the audio file specified by `filename`.
    The appropriate :class:`AudioSource` class is guessed from file's extension.

    :Parameters:

        `filename` :
            path to an audio file.

    :Returns:

        an `AudioSource` object that reads data from the given file.
    """

    if filename.lower().endswith(".wav"):
        return WaveAudioSource(filename)

    raise Exception("Can not create an AudioSource object from '%s'" % (filename))


def player_for(audio_source):
    """
    Return a :class:`PyAudioPlayer` that can play data from `audio_source`.

    :Parameters:

        `audio_source` : 
            an `AudioSource` object.

    :Returns:

        `PyAudioPlayer` that has the same sampling rate, sample width and number of channels
        as `audio_source`.
    """

    return PyAudioPlayer(audio_source.get_sampling_rate(),
                         audio_source.get_sample_width(),
                         audio_source.get_channels())
