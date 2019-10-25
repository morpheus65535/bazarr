# coding=utf-8

import os
import pycountry

from get_args import args
from subzero.language import Language
from database import database


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [{'code3': lang.alpha_3, 'code2': lang.alpha_2, 'name': lang.name}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]
    
    # Insert languages in database table
    for lang in langs:
        database.execute("INSERT OR IGNORE INTO table_settings_languages (code3, code2, name) VALUES (?, ?, ?)",
                         (lang['code3'], lang['code2'], lang['name']))

    database.execute("INSERT OR IGNORE INTO table_settings_languages (code3, code2, name) "
                     "VALUES ('pob', 'pb', 'Brazilian Portuguese')")

    langs = [{'code3b': lang.bibliographic, 'code3': lang.alpha_3}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]
    
    # Update languages in database table
    for lang in langs:
        database.execute("UPDATE table_settings_languages SET code3b=? WHERE code3=?", (lang['code3b'], lang['code3']))


def language_from_alpha2(lang):
    result = database.execute("SELECT name FROM table_settings_languages WHERE code2=?", (lang,))
    return result[0]['name'] or None


def language_from_alpha3(lang):
    result = database.execute("SELECT name FROM table_settings_languages WHERE code3=? or code3b=?", (lang, lang))
    return result[0]['name'] or None


def alpha2_from_alpha3(lang):
    result = database.execute("SELECT code2 FROM table_settings_languages WHERE code3=? or code3b=?", (lang, lang))
    return result[0]['code2'] or None


def alpha2_from_language(lang):
    result = database.execute("SELECT code2 FROM table_settings_languages WHERE name=?", (lang,))
    return result[0]['code2'] or None


def alpha3_from_alpha2(lang):
    result = database.execute("SELECT code3 FROM table_settings_languages WHERE code2=?", (lang,))
    return result[0]['code3'] or None


def alpha3_from_language(lang):
    result = database.execute("SELECT code3 FROM table_settings_languages WHERE name=?", (lang,))
    return result[0]['code3'] or None


def get_language_set():
    languages = database.execute("SELECT code3 FROM table_settings_languages WHERE enabled=1")

    language_set = set()
    
    for lang in languages:
        if lang['code3'] == 'pob':
            language_set.add(Language('por', 'BR'))
        else:
            language_set.add(Language(lang['code3']))
    
    return language_set


if __name__ == '__main__':
    load_language_in_db()
