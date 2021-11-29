"""Top-level package for Deep Translator"""

# TODO: Discussion: Do these need to be in __init__.py? Are they intended to be exportable?
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

# TODO: Discussion: These should be declared in setup.cfg, setting them here is redundant
__author__ = """Nidhal Baccouri"""
__email__ = 'nidhalbacc@gmail.com'
__version__ = '1.5.0'

__all__ = [
    "GoogleTranslator",
    "PonsTranslator",
    "LingueeTranslator",
    "MyMemoryTranslator",
    "YandexTranslator",
    "MicrosoftTranslator",
    "QCRI",
    "DeepL",
    "single_detection",
    "batch_detection"
           ]
