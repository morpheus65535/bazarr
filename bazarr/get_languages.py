# coding=utf-8

import pycountry

from subzero.language import Language
from database import database, TableSettingsLanguages


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [[lang.alpha_3, lang.alpha_2, lang.name]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]
    
    # Insert languages in database table
    TableSettingsLanguages.insert_many(langs,
                                       fields=[TableSettingsLanguages.code3, TableSettingsLanguages.code2,
                                               TableSettingsLanguages.name]) \
        .on_conflict(action='IGNORE') \
        .execute()

    TableSettingsLanguages.insert({TableSettingsLanguages.code3: 'pob', TableSettingsLanguages.code2: 'pb',
                                   TableSettingsLanguages.name: 'Brazilian Portuguese'}) \
        .on_conflict(action='IGNORE') \
        .execute()

    # update/insert chinese languages
    TableSettingsLanguages.update({TableSettingsLanguages.name: 'Chinese Simplified'}) \
        .where(TableSettingsLanguages.code2 == 'zt')\
        .execute()
    TableSettingsLanguages.insert({TableSettingsLanguages.code3: 'zht', TableSettingsLanguages.code2: 'zt',
                                   TableSettingsLanguages.name: 'Chinese Traditional'}) \
        .on_conflict(action='IGNORE')\
        .execute()

    langs = [[lang.bibliographic, lang.alpha_3]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]
    
    # Update languages in database table
    for lang in langs:
        TableSettingsLanguages.update({TableSettingsLanguages.code3b: lang[0]}) \
            .where(TableSettingsLanguages.code3 == lang[1]) \
            .execute()

    # Create languages dictionary for faster conversion than calling database
    create_languages_dict()


def create_languages_dict():
    global languages_dict
    languages_dict = TableSettingsLanguages.select(TableSettingsLanguages.name,
                                                   TableSettingsLanguages.code2,
                                                   TableSettingsLanguages.code3,
                                                   TableSettingsLanguages.code3b).dicts()


def language_from_alpha2(lang):
    return next((item["name"] for item in languages_dict if item["code2"] == lang[:2]), None)


def language_from_alpha3(lang):
    return next((item["name"] for item in languages_dict if item["code3"] == lang[:3] or item["code3b"] == lang[:3]),
                None)


def alpha2_from_alpha3(lang):
    return next((item["code2"] for item in languages_dict if item["code3"] == lang[:3] or item["code3b"] == lang[:3]),
                None)


def alpha2_from_language(lang):
    return next((item["code2"] for item in languages_dict if item["name"] == lang), None)


def alpha3_from_alpha2(lang):
    return next((item["code3"] for item in languages_dict if item["code2"] == lang[:2]), None)


def alpha3_from_language(lang):
    return next((item["code3"] for item in languages_dict if item["name"] == lang), None)


def get_language_set():
    languages = TableSettingsLanguages.select(TableSettingsLanguages.code3) \
        .where(TableSettingsLanguages.enabled == 1).dicts()

    language_set = set()
    
    for lang in languages:
        if lang['code3'] == 'pob':
            language_set.add(Language('por', 'BR'))
        elif lang['code3'] == 'zht':
            language_set.add(Language('zho', 'TW'))
        else:
            language_set.add(Language(lang['code3']))
    
    return language_set


if __name__ == '__main__':
    load_language_in_db()
