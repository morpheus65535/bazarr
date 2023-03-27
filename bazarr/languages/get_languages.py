# coding=utf-8

import pycountry

from subzero.language import Language
from sqlalchemy import insert, update

from .custom_lang import CustomLanguage
from app.database import TableSettingsLanguages, database


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [{'code3': lang.alpha_3, 'code2': lang.alpha_2, 'name': lang.name}
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]

    # Insert standard languages in database table
    stmt = insert(TableSettingsLanguages).values(langs)
    stmt = stmt.on_conflict_do_nothing()
    database.execute(stmt)
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
    TableSettingsLanguages.update({TableSettingsLanguages.name: 'Chinese Simplified'}) \
        .where(TableSettingsLanguages.code3 == 'zho') \
        .execute()

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
        custom = CustomLanguage.from_value(lang["code3"], "alpha3")
        if custom is None:
            language_set.add(Language(lang["code3"]))
        else:
            language_set.add(custom.subzero_language())

    return language_set
