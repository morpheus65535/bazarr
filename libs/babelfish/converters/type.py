# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
from . import LanguageConverter
from ..exceptions import LanguageConvertError
from ..language import LANGUAGE_MATRIX


class LanguageTypeConverter(LanguageConverter):
    FULLNAME = {'A': 'ancient', 'C': 'constructed', 'E': 'extinct', 'H': 'historical', 'L': 'living', 'S': 'special'}
    SYMBOLS = {}
    for iso_language in LANGUAGE_MATRIX:
        SYMBOLS[iso_language.alpha3] = iso_language.type
    codes = set(SYMBOLS.values())

    def convert(self, alpha3, country=None, script=None):
        if self.SYMBOLS[alpha3] in self.FULLNAME:
            return self.FULLNAME[self.SYMBOLS[alpha3]]
        raise LanguageConvertError(alpha3, country, script)
