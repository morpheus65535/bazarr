"""Top-level package for Deep Translator"""

from .google_trans import GoogleTranslator
from .pons import PonsTranslator
from .linguee import LingueeTranslator
from .mymemory import MyMemoryTranslator
from .yandex import YandexTranslator
from .qcri import QCRI
from .deepl import DeepL
from .detection import single_detection, batch_detection
from .microsoft import MicrosoftTranslator
from .papago import PapagoTranslator
from .libre import LibreTranslator

__author__ = """Nidhal Baccouri"""
__email__ = 'nidhalbacc@gmail.com'
__version__ = '1.6.1'

__all__ = [
    "GoogleTranslator",
    "PonsTranslator",
    "LingueeTranslator",
    "MyMemoryTranslator",
    "YandexTranslator",
    "MicrosoftTranslator",
    "QCRI",
    "DeepL",
    "LibreTranslator",
    "PapagoTranslator",
    "single_detection",
    "batch_detection"
    ]
