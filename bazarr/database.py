# coding=utf-8

import os
import ast
import sqlite3
import logging
import json

from sqlite3worker import Sqlite3Worker

from get_args import args
from helper import path_mappings
from config import settings, get_array_from

global profile_id_list
profile_id_list = []


def db_init():
    if not os.path.exists(os.path.join(args.config_dir, 'db', 'bazarr.db')):
        # Get SQL script from file
        fd = open(os.path.join(os.path.dirname(__file__), 'create_db.sql'), 'r')
        script = fd.read()
        # Close SQL script file
        fd.close()
        # Open database connection
        db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c = db.cursor()
        # Execute script and commit change to database
        c.executescript(script)
        # Close database connection
        db.close()
        logging.info('BAZARR Database created successfully')


database = Sqlite3Worker(os.path.join(args.config_dir, 'db', 'bazarr.db'), max_queue_size=256, as_dict=True)


class SqliteDictConverter:
    def __init__(self):
        self.keys_insert = tuple()
        self.keys_update = tuple()
        self.values = tuple()
        self.question_marks = tuple()

    def convert(self, values_dict):
        if type(values_dict) is dict:
            self.keys_insert = tuple()
            self.keys_update = tuple()
            self.values = tuple()
            self.question_marks = tuple()

            temp_keys = list()
            temp_values = list()
            for item in values_dict.items():
                temp_keys.append(item[0])
                temp_values.append(item[1])
            self.keys_insert = ','.join(temp_keys)
            self.keys_update = ','.join([k + '=?' for k in temp_keys])
            self.values = tuple(temp_values)
            self.question_marks = ','.join(list('?'*len(values_dict)))
            return self
        else:
            pass


dict_converter = SqliteDictConverter()


class SqliteDictPathMapper:
    def __init__(self):
        pass

    def path_replace(self, values_dict):
        if type(values_dict) is list:
            for item in values_dict:
                item['path'] = path_mappings.path_replace(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_mappings.path_replace(values_dict['path'])
        else:
            return path_mappings.path_replace(values_dict)

    def path_replace_movie(self, values_dict):
        if type(values_dict) is list:
            for item in values_dict:
                item['path'] = path_mappings.path_replace_movie(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_mappings.path_replace_movie(values_dict['path'])
        else:
            return path_mappings.path_replace_movie(values_dict)


dict_mapper = SqliteDictPathMapper()


def db_upgrade():
    columnToAdd = [
        ['table_shows', 'year', 'text'],
        ['table_shows', 'alternateTitles', 'text'],
        ['table_shows', 'forced', 'text', 'False'],
        ['table_shows', 'tags', 'text', '[]'],
        ['table_shows', 'seriesType', 'text', ''],
        ['table_shows', 'imdbId', 'text', ''],
        ['table_shows', 'profileId', 'integer'],
        ['table_episodes', 'format', 'text'],
        ['table_episodes', 'resolution', 'text'],
        ['table_episodes', 'video_codec', 'text'],
        ['table_episodes', 'audio_codec', 'text'],
        ['table_episodes', 'episode_file_id', 'integer'],
        ['table_episodes', 'audio_language', 'text'],
        ['table_movies', 'sortTitle', 'text'],
        ['table_movies', 'year', 'text'],
        ['table_movies', 'alternativeTitles', 'text'],
        ['table_movies', 'format', 'text'],
        ['table_movies', 'resolution', 'text'],
        ['table_movies', 'video_codec', 'text'],
        ['table_movies', 'audio_codec', 'text'],
        ['table_movies', 'imdbId', 'text'],
        ['table_movies', 'forced', 'text', 'False'],
        ['table_movies', 'movie_file_id', 'integer'],
        ['table_movies', 'tags', 'text', '[]'],
        ['table_movies', 'profileId', 'integer'],
        ['table_history', 'video_path', 'text'],
        ['table_history', 'language', 'text'],
        ['table_history', 'provider', 'text'],
        ['table_history', 'score', 'text'],
        ['table_history', 'subs_id', 'text'],
        ['table_history', 'subtitles_path', 'text'],
        ['table_history_movie', 'video_path', 'text'],
        ['table_history_movie', 'language', 'text'],
        ['table_history_movie', 'provider', 'text'],
        ['table_history_movie', 'score', 'text'],
        ['table_history_movie', 'subs_id', 'text'],
        ['table_history_movie', 'subtitles_path', 'text']
    ]

    for column in columnToAdd:
        try:
            # Check if column already exist in table
            columns_dict = database.execute('''PRAGMA table_info('{0}')'''.format(column[0]))
            columns_names_list = [x['name'] for x in columns_dict]
            if column[1] in columns_names_list:
                continue

            # Creating the missing column
            if len(column) == 3:
                database.execute('''ALTER TABLE {0} ADD COLUMN "{1}" "{2}"'''.format(column[0], column[1], column[2]))
            else:
                database.execute('''ALTER TABLE {0} ADD COLUMN "{1}" "{2}" DEFAULT "{3}"'''.format(column[0], column[1], column[2], column[3]))
            logging.debug('BAZARR Database upgrade process added column {0} to table {1}.'.format(column[1], column[0]))
        except:
            pass

    # Create blacklist tables
    database.execute("CREATE TABLE IF NOT EXISTS table_blacklist (sonarr_series_id integer, sonarr_episode_id integer, "
                     "timestamp integer, provider text, subs_id text, language text)")
    database.execute("CREATE TABLE IF NOT EXISTS table_blacklist_movie (radarr_id integer, timestamp integer, "
                     "provider text, subs_id text, language text)")

    # Create languages profiles table and populate it
    lang_table_content = database.execute("SELECT * FROM table_languages_profiles")
    if isinstance(lang_table_content, list):
        lang_table_exist = True
    else:
        lang_table_exist = False
        database.execute("CREATE TABLE IF NOT EXISTS table_languages_profiles ("
                         "profileId INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL, "
                         "cutoff INTEGER, items TEXT NOT NULL)")

    if not lang_table_exist:
        series_default = []
        try:
            for language in ast.literal_eval(settings.general.serie_default_language):
                if settings.general.serie_default_forced == 'Both':
                    series_default.append([language, 'True', settings.general.serie_default_hi])
                    series_default.append([language, 'False', settings.general.serie_default_hi])
                else:
                    series_default.append([language, settings.general.serie_default_forced,
                                           settings.general.serie_default_hi])
        except ValueError:
            pass

        movies_default = []
        try:
            for language in ast.literal_eval(settings.general.movie_default_language):
                if settings.general.movie_default_forced == 'Both':
                    movies_default.append([language, 'True', settings.general.movie_default_hi])
                    movies_default.append([language, 'False', settings.general.movie_default_hi])
                else:
                    movies_default.append([language, settings.general.movie_default_forced,
                                           settings.general.movie_default_hi])
        except ValueError:
            pass

        profiles_to_create = database.execute("SELECT DISTINCT languages, hearing_impaired, forced "
                                              "FROM (SELECT languages, hearing_impaired, forced FROM table_shows "
                                              "UNION ALL SELECT languages, hearing_impaired, forced FROM table_movies) "
                                              "a WHERE languages NOT null and languages NOT IN ('None', '[]')")

        for profile in profiles_to_create:
            profile_items = []
            languages_list = ast.literal_eval(profile['languages'])
            for i, language in enumerate(languages_list, 1):
                if profile['forced'] == 'Both':
                    profile_items.append({'id': i, 'language': language, 'forced': 'True',
                                          'hi': profile['hearing_impaired'], 'audio_exclude': 'False'})
                    profile_items.append({'id': i, 'language': language, 'forced': 'False',
                                          'hi': profile['hearing_impaired'], 'audio_exclude': 'False'})
                else:
                    profile_items.append({'id': i, 'language': language, 'forced': profile['forced'],
                                          'hi': profile['hearing_impaired'], 'audio_exclude': 'False'})

            # Create profiles
            new_profile_name = profile['languages'] + ' (' + profile['hearing_impaired'] + '/' + profile['forced'] + ')'
            database.execute("INSERT INTO table_languages_profiles (name, cutoff, items) VALUES("
                             "?,null,?)", (new_profile_name, json.dumps(profile_items),))
            created_profile_id = database.execute("SELECT profileId FROM table_languages_profiles WHERE name = ?",
                                                  (new_profile_name,), only_one=True)['profileId']
            # Assign profiles to series and movies
            database.execute("UPDATE table_shows SET profileId = ? WHERE languages = ? AND hearing_impaired = ? AND "
                             "forced = ?", (created_profile_id, profile['languages'], profile['hearing_impaired'],
                                            profile['forced']))
            database.execute("UPDATE table_movies SET profileId = ? WHERE languages = ? AND hearing_impaired = ? AND "
                             "forced = ?", (created_profile_id, profile['languages'], profile['hearing_impaired'],
                                            profile['forced']))

            # Save new defaults
            profile_items_list = []
            for item in profile_items:
                profile_items_list.append([item['language'], item['forced'], item['hi']])
            try:
                if created_profile_id and profile_items_list == series_default:
                    settings.general.serie_default_profile = str(created_profile_id)
            except:
                pass

            try:
                if created_profile_id and profile_items_list == movies_default:
                    settings.general.movie_default_profile = str(created_profile_id)
            except:
                pass

        # null languages, forced and hearing_impaired for all series and movies
        database.execute("UPDATE table_shows SET languages = null, forced = null, hearing_impaired = null")
        database.execute("UPDATE table_movies SET languages = null, forced = null, hearing_impaired = null")

        # Force series, episodes and movies sync with Sonarr to get all the audio track from video files
        # Set environment variable that is going to be use during the init process to run sync once Bazarr is ready.
        os.environ['BAZARR_AUDIO_PROFILES_MIGRATION'] = '1'


def get_exclusion_clause(type):
    where_clause = ''
    if type == 'series':
        tagsList = ast.literal_eval(settings.sonarr.excluded_tags)
        for tag in tagsList:
            where_clause += ' AND table_shows.tags NOT LIKE "%\'' + tag + '\'%"'
    else:
        tagsList = ast.literal_eval(settings.radarr.excluded_tags)
        for tag in tagsList:
            where_clause += ' AND table_movies.tags NOT LIKE "%\'' + tag + '\'%"'

    if type == 'series':
        monitoredOnly = settings.sonarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause += ' AND table_episodes.monitored = "True"'
    else:
        monitoredOnly = settings.radarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause += ' AND table_movies.monitored = "True"'

    if type == 'series':
        typesList = get_array_from(settings.sonarr.excluded_series_types)
        for type in typesList:
            where_clause += ' AND table_shows.seriesType != "' + type + '"'

    return where_clause


def update_profile_id_list():
    global profile_id_list
    profile_id_list = database.execute("SELECT profileId, name, cutoff, items FROM table_languages_profiles")

    for profile in profile_id_list:
            profile['items'] = json.loads(profile['items'])


def get_profiles_list(profile_id=None):
    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id:
        for profile in profile_id_list:
            if profile['profileId'] == profile_id:
                return profile
    else:
        return profile_id_list


def get_desired_languages(profile_id):
    languages = []

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id:
        for profile in profile_id_list:
            profileId, name, cutoff, items = profile.values()
            if profileId == int(profile_id):
                languages = [x['language'] for x in items]
                break

    return languages


def get_profile_id_name(profile_id):
    name_from_id = None

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id:
        for profile in profile_id_list:
            profileId, name, cutoff, items = profile.values()
            if profileId == int(profile_id):
                name_from_id = name
                break

    return name_from_id


def get_profile_cutoff(profile_id):
    cutoff_language = None

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id:
        cutoff_language = []
        for profile in profile_id_list:
            profileId, name, cutoff, items = profile.values()
            if cutoff:
                if profileId == int(profile_id):
                    for item in items:
                        if item['id'] == cutoff:
                            return [item]
                        elif cutoff == 65535:
                            cutoff_language.append(item)

        if not len(cutoff_language):
            cutoff_language = None

    return cutoff_language


def get_audio_profile_languages(series_id=None, episode_id=None, movie_id=None):
    from get_languages import alpha2_from_language, alpha3_from_language
    audio_languages = []

    if series_id:
        audio_languages_list_str = database.execute("SELECT audio_language FROM table_shows WHERE sonarrSeriesId=?",
                                                    (series_id,), only_one=True)['audio_language']
        try:
            audio_languages_list = ast.literal_eval(audio_languages_list_str)
        except ValueError:
            pass
        else:
            for language in audio_languages_list:
                audio_languages.append(
                    {"name": language,
                     "code2": alpha2_from_language(language) or None,
                     "code3": alpha3_from_language(language) or None}
                )
    elif episode_id:
        audio_languages_list_str = database.execute("SELECT audio_language FROM table_episodes WHERE sonarrEpisodeId=?",
                                                    (episode_id,), only_one=True)['audio_language']
        try:
            audio_languages_list = ast.literal_eval(audio_languages_list_str)
        except ValueError:
            pass
        else:
            for language in audio_languages_list:
                audio_languages.append(
                    {"name": language,
                     "code2": alpha2_from_language(language) or None,
                     "code3": alpha3_from_language(language) or None}
                )
    elif movie_id:
        audio_languages_list_str = database.execute("SELECT audio_language FROM table_movies WHERE radarrId=?",
                                                    (movie_id,), only_one=True)['audio_language']
        try:
            audio_languages_list = ast.literal_eval(audio_languages_list_str)
        except ValueError:
            pass
        else:
            for language in audio_languages_list:
                audio_languages.append(
                    {"name": language,
                     "code2": alpha2_from_language(language) or None,
                     "code3": alpha3_from_language(language) or None}
                )

    return audio_languages
