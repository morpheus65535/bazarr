class DuplicateArgument(Exception):
    pass


class TooSamllBlockDuration(ValueError):
    """Raised when block_dur results in a block_size smaller than one sample."""

    def __init__(self, message, block_dur, sampling_rate):
        self.block_dur = block_dur
        self.sampling_rate = sampling_rate
        super(TooSamllBlockDuration, self).__init__(message)


class TimeFormatError(Exception):
    """Raised when a duration formatting directive is unknown."""


class EndOfProcessing(Exception):
    """Raised within command line script's main function to jump to
    postprocessing code."""


class AudioIOError(Exception):
    """Raised when a compressed audio file cannot be loaded or when trying
    to read from a not yet open AudioSource"""


class AudioParameterError(AudioIOError):
    """Raised when one audio parameter is missing when loading raw data or
    saving data to a format other than raw. Also raised when an audio
    parameter has a wrong value."""


class AudioEncodingError(Exception):
    """Raised if audio data can not be encoded in the provided format"""


class AudioEncodingWarning(RuntimeWarning):
    """Raised if audio data can not be encoded in the provided format
    but saved as wav.
    """
