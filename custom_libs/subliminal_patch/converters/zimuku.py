# -*- coding: utf-8 -*-
from __future__ import absolute_import
from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

class zimukuConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_zimuku = { u'简体': ('zho', 'CN', None), u'繁体': ('zho', 'TW', None),
                            u'簡體': ('zho', 'CN', None), u'繁體': ('zho', 'TW', None),
                            u'英文': ('eng',),
                            u'chs': ('zho', 'CN', None), u'cht': ('zho', 'TW', None),
                            u'chn': ('zho', 'CN', None), u'twn': ('zho', 'TW', None)}
        self.to_zimuku = { ('zho', 'CN', None): u'chs', ('zho', 'TW', None): u'cht',
                         ('eng', None, None) : u'eng', ('zho', None, None): u'chs'}
        self.codes = set(self.from_zimuku.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_zimuku:
            return self.to_zimuku[(alpha3, country, script)]

        raise ConfigurationError('Unsupported language for zimuku: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, zimuku):
        if zimuku in self.from_zimuku:
            return self.from_zimuku[zimuku]

        raise ConfigurationError('Unsupported language code for zimuku: %s' % zimuku)