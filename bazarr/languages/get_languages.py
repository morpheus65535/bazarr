# coding=utf-8

import pycountry

from subzero.language import Language

from .custom_lang import CustomLanguage
from app.database import TableSettingsLanguages, database, rows_as_list_of_dicts, insert, update


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [{'code3': lang.alpha_3, 'code2': lang.alpha_2, 'name': lang.name, 'enabled': 0}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]

    # Insert standard languages in database table
    database.execute(insert(TableSettingsLanguages).values(langs).on_conflict_do_nothing())
    database.commit()

    # Update standard languages with code3b if available
    langs = [{'code3b': lang.bibliographic, 'code3': lang.alpha_3}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]

    # Update languages in database table
    database.execute(update(TableSettingsLanguages), langs)
    database.commit()

    # Insert custom languages in database table
    CustomLanguage.register(TableSettingsLanguages)

    # Create languages dictionary for faster conversion than calling database
    create_languages_dict()


def create_languages_dict():
    global languages_dict
    # replace chinese by chinese simplified
    database.execute(update(TableSettingsLanguages).values(name='Chinese Simplified')
                     .where(TableSettingsLanguages.code3 == 'zho'))
    database.commit()

    languages_dict = rows_as_list_of_dicts(database.query(TableSettingsLanguages.code3, TableSettingsLanguages.code2,
                                                          TableSettingsLanguages.name, TableSettingsLanguages.code3b))


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
    languages = database.query(TableSettingsLanguages.code3).where(TableSettingsLanguages.enabled == 1)

    language_set = set()

    for lang in languages:
        custom = CustomLanguage.from_value(lang.code3, "alpha3")
        if custom is None:
            language_set.add(Language(lang.code3))
        else:
            language_set.add(custom.subzero_language())

    return language_set
