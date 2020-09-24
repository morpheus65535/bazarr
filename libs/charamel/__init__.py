"""
🌏 Charamel: Truly Universal Encoding Detection in Python 🌎
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usage:
    >>> import charamel
    >>> detector = charamel.Detector()
    >>> content = b'El espa\xf1ol o castellano del lat\xedn hablado'
    >>> encoding = detector.detect(content)
    >>> encoding
    <Encoding.ISO_8859_14: 'iso8859_14'>
    >>> content.decode(encoding)
    'El español o castellano del latín hablado'

Licensed under Apache 2.0
"""
from .detector import Detector  # noqa: F401
from .encoding import Encoding  # noqa: F401

__version__ = '1.0.0'
