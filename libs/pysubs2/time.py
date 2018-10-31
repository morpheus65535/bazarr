from __future__ import division

from collections import namedtuple
import re


#: Pattern that matches both SubStation and SubRip timestamps.
TIMESTAMP = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{2,3})")

Times = namedtuple("Times", ["h", "m", "s", "ms"])

def make_time(h=0, m=0, s=0, ms=0, frames=None, fps=None):
    """
    Convert time to milliseconds.

    See :func:`pysubs2.time.times_to_ms()`. When both frames and fps are specified,
    :func:`pysubs2.time.frames_to_ms()` is called instead.

    Raises:
        ValueError: Invalid fps, or one of frames/fps is missing.

    Example:
        >>> make_time(s=1.5)
        1500
        >>> make_time(frames=50, fps=25)
        2000

    """
    if frames is None and fps is None:
        return times_to_ms(h, m, s, ms)
    elif frames is not None and fps is not None:
        return frames_to_ms(frames, fps)
    else:
        raise ValueError("Both fps and frames must be specified")

def timestamp_to_ms(groups):
    """
    Convert groups from :data:`pysubs2.time.TIMESTAMP` match to milliseconds.
    
    Example:
        >>> timestamp_to_ms(TIMESTAMP.match("0:00:00.42").groups())
        420
    
    """
    h, m, s, frac = map(int, groups)
    ms = frac * 10**(3 - len(groups[-1]))
    ms += s * 1000
    ms += m * 60000
    ms += h * 3600000
    return ms

def times_to_ms(h=0, m=0, s=0, ms=0):
    """
    Convert hours, minutes, seconds to milliseconds.
    
    Arguments may be positive or negative, int or float,
    need not be normalized (``s=120`` is okay).
    
    Returns:
        Number of milliseconds (rounded to int).
    
    """
    ms += s * 1000
    ms += m * 60000
    ms += h * 3600000
    return int(round(ms))

def frames_to_ms(frames, fps):
    """
    Convert frame-based duration to milliseconds.
    
    Arguments:
        frames: Number of frames (should be int).
        fps: Framerate (must be a positive number, eg. 23.976).
    
    Returns:
        Number of milliseconds (rounded to int).
        
    Raises:
        ValueError: fps was negative or zero.
    
    """
    if fps <= 0:
        raise ValueError("Framerate must be positive number (%f)." % fps)

    return int(round(frames * (1000 / fps)))

def ms_to_frames(ms, fps):
    """
    Convert milliseconds to number of frames.
    
    Arguments:
        ms: Number of milliseconds (may be int, float or other numeric class).
        fps: Framerate (must be a positive number, eg. 23.976).
    
    Returns:
        Number of frames (int).
        
    Raises:
        ValueError: fps was negative or zero.
    
    """
    if fps <= 0:
        raise ValueError("Framerate must be positive number (%f)." % fps)

    return int(round((ms / 1000) * fps))

def ms_to_times(ms):
    """
    Convert milliseconds to normalized tuple (h, m, s, ms).
    
    Arguments:
        ms: Number of milliseconds (may be int, float or other numeric class).
            Should be non-negative.
    
    Returns:
        Named tuple (h, m, s, ms) of ints.
        Invariants: ``ms in range(1000) and s in range(60) and m in range(60)``
    
    """
    ms = int(round(ms))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return Times(h, m, s, ms)

def ms_to_str(ms, fractions=False):
    """
    Prettyprint milliseconds to [-]H:MM:SS[.mmm]
    
    Handles huge and/or negative times. Non-negative times with ``fractions=True``
    are matched by :data:`pysubs2.time.TIMESTAMP`.
    
    Arguments:
        ms: Number of milliseconds (int, float or other numeric class).
        fractions: Whether to print up to millisecond precision.
    
    Returns:
        str
    
    """
    sgn = "-" if ms < 0 else ""
    h, m, s, ms = ms_to_times(abs(ms))
    if fractions:
        return sgn + "{:01d}:{:02d}:{:02d}.{:03d}".format(h, m, s, ms)
    else:
        return sgn + "{:01d}:{:02d}:{:02d}".format(h, m, s)
