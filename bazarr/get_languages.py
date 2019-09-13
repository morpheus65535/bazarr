# coding=utf-8

from __future__ import absolute_import
import os
import pycountry

from get_args import args
from subzero.language import Language
from database import TableSettingsLanguages


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [{'code3': lang.alpha_3, 'code2': lang.alpha_2, 'name': lang.name}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]
    
    # Insert languages in database table
    for lang in langs:
        TableSettingsLanguages.insert(
            lang
        ).on_conflict_ignore().execute()

    TableSettingsLanguages.insert(
        {
            TableSettingsLanguages.code3: 'pob',
            TableSettingsLanguages.code2: 'pb',
            TableSettingsLanguages.name: 'Brazilian Portuguese'
        }
    ).on_conflict_ignore().execute()

    langs = [{'code3b': lang.bibliographic, 'code3': lang.alpha_3}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]
    
    # Update languages in database table
    for lang in langs:
        TableSettingsLanguages.update(
            {
                TableSettingsLanguages.code3b: lang['code3b']
            }
        ).where(
            TableSettingsLanguages.code3 == lang['code3']
        ).execute()


def language_from_alpha2(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.name
    ).where(
        TableSettingsLanguages.code2 == lang
    ).first()
    return result.name


def language_from_alpha3(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.name
    ).where(
        (TableSettingsLanguages.code3 == lang) |
        (TableSettingsLanguages.code3b == lang)
    ).first()
    return result.name


def alpha2_from_alpha3(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.code2
    ).where(
        (TableSettingsLanguages.code3 == lang) |
        (TableSettingsLanguages.code3b == lang)
    ).first()
    return result.code2


def alpha2_from_language(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.code2
    ).where(
        TableSettingsLanguages.name == lang
    ).first()
    return result.code2


def alpha3_from_alpha2(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.code3
    ).where(
        TableSettingsLanguages.code2 == lang
    ).first()
    return result.code3


def alpha3_from_language(lang):
    result = TableSettingsLanguages.select(
        TableSettingsLanguages.code3
    ).where(
        TableSettingsLanguages.name == lang
    ).first()
    return result.code3


def get_language_set():
    languages = TableSettingsLanguages.select(
        TableSettingsLanguages.code3
    ).where(
        TableSettingsLanguages.enabled == 1
    )

    language_set = set()
    
    for lang in languages:
        if lang.code3 == 'pob':
            language_set.add(Language('por', 'BR'))
        else:
            language_set.add(Language(lang.code3))
    
    return language_set


if __name__ == '__main__':
    load_language_in_db()
