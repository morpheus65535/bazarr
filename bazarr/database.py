import os
from sqlite3worker import Sqlite3Worker
from six import string_types

from get_args import args
from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = Sqlite3Worker(os.path.join(args.config_dir, 'db', 'bazarr.db'), max_queue_size=256, as_dict=True)


class SqliteDictConverter:
    def __init__(self):
        pass

    def convert(self, values_dict):
        self.keys = str()
        self.values = str()
        self.items = str()

        if type(values_dict) is dict:
            for key, value in values_dict.items():
                self.keys += key + ", "
                if type(value) is not string_types:
                    value = str(value)
                else:
                    value = "\"" + value + "\""
                self.values += value + ", "
                self.items += key + "=" + value + ", "
            self.keys = self.keys.rstrip(", ")
            self.values = self.values.rstrip(", ")
            self.items = self.items.rstrip(", ")
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