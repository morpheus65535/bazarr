# -*- coding: utf-8 -*-
from __future__ import absolute_import
from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

class AssrtConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_assrt = { u'简体': ('zho', 'CN', None), u'繁体': ('zho', 'TW', None),
                            u'簡體': ('zho', 'CN', None), u'繁體': ('zho', 'TW', None),
                            u'英文': ('eng',),
                            u'chs': ('zho', 'CN', None), u'cht': ('zho', 'TW', None),
                            u'chn': ('zho', 'CN', None), u'twn': ('zho', 'TW', None)}
        self.to_assrt = { ('zho', 'CN', None): u'chs', ('zho', 'TW', None): u'cht',
                         ('eng', None, None) : u'eng', ('zho', None, None): u'chs'}
        self.codes = set(self.from_assrt.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_assrt:
            return self.to_assrt[(alpha3, country, script)]

        raise ConfigurationError('Unsupported language for assrt: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, assrt):
        if assrt in self.from_assrt:
            return self.from_assrt[assrt]

        raise ConfigurationError('Unsupported language code for assrt: %s' % assrt)
