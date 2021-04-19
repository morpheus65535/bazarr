"""
Module for basic audio signal processing and array operations.

.. autosummary::
    :toctree: generated/

    to_array
    extract_single_channel
    compute_average_channel
    compute_average_channel_stereo
    separate_channels
    calculate_energy_single_channel
    calculate_energy_multichannel
"""
from array import array as array_
import audioop
import math

FORMAT = {1: "b", 2: "h", 4: "i"}
_EPSILON = 1e-10


def to_array(data, sample_width, channels):
    """Extract individual channels of audio data and return a list of arrays of
    numeric samples. This will always return a list of `array.array` objects
    (one per channel) even if audio data is mono.

    Parameters
    ----------
    data : bytes
        raw audio data.
    sample_width : int
        size in bytes of one audio sample (one channel considered).

    Returns
    -------
    samples_arrays : list
        list of arrays of audio samples.
    """
    fmt = FORMAT[sample_width]
    if channels == 1:
        return [array_(fmt, data)]
    return separate_channels(data, fmt, channels)


def extract_single_channel(data, fmt, channels, selected):
    samples = array_(fmt, data)
    return samples[selected::channels]


def compute_average_channel(data, fmt, channels):
    """
    Compute and return average channel of multi-channel audio data. If the
    number of channels is 2, use :func:`compute_average_channel_stereo` (much
    faster). This function uses satandard `array` module to convert `bytes` data
    into an array of numeric values.

    Parameters
    ----------
    data : bytes
        multi-channel audio data to mix down.
    fmt : str
        format (single character) to pass to `array.array` to convert `data`
        into an array of samples. This should be "b" if audio data's sample width
        is 1, "h" if it's 2 and "i" if it's 4.
    channels : int
        number of channels of audio data.

    Returns
    -------
    mono_audio : bytes
        mixed down audio data.
    """
    all_channels = array_(fmt, data)
    mono_channels = [
        array_(fmt, all_channels[ch::channels]) for ch in range(channels)
    ]
    avg_arr = array_(
        fmt,
        (round(sum(samples) / channels) for samples in zip(*mono_channels)),
    )
    return avg_arr


def compute_average_channel_stereo(data, sample_width):
    """Compute and return average channel of stereo audio data. This function
    should be used when the number of channels is exactly 2 because in that
    case we can use standard `audioop` module which *much* faster then calling
    :func:`compute_average_channel`.

    Parameters
    ----------
    data : bytes
        2-channel audio data to mix down.
    sample_width : int
        size in bytes of one audio sample (one channel considered).

    Returns
    -------
    mono_audio : bytes
        mixed down audio data.
    """
    fmt = FORMAT[sample_width]
    arr = array_(fmt, audioop.tomono(data, sample_width, 0.5, 0.5))
    return arr


def separate_channels(data, fmt, channels):
    """Create a list of arrays of audio samples (`array.array` objects), one for
    each channel.

    Parameters
    ----------
    data : bytes
        multi-channel audio data to mix down.
    fmt : str
        format (single character) to pass to `array.array` to convert `data`
        into an array of samples. This should be "b" if audio data's sample width
        is 1, "h" if it's 2 and "i" if it's 4.
    channels : int
        number of channels of audio data.

    Returns
    -------
    channels_arr : list
        list of audio channels, each as a standard `array.array`.
    """
    all_channels = array_(fmt, data)
    mono_channels = [
        array_(fmt, all_channels[ch::channels]) for ch in range(channels)
    ]
    return mono_channels


def calculate_energy_single_channel(data, sample_width):
    """Calculate the energy of mono audio data. Energy is computed as:

    .. math:: energy = 20 \log(\sqrt({1}/{N}\sum_{i}^{N}{a_i}^2)) % # noqa: W605

    where `a_i` is the i-th audio sample and `N` is the number of audio samples
    in data.

    Parameters
    ----------
    data : bytes
        single-channel audio data.
    sample_width : int
        size in bytes of one audio sample.

    Returns
    -------
    energy : float
        energy of audio signal.
    """
    energy_sqrt = max(audioop.rms(data, sample_width), _EPSILON)
    return 20 * math.log10(energy_sqrt)


def calculate_energy_multichannel(x, sample_width, aggregation_fn=max):
    """Calculate the energy of multi-channel audio data. Energy is calculated
    channel-wise. An aggregation function is applied to the resulting energies
    (default: `max`). Also see :func:`calculate_energy_single_channel`.

    Parameters
    ----------
    data : bytes
        single-channel audio data.
    sample_width : int
        size in bytes of one audio sample (one channel considered).
    aggregation_fn : callable, default: max
        aggregation function to apply to the resulting per-channel energies.

    Returns
    -------
    energy : float
        aggregated energy of multi-channel audio signal.
    """
    energies = (calculate_energy_single_channel(xi, sample_width) for xi in x)
    return aggregation_fn(energies)
