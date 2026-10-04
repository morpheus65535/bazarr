# -*- coding: utf-8 -*-
from __future__ import absolute_import
from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError


class SubhdConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_subhd = {
            '简体': ('zho', 'CN', None),
            '繁体': ('zho', 'TW', None),
            '簡體': ('zho', 'CN', None),
            '繁體': ('zho', 'TW', None),
            '双语': ('zho', 'CN', None),
            '双语繁体': ('zho', 'TW', None),
            '英语': ('eng',),
            '英文': ('eng',),
            'chs': ('zho', 'CN', None),
            'cht': ('zho', 'TW', None),
            'chn': ('zho', 'CN', None),
            'twn': ('zho', 'TW', None),
        }
        self.to_subhd = {
            ('zho', 'CN', None): 'chs',
            ('zho', 'TW', None): 'cht',
            ('zho', 'HK', None): 'cht',
            ('zho', None, None): 'chs',
            ('eng', None, None): 'eng',
        }
        self.codes = set(self.from_subhd.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subhd:
            return self.to_subhd[(alpha3, country, script)]
        if (alpha3, None, None) in self.to_subhd:
            return self.to_subhd[(alpha3, None, None)]
        raise ConfigurationError('Unsupported language for subhd: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, subhd):
        if subhd in self.from_subhd:
            return self.from_subhd[subhd]
        raise ConfigurationError('Unsupported language code for subhd: %s' % subhd)
