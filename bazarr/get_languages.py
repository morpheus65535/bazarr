# coding=utf-8

import pycountry
import ast

from subzero.language import Language
from database import database


def load_language_in_db():
    # Get languages list in langs tuple
    langs = [[lang.alpha_3, lang.alpha_2, lang.name]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2')]
    
    # Insert languages in database table
    database.execute("INSERT OR IGNORE INTO table_settings_languages (code3, code2, name) VALUES (?, ?, ?)",
                     langs, execute_many=True)

    database.execute("INSERT OR IGNORE INTO table_settings_languages (code3, code2, name) "
                     "VALUES ('pob', 'pb', 'Brazilian Portuguese')")

    langs = [[lang.bibliographic, lang.alpha_3]
             for lang in pycountry.languages
             if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]
    
    # Update languages in database table
    database.execute("UPDATE table_settings_languages SET code3b=? WHERE code3=?", langs, execute_many=True)

    # Create languages dictionary for faster conversion than calling database
    create_languages_dict()


def create_languages_dict():
    global languages_dict
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
        if lang['code3'] == 'pob':
            language_set.add(Language('por', 'BR'))
        else:
            language_set.add(Language(lang['code3']))
    
    return language_set


def clean_desired_languages():
    from list_subtitles import list_missing_subtitles, list_missing_subtitles_movies
    enabled_languages = []
    enabled_languages_temp = database.execute("SELECT code2 FROM table_settings_languages WHERE enabled=1")
    for language in enabled_languages_temp:
        enabled_languages.append(language['code2'])

    series_languages = database.execute("SELECT sonarrSeriesId, languages FROM table_shows")
    movies_languages = database.execute("SELECT radarrId, languages FROM table_movies")

    for item in series_languages:
        if item['languages'] != 'None':
            try:
                languages_list = ast.literal_eval(item['languages'])
            except:
                pass
            else:
                cleaned_languages_list = []
                for language in languages_list:
                    if language in enabled_languages:
                        cleaned_languages_list.append(language)
                if cleaned_languages_list != languages_list:
                    database.execute("UPDATE table_shows SET languages=? WHERE sonarrSeriesId=?",
                                     (str(cleaned_languages_list), item['sonarrSeriesId']))
                    list_missing_subtitles(no=item['sonarrSeriesId'])

    for item in movies_languages:
        if item['languages'] != 'None':
            try:
                languages_list = ast.literal_eval(item['languages'])
            except:
                pass
            else:
                cleaned_languages_list = []
                for language in languages_list:
                    if language in enabled_languages:
                        cleaned_languages_list.append(language)
                if cleaned_languages_list != languages_list:
                    database.execute("UPDATE table_movies SET languages=? WHERE radarrId=?",
                                     (str(cleaned_languages_list), item['radarrId']))
                    list_missing_subtitles_movies(no=item['radarrId'])


if __name__ == '__main__':
    load_language_in_db()
