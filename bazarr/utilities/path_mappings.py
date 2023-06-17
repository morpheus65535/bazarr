# coding=utf-8

import re

from app.config import settings


class PathMappings:
    def __init__(self):
        self.path_mapping_series = []
        self.path_mapping_movies = []

    def update(self):
        self.path_mapping_series = [x for x in settings.general.path_mappings if x[0] != x[1]]
        self.path_mapping_movies = [x for x in settings.general.path_mappings_movie if x[0] != x[1]]

    def path_replace(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_series:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[0] in path:
                path = path.replace(path_mapping[0], path_mapping[1])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_reverse(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_series:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[1] in path:
                path = path.replace(path_mapping[1], path_mapping[0])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_movie(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_movies:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[0] in path:
                path = path.replace(path_mapping[0], path_mapping[1])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_reverse_movie(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_movies:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[1] in path:
                path = path.replace(path_mapping[1], path_mapping[0])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path


path_mappings = PathMappings()
