"""
    pint.converters
    ~~~~~~~~~~~~~~~

    Functions and classes related to unit conversions.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from .compat import HAS_NUMPY, exp, log  # noqa: F401


class Converter:
    """Base class for value converters."""

    @property
    def is_multiplicative(self):
        return True

    @property
    def is_logarithmic(self):
        return False

    def to_reference(self, value, inplace=False):
        return value

    def from_reference(self, value, inplace=False):
        return value


class ScaleConverter(Converter):
    """A linear transformation."""

    def __init__(self, scale):
        self.scale = scale

    def to_reference(self, value, inplace=False):
        if inplace:
            value *= self.scale
        else:
            value = value * self.scale

        return value

    def from_reference(self, value, inplace=False):
        if inplace:
            value /= self.scale
        else:
            value = value / self.scale

        return value


class OffsetConverter(Converter):
    """An affine transformation."""

    def __init__(self, scale, offset):
        self.scale = scale
        self.offset = offset

    @property
    def is_multiplicative(self):
        return self.offset == 0

    def to_reference(self, value, inplace=False):
        if inplace:
            value *= self.scale
            value += self.offset
        else:
            value = value * self.scale + self.offset

        return value

    def from_reference(self, value, inplace=False):
        if inplace:
            value -= self.offset
            value /= self.scale
        else:
            value = (value - self.offset) / self.scale

        return value


class LogarithmicConverter(Converter):
    """ Converts between linear units and logarithmic units, such as dB, octave, neper or pH.
    Q_log = logfactor * log( Q_lin / scale ) / log(log_base)

    Parameters
    ----------
    scale : float
        unit of reference at denominator for logarithmic unit conversion
    logbase : float
        base of logarithm used in the logarithmic unit conversion
    logfactor : float
        factor multupled to logarithm for unit conversion
    inplace : bool
        controls if computation is done in place
    """

    def __init__(self, scale, logbase, logfactor):
        """
        Parameters
        ----------
        scale : float
            unit of reference at denominator inside logarithm for unit conversion
        logbase: float
            base of logarithm used in unit conversion
        logfactor: float
            factor multiplied to logarithm for unit conversion
        """

        self.scale = scale
        self.logbase = logbase
        self.logfactor = logfactor

    @property
    def is_multiplicative(self):
        return False

    @property
    def is_logarithmic(self):
        return True

    def from_reference(self, value, inplace=False):
        """Converts value from the reference unit to the logarithmic unit

            dBm   <------   mW
            y dBm = 10 log10( x / 1mW )
        """
        if inplace:
            value /= self.scale
            if HAS_NUMPY:
                log(value, value)
            else:
                value = log(value)
            value *= self.logfactor / log(self.logbase)
        else:
            value = self.logfactor * log(value / self.scale) / log(self.logbase)

        return value

    def to_reference(self, value, inplace=False):
        """Converts value to the reference unit from the logarithmic unit

            dBm   ------>   mW
            y dBm = 10 log10( x / 1mW )
        """
        if inplace:
            value /= self.logfactor
            value *= log(self.logbase)
            if HAS_NUMPY:
                exp(value, value)
            else:
                value = exp(value)
            value *= self.scale
        else:
            value = self.scale * exp(log(self.logbase) * (value / self.logfactor))

        return value
