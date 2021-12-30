# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
from . import LanguageReverseConverter, CaseInsensitiveDict
from ..exceptions import LanguageReverseError
from ..language import language_converters


class OpenSubtitlesConverter(LanguageReverseConverter):
    def __init__(self):
        self.alpha3b_converter = language_converters['alpha3b']
        self.alpha2_converter = language_converters['alpha2']
        self.to_opensubtitles = {('por', 'BR'): 'pob', ('gre', None): 'ell', ('srp', None): 'scc', ('srp', 'ME'): 'mne', ('chi', 'TW'): 'zht'}
        self.from_opensubtitles = CaseInsensitiveDict({'pob': ('por', 'BR'), 'pb': ('por', 'BR'), 'ell': ('ell', None),
                                                       'scc': ('srp', None), 'mne': ('srp', 'ME'), 'zht': ('zho', 'TW')})
        self.codes = (self.alpha2_converter.codes | self.alpha3b_converter.codes | set(self.from_opensubtitles.keys()))

    def convert(self, alpha3, country=None, script=None):
        alpha3b = self.alpha3b_converter.convert(alpha3, country, script)
        if (alpha3b, country) in self.to_opensubtitles:
            return self.to_opensubtitles[(alpha3b, country)]
        return alpha3b

    def reverse(self, opensubtitles):
        if opensubtitles in self.from_opensubtitles:
            return self.from_opensubtitles[opensubtitles]
        for conv in [self.alpha3b_converter, self.alpha2_converter]:
            try:
                return conv.reverse(opensubtitles)
            except LanguageReverseError:
                pass
        raise LanguageReverseError(opensubtitles)
