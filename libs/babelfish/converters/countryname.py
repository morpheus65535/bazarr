# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
from . import CountryReverseConverter, CaseInsensitiveDict
from ..country import COUNTRY_MATRIX
from ..exceptions import CountryConvertError, CountryReverseError


class CountryNameConverter(CountryReverseConverter):
    def __init__(self):
        self.codes = set()
        self.to_name = {}
        self.from_name = CaseInsensitiveDict()
        for country in COUNTRY_MATRIX:
            self.codes.add(country.name)
            self.to_name[country.alpha2] = country.name
            self.from_name[country.name] = country.alpha2

    def convert(self, alpha2):
        if alpha2 not in self.to_name:
            raise CountryConvertError(alpha2)
        return self.to_name[alpha2]

    def reverse(self, name):
        if name not in self.from_name:
            raise CountryReverseError(name)
        return self.from_name[name]
