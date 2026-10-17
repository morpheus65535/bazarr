# coding=utf-8

import re
from typing import overload

from app.config import settings


class PathMappings:
    def __init__(self) -> None:
        self.path_mapping_series: list[list[str] | tuple[str, str]] = []
        self.path_mapping_movies: list[list[str] | tuple[str, str]] = []

    def update(self) -> None:
        self.path_mapping_series = [x for x in settings.general.path_mappings if x[0] != x[1]]
        self.path_mapping_movies = [x for x in settings.general.path_mappings_movie if x[0] != x[1]]

    @overload
    def path_replace(self, path: str) -> str: ...

    @overload
    def path_replace(self, path: None) -> None: ...

    def path_replace(self, path: str | None) -> str | None:
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

    @overload
    def path_replace_reverse(self, path: str) -> str: ...

    @overload
    def path_replace_reverse(self, path: None) -> None: ...

    def path_replace_reverse(self, path: str | None) -> str | None:
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

    @overload
    def path_replace_movie(self, path: str) -> str: ...

    @overload
    def path_replace_movie(self, path: None) -> None: ...

    def path_replace_movie(self, path: str | None) -> str | None:
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

    @overload
    def path_replace_reverse_movie(self, path: str) -> str: ...

    @overload
    def path_replace_reverse_movie(self, path: None) -> None: ...

    def path_replace_reverse_movie(self, path: str | None) -> str | None:
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
