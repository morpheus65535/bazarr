#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
import os.path
import tempfile
import zipfile
import requests


DATA_DIR = os.path.dirname(__file__)

# iso-3166-1.txt
print('Downloading ISO-3166-1 standard (ISO country codes)...')
with open(os.path.join(DATA_DIR, 'iso-3166-1.txt'), 'w') as f:
    r = requests.get('http://www.iso.org/iso/home/standards/country_codes/country_names_and_code_elements_txt.htm')
    f.write(r.content.strip())

# iso-639-3.tab
print('Downloading ISO-639-3 standard (ISO language codes)...')
with tempfile.TemporaryFile() as f:
    r = requests.get('http://www-01.sil.org/iso639-3/iso-639-3_Code_Tables_20130531.zip')
    f.write(r.content)
    with zipfile.ZipFile(f) as z:
        z.extract('iso-639-3.tab', DATA_DIR)

# iso-15924
print('Downloading ISO-15924 standard (ISO script codes)...')
with tempfile.TemporaryFile() as f:
    r = requests.get('http://www.unicode.org/iso15924/iso15924.txt.zip')
    f.write(r.content)
    with zipfile.ZipFile(f) as z:
        z.extract('iso15924-utf8-20131012.txt', DATA_DIR)

# opensubtitles supported languages
print('Downloading OpenSubtitles supported languages...')
with open(os.path.join(DATA_DIR, 'opensubtitles_languages.txt'), 'w') as f:
    r = requests.get('http://www.opensubtitles.org/addons/export_languages.php')
    f.write(r.content)

print('Done!')
