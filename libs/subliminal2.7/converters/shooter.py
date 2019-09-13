# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter

from ..exceptions import ConfigurationError


class ShooterConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_shooter = {'chn': ('zho',), 'eng': ('eng',)}
        self.to_shooter = {v: k for k, v in self.from_shooter.items()}
        self.codes = set(self.from_shooter.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3,) in self.to_shooter:
            return self.to_shooter[(alpha3,)]

        raise ConfigurationError('Unsupported language for shooter: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, shooter):
        if shooter in self.from_shooter:
            return self.from_shooter[shooter]

        raise ConfigurationError('Unsupported language code for shooter: %s' % shooter)
