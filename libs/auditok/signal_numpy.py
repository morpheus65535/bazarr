import numpy as np
from .signal import (
    compute_average_channel_stereo,
    calculate_energy_single_channel,
    calculate_energy_multichannel,
)

FORMAT = {1: np.int8, 2: np.int16, 4: np.int32}


def to_array(data, sample_width, channels):
    fmt = FORMAT[sample_width]
    if channels == 1:
        return np.frombuffer(data, dtype=fmt).astype(np.float64)
    return separate_channels(data, fmt, channels).astype(np.float64)


def extract_single_channel(data, fmt, channels, selected):
    samples = np.frombuffer(data, dtype=fmt)
    return np.asanyarray(samples[selected::channels], order="C")


def compute_average_channel(data, fmt, channels):
    array = np.frombuffer(data, dtype=fmt).astype(np.float64)
    return array.reshape(-1, channels).mean(axis=1).round().astype(fmt)


def separate_channels(data, fmt, channels):
    array = np.frombuffer(data, dtype=fmt)
    return np.asanyarray(array.reshape(-1, channels).T, order="C")
