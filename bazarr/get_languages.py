# coding=utf-8

import pycountry

from subzero.language import Language
from database import database
from custom_lang import CustomLanguage

def load_language_in_db():
    # Get languages list in langs tuple
    langs = [[lang.alpha_3, lang.alpha_2, lang.name]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]
    
    # Insert languages in database table
    database.execute("INSERT OR IGNORE INTO table_settings_languages (code3, code2, name) VALUES (?, ?, ?)",
                     langs, execute_many=True)
    
    CustomLanguage.register(database)

    langs = [[lang.bibliographic, lang.alpha_3]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]
    
    # Update languages in database table
    database.execute("UPDATE table_settings_languages SET code3b=? WHERE code3=?", langs, execute_many=True)

    # Create languages dictionary for faster conversion than calling database
    create_languages_dict()


def create_languages_dict():
    global languages_dict
    #replace chinese by chinese simplified
    database.execute("UPDATE table_settings_languages SET name = 'Chinese Simplified' WHERE code3 = 'zho'")
    
    languages_dict = database.execute("SELECT name, code2, code3, code3b FROM table_settings_languages")


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
    languages = database.execute("SELECT code3 FROM table_settings_languages WHERE enabled=1")

    language_set = set()

    for lang in languages:
        custom = CustomLanguage.from_value(lang["code3"], "alpha3")
        if custom is None:
            language_set.add(Language(lang["code3"]))
        else:
            language_set.add(custom.subzero_language())

    return language_set


if __name__ == '__main__':
    load_language_in_db()
