"""
Class summary
=============

.. autosummary::

        DataSource
        StringDataSource
        ADSFactory
        ADSFactory.AudioDataSource
        ADSFactory.ADSDecorator
        ADSFactory.OverlapADS
        ADSFactory.LimiterADS
        ADSFactory.RecorderADS
        DataValidator
        AudioEnergyValidator

"""


from abc import ABCMeta, abstractmethod
import math
from array import array
from .io import Rewindable, from_file, BufferAudioSource, PyAudioSource
from .exceptions import DuplicateArgument
import sys


try:
    import numpy
    _WITH_NUMPY = True
except ImportError as e:
    _WITH_NUMPY = False
    
try:
    from builtins import str
    basestring = str
except ImportError as e:
    if sys.version_info >= (3, 0):
        basestring = str
    
    

__all__ = ["DataSource", "DataValidator", "StringDataSource", "ADSFactory", "AudioEnergyValidator"]
    

class DataSource():
    """
    Base class for objects passed to :func:`auditok.core.StreamTokenizer.tokenize`.
    Subclasses should implement a :func:`DataSource.read` method.
    """
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def read(self):
        """
        Read a piece of data read from this source.
        If no more data is available, return None.
        """
    
    
class DataValidator():
    """
    Base class for a validator object used by :class:`.core.StreamTokenizer` to check
    if read data is valid.
    Subclasses should implement :func:`is_valid` method.
    """
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def is_valid(self, data):
        """
        Check whether `data` is valid
        """

class StringDataSource(DataSource):
    """
    A class that represent a :class:`DataSource` as a string buffer.
    Each call to :func:`DataSource.read` returns on character and moves one step forward.
    If the end of the buffer is reached, :func:`read` returns None.
   
    :Parameters:
        
        `data` : 
            a basestring object.
     
    """
     
    def __init__(self, data):

        self._data = None
        self._current = 0
        self.set_data(data)
        
    
    def read(self):
        """
        Read one character from buffer.
        
        :Returns:
        
            Current character or None if end of buffer is reached
        """
        
        if self._current >= len(self._data):
            return None
        self._current += 1
        return self._data[self._current - 1]
    
    def set_data(self, data):
        """
        Set a new data buffer.
        
        :Parameters:
        
            `data` : a basestring object 
                New data buffer.
        """
        
        if not isinstance(data, basestring):
            raise ValueError("data must an instance of basestring")
        self._data = data
        self._current = 0
        


class ADSFactory:
    """
    Factory class that makes it easy to create an :class:`ADSFactory.AudioDataSource` object that implements
    :class:`DataSource` and can therefore be passed to :func:`auditok.core.StreamTokenizer.tokenize`.
    
    Whether you read audio data from a file, the microphone or a memory buffer, this factory
    instantiates and returns the right :class:`ADSFactory.AudioDataSource` object.
    
    There are many other features you want your :class:`ADSFactory.AudioDataSource` object to have, such as: 
    memorize all read audio data so that you can rewind and reuse it (especially useful when 
    reading data from the microphone), read a fixed amount of data (also useful when reading 
    from the microphone), read overlapping audio frames (often needed when dosing a spectral
    analysis of data).
    
    :func:`ADSFactory.ads` automatically creates and return object with the desired behavior according
    to the supplied keyword arguments. 
     
    """
    
    @staticmethod
    def _check_normalize_args(kwargs):
        
        for k in kwargs:
            if not k in ["block_dur", "hop_dur", "block_size", "hop_size", "max_time", "record",
                         "audio_source", "filename", "data_buffer", "frames_per_buffer", "sampling_rate",
                         "sample_width", "channels", "sr", "sw", "ch", "asrc", "fn", "fpb", "db", "mt",
                         "rec", "bd", "hd", "bs", "hs"]:
                raise ValueError("Invalid argument: {0}".format(k))
        
        if "block_dur" in kwargs and "bd" in kwargs:
            raise DuplicateArgument("Either 'block_dur' or 'bd' must be specified, not both")
        
        if "hop_dur" in kwargs and "hd" in kwargs:
            raise DuplicateArgument("Either 'hop_dur' or 'hd' must be specified, not both")
        
        if "block_size" in kwargs and "bs" in kwargs:
            raise DuplicateArgument("Either 'block_size' or 'bs' must be specified, not both")
        
        if "hop_size" in kwargs and "hs" in kwargs:
            raise DuplicateArgument("Either 'hop_size' or 'hs' must be specified, not both")
        
        if "max_time" in kwargs and "mt" in kwargs:
            raise DuplicateArgument("Either 'max_time' or 'mt' must be specified, not both")
        
        if "audio_source" in kwargs and "asrc" in kwargs:
            raise DuplicateArgument("Either 'audio_source' or 'asrc' must be specified, not both")
        
        if "filename" in kwargs and "fn" in kwargs:
            raise DuplicateArgument("Either 'filename' or 'fn' must be specified, not both")
        
        if "data_buffer" in kwargs and "db" in kwargs:
            raise DuplicateArgument("Either 'filename' or 'db' must be specified, not both")
        
        if "frames_per_buffer" in kwargs and "fbb" in kwargs:
            raise DuplicateArgument("Either 'frames_per_buffer' or 'fpb' must be specified, not both")
        
        if "sampling_rate" in kwargs and "sr" in kwargs:
            raise DuplicateArgument("Either 'sampling_rate' or 'sr' must be specified, not both")
        
        if "sample_width" in kwargs and "sw" in kwargs:
            raise DuplicateArgument("Either 'sample_width' or 'sw' must be specified, not both")
        
        if "channels" in kwargs and "ch" in kwargs:
            raise DuplicateArgument("Either 'channels' or 'ch' must be specified, not both")
        
        if "record" in kwargs and "rec" in kwargs:
            raise DuplicateArgument("Either 'record' or 'rec' must be specified, not both")
        
        
        kwargs["bd"] = kwargs.pop("block_dur", None) or kwargs.pop("bd", None)
        kwargs["hd"] = kwargs.pop("hop_dur", None) or kwargs.pop("hd", None)
        kwargs["bs"] = kwargs.pop("block_size", None) or kwargs.pop("bs", None)
        kwargs["hs"] = kwargs.pop("hop_size", None) or kwargs.pop("hs", None)
        kwargs["mt"] = kwargs.pop("max_time", None) or kwargs.pop("mt", None)
        kwargs["asrc"] = kwargs.pop("audio_source", None) or kwargs.pop("asrc", None)
        kwargs["fn"] = kwargs.pop("filename", None) or kwargs.pop("fn", None)
        kwargs["db"] = kwargs.pop("data_buffer", None) or kwargs.pop("db", None)
        
        record = kwargs.pop("record", False)
        if not record:
            record = kwargs.pop("rec", False)
            if not isinstance(record, bool):
                raise TypeError("'record' must be a boolean")
            
        kwargs["rec"] = record
        
        # keep long names for arguments meant for BufferAudioSource and PyAudioSource
        if "frames_per_buffer" in kwargs or "fpb" in kwargs:
            kwargs["frames_per_buffer"] = kwargs.pop("frames_per_buffer", None) or kwargs.pop("fpb", None)
        
        if "sampling_rate" in kwargs or "sr" in kwargs:
            kwargs["sampling_rate"] = kwargs.pop("sampling_rate", None) or kwargs.pop("sr", None)
        
        if "sample_width" in kwargs or "sw" in kwargs:    
            kwargs["sample_width"] = kwargs.pop("sample_width", None) or kwargs.pop("sw", None)
        
        if "channels" in kwargs or "ch" in kwargs:
            kwargs["channels"] = kwargs.pop("channels", None) or kwargs.pop("ch", None)
        
        
        
        
            
            
    
    @staticmethod
    def ads(**kwargs):
        
        """
        Create an return an :class:`ADSFactory.AudioDataSource`. The type and behavior of the object is the result
        of the supplied parameters.
        
        :Parameters:
        
        *No parameters* :  
           read audio data from the available built-in microphone with the default parameters.
           The returned :class:`ADSFactory.AudioDataSource` encapsulate an :class:`io.PyAudioSource` object and hence 
           it accepts the next four parameters are passed to use instead of their default values.
        
        `sampling_rate`, `sr` : *(int)*
            number of samples per second. Default = 16000.
        
        `sample_width`, `sw` : *(int)*
            number of bytes per sample (must be in (1, 2, 4)). Default = 2
        
        `channels`, `ch` : *(int)*
            number of audio channels. Default = 1 (only this value is currently accepted)  
            
        `frames_per_buffer`, `fpb` : *(int)*
            number of samples of PyAudio buffer. Default = 1024.
        
        `audio_source`, `asrc` : an `AudioSource` object
            read data from this audio source
            
        `filename`, `fn` : *(string)*
            build an `io.AudioSource` object using this file (currently only wave format is supported)
            
        `data_buffer`, `db` : *(string)*
            build an `io.BufferAudioSource` using data in `data_buffer`. If this keyword is used,
            `sampling_rate`, `sample_width` and `channels` are passed to `io.BufferAudioSource`
            constructor and used instead of default values.
            
        `max_time`, `mt` : *(float)*
            maximum time (in seconds) to read. Default behavior: read until there is no more data
            available. 
         
        `record`, `rec` : *(bool)*
            save all read data in cache. Provide a navigable object which boasts a `rewind` method.
            Default = False.
        
        `block_dur`, `bd` : *(float)*
            processing block duration in seconds. This represents the quantity of audio data to return 
            each time the :func:`read` method is invoked. If `block_dur` is 0.025 (i.e. 25 ms) and the sampling
            rate is 8000 and the sample width is 2 bytes, :func:`read` returns a buffer of 0.025 * 8000 * 2 = 400
            bytes at most. This parameter will be looked for (and used if available) before `block_size`.
            If neither parameter is given, `block_dur` will be set to 0.01 second (i.e. 10 ms)
            
            
        `hop_dur`, `hd` : *(float)*
            quantity of data to skip from current processing window. if `hop_dur` is supplied then there
            will be an overlap of `block_dur` - `hop_dur` between two adjacent blocks. This
            parameter will be looked for (and used if available) before `hop_size`. If neither parameter
            is given, `hop_dur` will be set to `block_dur` which means that there will be no overlap
            between two consecutively read blocks.
             
        `block_size`, `bs` : *(int)*
            number of samples to read each time the `read` method is called. Default: a block size
            that represents a window of 10ms, so for a sampling rate of 16000, the default `block_size`
            is 160 samples, for a rate of 44100, `block_size` = 441 samples, etc.
        
        `hop_size`, `hs` : *(int)*
            determines the number of overlapping samples between two adjacent read windows. For a
            `hop_size` of value *N*, the overlap is `block_size` - *N*. Default : `hop_size` = `block_size`,
            means that there is no overlap.
            
        :Returns:
        
        An AudioDataSource object that has the desired features.
        
        :Exampels:
        
        1. **Create an AudioDataSource that reads data from the microphone (requires Pyaudio) with default audio parameters:**
        
        .. code:: python
        
            from auditok import ADSFactory
            ads = ADSFactory.ads()
            ads.get_sampling_rate()
            16000
            ads.get_sample_width()
            2
            ads.get_channels()
            1
        
        
        2. **Create an AudioDataSource that reads data from the microphone with a sampling rate of 48KHz:**
        
        .. code:: python
        
            from auditok import ADSFactory
            ads = ADSFactory.ads(sr=48000)
            ads.get_sampling_rate()
            48000
        
        3. **Create an AudioDataSource that reads data from a wave file:**
        
        .. code:: python
        
            import auditok
            from auditok import ADSFactory
            ads = ADSFactory.ads(fn=auditok.dataset.was_der_mensch_saet_mono_44100_lead_trail_silence)
            ads.get_sampling_rate()
            44100
            ads.get_sample_width()
            2
            ads.get_channels()
            1
        
        4. **Define size of read blocks as 20 ms**
        
        .. code:: python
        
            import auditok
            from auditok import ADSFactory
            '''
            we know samling rate for previous file is 44100 samples/second
            so 10 ms are equivalent to 441 samples and 20 ms to 882
            '''
            block_size = 882
            ads = ADSFactory.ads(bs = 882, fn=auditok.dataset.was_der_mensch_saet_mono_44100_lead_trail_silence)
            ads.open()
            # read one block
            data = ads.read()
            ads.close()
            len(data)
            1764
            assert len(data) ==  ads.get_sample_width() * block_size
        
        5. **Define block size as a duration (use block_dur or bd):**
        
        .. code:: python
        
            import auditok
            from auditok import ADSFactory
            dur = 0.25 # second
            ads = ADSFactory.ads(bd = dur, fn=auditok.dataset.was_der_mensch_saet_mono_44100_lead_trail_silence)
            '''
            we know samling rate for previous file is 44100 samples/second
            for a block duration of 250 ms, block size should be 0.25 * 44100 = 11025
            '''
            ads.get_block_size()
            11025
            assert ads.get_block_size() ==  int(0.25 * 44100)
            ads.open()
            # read one block
            data = ads.read()
            ads.close()
            len(data)
            22050
            assert len(data) ==  ads.get_sample_width() * ads.get_block_size()
            
        6. **Read overlapping blocks (one of hope_size, hs, hop_dur or hd > 0):**
        
        For better readability we'd better use :class:`auditok.io.BufferAudioSource` with a string buffer:

        .. code:: python

            import auditok
            from auditok import ADSFactory
            '''
            we supply a data beffer instead of a file (keyword 'bata_buffer' or 'db')
            sr : sampling rate = 16 samples/sec
            sw : sample width = 1 byte
            ch : channels = 1
            '''
            buffer = "abcdefghijklmnop" # 16 bytes = 1 second of data
            bd = 0.250 # block duration = 250 ms = 4 bytes
            hd = 0.125 # hop duration = 125 ms = 2 bytes 
            ads = ADSFactory.ads(db = "abcdefghijklmnop", bd = bd, hd = hd, sr = 16, sw = 1, ch = 1)
            ads.open()
            ads.read()
            'abcd'
            ads.read()
            'cdef'
            ads.read()
            'efgh'
            ads.read()
            'ghij'
            data = ads.read()
            assert data == 'ijkl'
        
        7. **Limit amount of read data (use max_time or mt):**
        
        .. code:: python
        
            '''
            We know audio file is larger than 2.25 seconds
            We want to read up to 2.25 seconds of audio data
            '''
            ads = ADSFactory.ads(mt = 2.25, fn=auditok.dataset.was_der_mensch_saet_mono_44100_lead_trail_silence)
            ads.open()
            data = []
            while True:
                d = ads.read()
                if d is None:
                    break
                data.append(d)
                
            ads.close()
            data = b''.join(data)
            assert len(data) == int(ads.get_sampling_rate() * 2.25 * ads.get_sample_width() * ads.get_channels())
        """
        
        # copy user's dicionary (shallow copy)
        kwargs = kwargs.copy()
        
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
                raise Warning("You should provide one of 'audio_source', 'filename' or 'data_buffer'\
                 keyword parameters. 'audio_source' will be used")
            
        # Case 2: a file name is supplied
        elif filename is not None:
            if data_buffer is not None:
                raise Warning("You should provide one of 'filename' or 'data_buffer'\
                 keyword parameters. 'filename' will be used")
            audio_source = from_file(filename)
            
        # Case 3: a data_buffer is supplied 
        elif data_buffer is not None:
            audio_source = BufferAudioSource(data_buffer = data_buffer, **kwargs)
            
        # Case 4: try to access native audio input
        else:
            audio_source = PyAudioSource(**kwargs)
             
             
        if block_dur is not None:
            if block_size is not None:
                raise DuplicateArgument("Either 'block_dur' or 'block_size' can be specified, not both")
            else:
                block_size = int(audio_source.get_sampling_rate() * block_dur)
        elif block_size is None:
            # Set default block_size to 10 ms
            block_size = int(audio_source.get_sampling_rate() / 100)

        # Instantiate base AudioDataSource  
        ads = ADSFactory.AudioDataSource(audio_source=audio_source, block_size=block_size)
        
        # Limit data to be read
        if max_time is not None:
            ads = ADSFactory.LimiterADS(ads=ads, max_time=max_time)
        
        # Record, rewind and reuse data
        if record:
            ads = ADSFactory.RecorderADS(ads=ads)
            
        # Read overlapping blocks of data
        if hop_dur is not None:
            if hop_size is not None:
                raise DuplicateArgument("Either 'hop_dur' or 'hop_size' can be specified, not both")
            else:
                hop_size = int(audio_source.get_sampling_rate() * hop_dur)
            
        if hop_size is not None:
            if hop_size <= 0 or  hop_size > block_size:
                raise ValueError("hop_size must be > 0 and <= block_size")
            if hop_size < block_size:
                ads = ADSFactory.OverlapADS(ads=ads, hop_size=hop_size)
        
        return ads
        
        
    class AudioDataSource(DataSource):
        """
        Base class for AudioDataSource objects.
        It inherits from DataSource and encapsulates an AudioSource object.
        """
        
        def __init__(self, audio_source, block_size):
            
            self.audio_source = audio_source
            self.block_size = block_size
                
        def get_block_size(self):
            return self.block_size
        
        def set_block_size(self, size):
            self.block_size = size

        def get_audio_source(self):
            return self.audio_source
        
        def set_audio_source(self, audio_source):
            self.audio_source = audio_source
            
        def open(self):
            self.audio_source.open()
        
        def close(self):
            self.audio_source.close()
            
        def is_open(self):
            return self.audio_source.is_open()
        
        def get_sampling_rate(self):
            return self.audio_source.get_sampling_rate()
        
        def get_sample_width(self):
            return self.audio_source.get_sample_width()
        
        def get_channels(self):
            return self.audio_source.get_channels()
        
        
        def rewind(self):
            if isinstance(self.audio_source, Rewindable):
                self.audio_source.rewind()
            else:
                raise Exception("Audio source is not rewindable")
            
            
        
        def is_rewindable(self):
            return isinstance(self.audio_source, Rewindable)
        
            
        def read(self):
            return self.audio_source.read(self.block_size)


    class ADSDecorator(AudioDataSource):
        """
        Base decorator class for AudioDataSource objects.
        """
        __metaclass__ = ABCMeta
        
        def __init__(self, ads):
            self.ads = ads
            
            self.get_block_size = self.ads.get_block_size
            self.set_block_size = self.ads.set_block_size
            self.get_audio_source = self.ads.get_audio_source
            self.open = self.ads.open
            self.close = self.ads.close
            self.is_open = self.ads.is_open
            self.get_sampling_rate = self.ads.get_sampling_rate
            self.get_sample_width = self.ads.get_sample_width
            self.get_channels = self.ads.get_channels
        
        def is_rewindable(self):
            return self.ads.is_rewindable
            
        def rewind(self):
            self.ads.rewind()
            self._reinit()
            
        def set_audio_source(self, audio_source):
            self.ads.set_audio_source(audio_source)
            self._reinit()
        
        def open(self):
            if not self.ads.is_open():
                self.ads.open()
                self._reinit()
            
        @abstractmethod
        def _reinit(self):
            pass            
        
        
    class OverlapADS(ADSDecorator):
        """
        A class for AudioDataSource objects that can read and return overlapping audio frames
        """
        
        def __init__(self, ads, hop_size):
            ADSFactory.ADSDecorator.__init__(self, ads)
            
            if hop_size <= 0 or hop_size > self.get_block_size():
                raise ValueError("hop_size must be either 'None' or \
                 between 1 and block_size (both inclusive)")
            self.hop_size = hop_size
            self._actual_block_size = self.get_block_size()
            self._reinit()
            
            
            def _get_block_size():
                return self._actual_block_size
            
            
        def _read_first_block(self):
            # For the first call, we need an entire block of size 'block_size'
            block = self.ads.read()
            if block is None:
                return None
            
            # Keep a slice of data in cache and append it in the next call
            if len(block) > self._hop_size_bytes:
                self._cache = block[self._hop_size_bytes:]
            
            # Up from the next call, we will use '_read_next_blocks'
            # and we only read 'hop_size'
            self.ads.set_block_size(self.hop_size)
            self.read = self._read_next_blocks
            
            return block
                
        def _read_next_blocks(self):
            block = self.ads.read()
            if block is None:
                return None
            
            # Append block to cache data to ensure overlap
            block = self._cache + block
            # Keep a slice of data in cache only if we have a full length block
            # if we don't that means that this is the last block
            if len(block) == self._block_size_bytes:
                self._cache = block[self._hop_size_bytes:]
            else:
                self._cache = None
                
            return block

        def read(self):
            pass
        
        def _reinit(self):
            self._cache = None
            self.ads.set_block_size(self._actual_block_size)
            self._hop_size_bytes = self.hop_size * \
                               self.get_sample_width() * \
                               self.get_channels()
            self._block_size_bytes = self.get_block_size() * \
                               self.get_sample_width() * \
                               self.get_channels()
            self.read = self._read_first_block



    class LimiterADS(ADSDecorator):
        """
        A class for AudioDataSource objects that can read a fixed amount of data.
        This can be useful when reading data from the microphone or from large audio files.
        """
        
        def __init__(self, ads, max_time):
            ADSFactory.ADSDecorator.__init__(self, ads)
            
            self.max_time = max_time
            self._reinit()
            
        def read(self):
            if self._total_read_bytes >=  self._max_read_bytes:
                return None
            block = self.ads.read()
            if block is None:
                return None
            self._total_read_bytes += len(block)
            
            if self._total_read_bytes >=  self._max_read_bytes:
                self.close()
            
            return block
                
                
        def _reinit(self):
            self._max_read_bytes = int(self.max_time  * self.get_sampling_rate()) * \
                                  self.get_sample_width() * \
                                  self.get_channels()
            self._total_read_bytes = 0

            

    class RecorderADS(ADSDecorator):
        """
        A class for AudioDataSource objects that can record all audio data they read,
        with a rewind facility.
        """
        
        def __init__(self, ads):
            ADSFactory.ADSDecorator.__init__(self, ads)
            
            self._reinit()
            
        def read(self):
            pass
        
        def _read_and_rec(self):
            # Read and save read data
            block = self.ads.read()
            if block is not None:
                self._cache.append(block)
            
            return block
            
            
        def _read_simple(self):
            # Read without recording
            return self.ads.read()

        def rewind(self):
            if self._record:
                # If has been recording, create a new BufferAudioSource
                # from recorded data
                dbuffer = self._concatenate(self._cache)
                asource = BufferAudioSource(dbuffer, self.get_sampling_rate(),
                                             self.get_sample_width(),
                                             self.get_channels())
                
                
                self.set_audio_source(asource)
                self.open()
                self._cache = []
                self._record = False
                self.read = self._read_simple
            
            else:
                self.ads.rewind()
                if not self.is_open():
                    self.open()
                    
        
        def is_rewindable(self):
            return True
        
        def _reinit(self):
            # when audio_source is replaced, start recording again
            self._record = True
            self._cache = []
            self.read = self._read_and_rec
        
        def _concatenate(self, data):
            try:
                # should always work for python 2
                # work for python 3 ONLY if data is a list (or an iterator)
                # whose each element is a 'bytes' objects
                return b''.join(data)
            except TypeError:
                # work for 'str' in python 2 and python 3
                return ''.join(data)


class AudioEnergyValidator(DataValidator):
    """
    The most basic auditok audio frame validator.
    This validator computes the log energy of an input audio frame
    and return True if the result is >= a given threshold, False 
    otherwise.
    
    :Parameters:
    
    `sample_width` : *(int)*
        Number of bytes of one audio sample. This is used to convert data from `basestring` or `Bytes` to
        an array of floats.
        
    `energy_threshold` : *(float)*
        A threshold used to check whether an input data buffer is valid.
    """
    
    
    if _WITH_NUMPY:
        
        _formats = {1: numpy.int8 , 2: numpy.int16, 4: numpy.int32}

        @staticmethod
        def _convert(signal, sample_width):
            return numpy.array(numpy.frombuffer(signal, dtype=AudioEnergyValidator._formats[sample_width]), dtype=numpy.float64)                             
            
        @staticmethod
        def _signal_energy(signal):
            return float(numpy.dot(signal, signal)) / len(signal)
        
        @staticmethod    
        def _signal_log_energy(signal):
            energy = AudioEnergyValidator._signal_energy(signal)
            if energy <= 0:
                return -200
            return 10. * numpy.log10(energy)
        
    else:
        
        
        _formats = {1: 'b' , 2: 'h', 4: 'i'}
        
        @staticmethod
        def _convert(signal, sample_width):
            return array("d", array(AudioEnergyValidator._formats[sample_width], signal))
        
        @staticmethod
        def _signal_energy(signal):
            energy = 0.
            for a in signal:
                energy += a * a
            return energy / len(signal)
        
        @staticmethod    
        def _signal_log_energy(signal):
            energy = AudioEnergyValidator._signal_energy(signal)
            if energy <= 0:
                return -200
            return 10. * math.log10(energy)
            
    
    def __init__(self, sample_width, energy_threshold=45):
        self.sample_width = sample_width
        self._energy_threshold = energy_threshold
        
            
    def is_valid(self, data):
        """
        Check if data is valid. Audio data will be converted into an array (of
        signed values) of which the log energy is computed. Log energy is computed
        as follows:
        
        .. code:: python
        
            arr = AudioEnergyValidator._convert(signal, sample_width)
            energy = float(numpy.dot(arr, arr)) / len(arr)
            log_energy = 10. * numpy.log10(energy)
        
        
        :Parameters:
        
        `data` : either a *string* or a *Bytes* buffer
            `data` is converted into a numerical array using the `sample_width`
            given in the constructor.
        
        :Retruns:
        
        True if `log_energy` >= `energy_threshold`, False otherwise.
        """
        
        signal = AudioEnergyValidator._convert(data, self.sample_width)
        return AudioEnergyValidator._signal_log_energy(signal) >= self._energy_threshold
    
    def get_energy_threshold(self):
        return self._energy_threshold
    
    def set_energy_threshold(self, threshold):
        self._energy_threshold = threshold

