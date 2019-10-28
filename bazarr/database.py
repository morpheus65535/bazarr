import os
from sqlite3worker import Sqlite3Worker
from six import string_types

from get_args import args
from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = Sqlite3Worker(os.path.join(args.config_dir, 'db', 'bazarr.db'), max_queue_size=256, as_dict=True)


class SqliteDictConverter:
    def __init__(self):
        self.keys_insert = tuple()
        self.keys_update = tuple()
        self.values = tuple()
        self.question_marks = tuple()

    def convert(self, values_dict):
        if type(values_dict) is dict:
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
                item['path'] = path_replace(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_replace(values_dict['path'])
        else:
            return path_replace(values_dict)

    def path_replace_movie(self, values_dict):
        if type(values_dict) is list:
            for item in values_dict:
                item['path'] = path_replace_movie(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_replace_movie(values_dict['path'])
        else:
            return path_replace(values_dict)


dict_mapper = SqliteDictPathMapper()