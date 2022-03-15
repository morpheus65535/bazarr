"""
This module gathers processing (i.e. tokenization) classes.

Class summary
=============

.. autosummary::

        StreamTokenizer
"""

from auditok.util import DataValidator

__all__ = ["StreamTokenizer"]


class StreamTokenizer():
    """
    Class for stream tokenizers. It implements a 4-state automaton scheme
    to extract sub-sequences of interest on the fly.
    
    :Parameters:
    
        `validator` :
            instance of `DataValidator` that implements `is_valid` method.
        
        `min_length` : *(int)*
            Minimum number of frames of a valid token. This includes all \
            tolerated non valid frames within the token.
            
        `max_length` : *(int)*
            Maximum number of frames of a valid token. This includes all \
            tolerated non valid frames within the token.
        
        `max_continuous_silence` : *(int)*
            Maximum number of consecutive non-valid frames within a token.
            Note that, within a valid token, there may be many tolerated \
            *silent* regions that contain each a number of non valid frames up to \
            `max_continuous_silence`
        
        `init_min` : *(int, default=0)*
            Minimum number of consecutive valid frames that must be **initially** \
            gathered before any sequence of non valid frames can be tolerated. This
            option is not always needed, it can be used to drop non-valid tokens as
            early as possible. **Default = 0** means that the option is by default 
            ineffective. 
                
        `init_max_silence` : *(int, default=0)*
            Maximum number of tolerated consecutive non-valid frames if the \
            number already gathered valid frames has not yet reached 'init_min'.
            This argument is normally used if `init_min` is used. **Default = 0**,
            by default this argument is not taken into consideration.
            
        `mode` : *(int, default=0)*
            `mode` can be:
        
        1. `StreamTokenizer.STRICT_MIN_LENGTH`: 
        if token *i* is delivered because `max_length`
        is reached, and token *i+1* is immediately adjacent to
        token *i* (i.e. token *i* ends at frame *k* and token *i+1* starts
        at frame *k+1*) then accept token *i+1* only of it has a size of at
        least `min_length`. The default behavior is to accept token *i+1*
        event if it is shorter than `min_length` (given that the above conditions
        are fulfilled of course).
           
        :Examples:
               
        In the following code, without `STRICT_MIN_LENGTH`, the 'BB' token is
        accepted although it is shorter than `min_length` (3), because it immediately
        follows the latest delivered token:
            
        .. code:: python
        
            from auditok import StreamTokenizer, StringDataSource, DataValidator
    
            class UpperCaseChecker(DataValidator):
                def is_valid(self, frame):
                    return frame.isupper()
                   
    
            dsource = StringDataSource("aaaAAAABBbbb")
            tokenizer = StreamTokenizer(validator=UpperCaseChecker(),
                                        min_length=3,
                                        max_length=4,
                                        max_continuous_silence=0)
         
            tokenizer.tokenize(dsource)
                    
                    
        :output:
    
         .. code:: python
         
            [(['A', 'A', 'A', 'A'], 3, 6), (['B', 'B'], 7, 8)]


        The following tokenizer will however reject the 'BB' token:
     
        .. code:: python
                
            dsource = StringDataSource("aaaAAAABBbbb")
            tokenizer = StreamTokenizer(validator=UpperCaseChecker(), 
                                        min_length=3, max_length=4,
                                        max_continuous_silence=0,
                                        mode=StreamTokenizer.STRICT_MIN_LENGTH)
            tokenizer.tokenize(dsource)
        
        :output:
            
        .. code:: python
            
            [(['A', 'A', 'A', 'A'], 3, 6)]
            
           
        2. `StreamTokenizer.DROP_TRAILING_SILENCE`: drop all tailing non-valid frames
        from a token to be delivered if and only if it is not **truncated**.
        This can be a bit tricky. A token is actually delivered if:
           
        - a. `max_continuous_silence` is reached
           
        :or:
           
        - b. Its length reaches `max_length`. This is called a **truncated** token
           
        In the current implementation, a `StreamTokenizer`'s decision is only based on already seen
        data and on incoming data. Thus, if a token is truncated at a non-valid but tolerated
        frame (`max_length` is reached but `max_continuous_silence` not yet) any tailing
        silence will be kept because it can potentially be part of valid token (if `max_length`
        was bigger). But if `max_continuous_silence` is reached before `max_length`, the delivered
        token will not be considered as truncated but a result of *normal* end of detection
        (i.e. no more valid data). In that case the tailing silence can be removed if you use
        the `StreamTokenizer.DROP_TRAILING_SILENCE` mode.
    
        :Example:
    
        .. code:: python
                       
             tokenizer = StreamTokenizer(validator=UpperCaseChecker(), min_length=3,
                                         max_length=6, max_continuous_silence=3,
                                         mode=StreamTokenizer.DROP_TRAILING_SILENCE)
            
             dsource = StringDataSource("aaaAAAaaaBBbbbb")
             tokenizer.tokenize(dsource)
        
        :output:
            
        .. code:: python
                
            [(['A', 'A', 'A', 'a', 'a', 'a'], 3, 8), (['B', 'B'], 9, 10)]
                    
        The first token is delivered with its tailing silence because it is truncated
        while the second one has its tailing frames removed.
                    
        Without `StreamTokenizer.DROP_TRAILING_SILENCE` the output would be:
                        
        .. code:: python
         
            [(['A', 'A', 'A', 'a', 'a', 'a'], 3, 8), (['B', 'B', 'b', 'b', 'b'], 9, 13)]
    
        
        
        3. `StreamTokenizer.STRICT_MIN_LENGTH | StreamTokenizer.DROP_TRAILING_SILENCE`:
        use both options. That means: first remove tailing silence, then ckeck if the
        token still has at least a length of `min_length`.
    """
    
    
    SILENCE = 0
    POSSIBLE_SILENCE = 1
    POSSIBLE_NOISE = 2 
    NOISE = 3
    
    STRICT_MIN_LENGTH = 2
    DROP_TRAILING_SILENCE = 4
    # alias
    DROP_TAILING_SILENCE = 4
    
    def __init__(self, validator, 
                 min_length, max_length, max_continuous_silence,
                 init_min=0, init_max_silence=0,
                 mode=0):
        
        if not isinstance(validator, DataValidator):
            raise TypeError("'validator' must be an instance of 'DataValidator'")
        
        if max_length <= 0:
            raise ValueError("'max_length' must be > 0 (value={0})".format(max_length))
        
        if min_length <= 0 or min_length > max_length:
            raise ValueError("'min_length' must be > 0 and <= 'max_length' (value={0})".format(min_length))
        
        if max_continuous_silence >= max_length:
            raise ValueError("'max_continuous_silence' must be < 'max_length' (value={0})".format(max_continuous_silence))
        
        if init_min >= max_length:
            raise ValueError("'init_min' must be < 'max_length' (value={0})".format(max_continuous_silence))
            
        self.validator = validator
        self.min_length = min_length
        self.max_length = max_length
        self.max_continuous_silence = max_continuous_silence
        self.init_min = init_min
        self.init_max_silent = init_max_silence
        
        self._mode = None
        self.set_mode(mode)
        self._strict_min_length = (mode & self.STRICT_MIN_LENGTH) != 0
        self._drop_tailing_silence  = (mode & self.DROP_TRAILING_SILENCE) != 0
        
        self._deliver = None
        self._tokens = None
        self._state = None
        self._data = None
        self._contiguous_token = False
        
        self._init_count = 0
        self._silence_length = 0
        self._start_frame = 0
        self._current_frame = 0
    
    def set_mode(self, mode):
        """
        :Parameters:
        
            `mode` : *(int)*
                New mode, must be one of:
                    
                
            - `StreamTokenizer.STRICT_MIN_LENGTH`
            
            - `StreamTokenizer.DROP_TRAILING_SILENCE`
            
            - `StreamTokenizer.STRICT_MIN_LENGTH | StreamTokenizer.DROP_TRAILING_SILENCE`
                   
            - `0`
                       
        See `StreamTokenizer.__init__` for more information about the mode.
        """
        
        if not mode in [self.STRICT_MIN_LENGTH, self.DROP_TRAILING_SILENCE,
           self.STRICT_MIN_LENGTH | self.DROP_TRAILING_SILENCE, 0]:
            
            raise ValueError("Wrong value for mode")
        
        self._mode = mode
        self._strict_min_length = (mode & self.STRICT_MIN_LENGTH) != 0
        self._drop_tailing_silence  = (mode & self.DROP_TRAILING_SILENCE) != 0
        
    
    def get_mode(self):
        """
        Return the current mode. To check whether a specific mode is activated use
        the bitwise 'and' operator `&`. Example:
           
        .. code:: python 
                
            if mode & self.STRICT_MIN_LENGTH != 0:
               do_something()
        """
        return self._mode
        
    def _reinitialize(self):
        self._contiguous_token = False
        self._data = []
        self._tokens = []
        self._state = self.SILENCE
        self._current_frame = -1
        self._deliver = self._append_token
    
    
    def tokenize(self, data_source, callback=None):
        """
        Read data from `data_source`, one frame a time, and process the read frames in
        order to detect sequences of frames that make up valid tokens.
        
        :Parameters:
           `data_source` : instance of the :class:`DataSource` class that implements a `read` method.
               'read' should return a slice of signal, i.e. frame (of whatever \
               type as long as it can be processed by validator) and None if \
               there is no more signal.
        
           `callback` : an optional 3-argument function.
               If a `callback` function is given, it will be called each time a valid token
               is found.
           
           
        :Returns:
           A list of tokens if `callback` is None. Each token is tuple with the following elements:
        
            .. code python
            
                (data, start, end)
            
           where `data` is a list of read frames, `start`: index of the first frame in the
           original data and `end` : index of the last frame. 
        
        """
        
        self._reinitialize()
        
        if callback is not None:
            self._deliver = callback
        
        while True:
            frame =  data_source.read()
            if frame is None:
                break
            self._current_frame += 1
            self._process(frame)
            
        self._post_process()
        
        if callback is None:
            _ret = self._tokens
            self._tokens = None
            return _ret
        
        
    def _process(self, frame):
        
        frame_is_valid = self.validator.is_valid(frame)
        
        if self._state == self.SILENCE:
            
            if frame_is_valid:
                # seems we got a valid frame after a silence
                self._init_count = 1
                self._silence_length = 0
                self._start_frame = self._current_frame
                self._data.append(frame)
                
                if self._init_count  >= self.init_min:
                    self._state = self.NOISE
                    if len(self._data) >= self.max_length:
                        self._process_end_of_detection(True)
                else:
                    self._state = self.POSSIBLE_NOISE
        
        elif self._state == self.POSSIBLE_NOISE:
            
            if frame_is_valid:
                self._silence_length = 0
                self._init_count += 1
                self._data.append(frame)
                if self._init_count  >= self.init_min:
                    self._state = self.NOISE
                    if len(self._data) >= self.max_length:
                        self._process_end_of_detection(True)
            
            else:                
                self._silence_length += 1
                if self._silence_length > self.init_max_silent or \
                len(self._data) + 1 >= self.max_length:
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
                    self._process_end_of_detection(True)
            
            elif self.max_continuous_silence <= 0 :
                # max token reached at this frame will _deliver if _contiguous_token
                # and not _strict_min_length
                self._process_end_of_detection()
                self._state = self.SILENCE
                
            else:
                # this is the first silent frame following a valid one
                # and it is tolerated
                self._silence_length = 1
                self._data.append(frame)
                self._state = self.POSSIBLE_SILENCE
                if len(self._data) == self.max_length:
                    self._process_end_of_detection(True)
                    # don't reset _silence_length because we still 
                    # need to know the total number of silent frames
                                   
                                
    
        elif self._state == self.POSSIBLE_SILENCE:
            
            if frame_is_valid:
                self._data.append(frame)
                self._silence_length = 0
                self._state = self.NOISE
                if len(self._data) >= self.max_length:
                    self._process_end_of_detection(True)
                
            else:
                if self._silence_length >= self.max_continuous_silence:
                    if self._silence_length < len(self._data):
                        # _deliver only gathered frames aren't all silent                    
                        self._process_end_of_detection()
                    else:
                        self._data = []
                    self._state = self.SILENCE
                    self._silence_length = 0
                else:
                    self._data.append(frame)
                    self._silence_length += 1
                    if len(self._data) >= self.max_length:
                        self._process_end_of_detection(True)
                        # don't reset _silence_length because we still 
                        # need to know the total number of silent frames
                        
    
    def _post_process(self):
        if self._state == self.NOISE or self._state == self.POSSIBLE_SILENCE:
            if len(self._data) > 0 and len(self._data) > self._silence_length:
                self._process_end_of_detection()
    
    
    def _process_end_of_detection(self, truncated=False):
        
        if not truncated and self._drop_tailing_silence and self._silence_length > 0:
            # happens if max_continuous_silence is reached
            # or max_length is reached at a silent frame
            self._data = self._data[0: - self._silence_length]
        
        if (len(self._data) >= self.min_length) or \
           (len(self._data) > 0 and \
            not self._strict_min_length and self._contiguous_token):
            
            
            
            _end_frame = self._start_frame + len(self._data) - 1
            self._deliver(self._data, self._start_frame, _end_frame)
            
            if truncated:
                # next token (if any) will start at _current_frame + 1
                self._start_frame = self._current_frame + 1
                # remember that it is contiguous with the just delivered one
                self._contiguous_token = True
            else:
                self._contiguous_token = False
        else:
            self._contiguous_token = False       
        
        self._data = []
            
    
    
    def _append_token(self, data, start, end):
        self._tokens.append((data, start, end))
