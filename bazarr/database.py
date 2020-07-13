import os
import ast
import sqlite3
import logging

from sqlite3worker import Sqlite3Worker

from get_args import args
from helper import path_mappings
from config import settings


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
        ['table_episodes', 'format', 'text'],
        ['table_episodes', 'resolution', 'text'],
        ['table_episodes', 'video_codec', 'text'],
        ['table_episodes', 'audio_codec', 'text'],
        ['table_episodes', 'episode_file_id', 'integer'],
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
        ['table_history', 'video_path', 'text'],
        ['table_history', 'language', 'text'],
        ['table_history', 'provider', 'text'],
        ['table_history', 'score', 'text'],
        ['table_history_movie', 'video_path', 'text'],
        ['table_history_movie', 'language', 'text'],
        ['table_history_movie', 'provider', 'text'],
        ['table_history_movie', 'score', 'text']
    ]

    for column in columnToAdd:
        try:
            if len(column) == 3:
                database.execute('''ALTER TABLE {0} ADD COLUMN "{1}" "{2}"'''.format(column[0], column[1], column[2]))
            else:
                database.execute('''ALTER TABLE {0} ADD COLUMN "{1}" "{2}" DEFAULT "{3}"'''.format(column[0], column[1], column[2], column[3]))
        except:
            pass

    # Fix null languages, hearing-impaired and forced for series and movies.
    database.execute("UPDATE table_shows SET languages = '[]' WHERE languages is null")
    database.execute("UPDATE table_shows SET hearing_impaired = 'False' WHERE hearing_impaired is null")
    database.execute("UPDATE table_shows SET forced = 'False' WHERE forced is null")
    database.execute("UPDATE table_movies SET languages = '[]' WHERE languages is null")
    database.execute("UPDATE table_movies SET hearing_impaired = 'False' WHERE hearing_impaired is null")
    database.execute("UPDATE table_movies SET forced = 'False' WHERE forced is null")


def filter_exclusions(dicts_list, type):
    if type == 'series':
        tagsList = ast.literal_eval(settings.sonarr.excluded_tags)
        monitoredOnly = settings.sonarr.getboolean('only_monitored')
    else:
        tagsList = ast.literal_eval(settings.radarr.excluded_tags)
        monitoredOnly = settings.radarr.getboolean('only_monitored')

    # Filter tags
    dictsList_tags_filtered = [item for item in dicts_list if set(tagsList).isdisjoint(ast.literal_eval(item['tags']))]

    # Filter monitored
    if monitoredOnly:
        dictsList_monitored_filtered = [item for item in dictsList_tags_filtered if item['monitored'] == 'True']
    else:
        dictsList_monitored_filtered = dictsList_tags_filtered

    # Filter series type
    if type == 'series':
        dictsList_types_filtered = [item for item in dictsList_monitored_filtered if item['seriesType'] not in
                                    ast.literal_eval(settings.sonarr.excluded_series_types)]
    else:
        dictsList_types_filtered = dictsList_monitored_filtered

    return dictsList_types_filtered
