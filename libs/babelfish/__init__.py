# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
__title__ = 'babelfish'
__version__ = '0.5.5-dev'
__author__ = 'Antoine Bertin'
__license__ = 'BSD'
__copyright__ = 'Copyright 2015 the BabelFish authors'

import sys

if sys.version_info[0] >= 3:
    basestr = str
else:
    basestr = basestring

from .converters import (LanguageConverter, LanguageReverseConverter, LanguageEquivalenceConverter, CountryConverter,
    CountryReverseConverter)
from .country import country_converters, COUNTRIES, COUNTRY_MATRIX, Country
from .exceptions import Error, LanguageConvertError, LanguageReverseError, CountryConvertError, CountryReverseError
from .language import language_converters, LANGUAGES, LANGUAGE_MATRIX, Language
from .script import SCRIPTS, SCRIPT_MATRIX, Script
