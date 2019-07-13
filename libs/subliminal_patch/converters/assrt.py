# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

class AssrtConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_assrt = { u'简体': ('zho', None, 'Hans'), u'繁体': ('zho', None, 'Hant'),
                            u'簡體': ('zho', None, 'Hans'), u'繁體': ('zho', None, 'Hant'),
                            u'英文': ('eng',),
                            u'chs': ('zho', None, 'Hans'), u'cht': ('zho', None, 'Hant'),
                            u'chn': ('zho', None, 'Hans'), u'twn': ('zho', None, 'Hant')}
        self.to_assrt = { ('zho', None, 'Hans'): u'chs', ('zho', None, 'Hant'): u'cht', ('eng',) : u'eng',
                          ('zho',): u'chs'}
        self.codes = set(self.from_assrt.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_assrt:
            return self.to_assrt[(alpha3, country, script)]

        raise ConfigurationError('Unsupported language for assrt: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, assrt):
        if assrt in self.from_assrt:
            return self.from_assrt[assrt]

        raise ConfigurationError('Unsupported language code for assrt: %s' % assrt)
