# coding=utf-8

import re
from typing import overload

from app.config import settings


class PathMappings:
    def __init__(self) -> None:
        self.path_mapping_series: list[list[str] | tuple[str, str]] = []
        self.path_mapping_movies: list[list[str] | tuple[str, str]] = []

    def update(self) -> None:
        """
        Refresh the cached path mapping lists from the current application
        settings.

        Reads the series and movie path mappings from the general settings
        section and stores only those entries whose source and destination
        paths differ, discarding identity mappings that would have no effect
        when translating paths. This method should be called whenever the
        settings are reloaded so that the in-memory mappings stay in sync
        with the persisted configuration.

        :return: None
        """
        self.path_mapping_series = [x for x in settings.general.path_mappings if x[0] != x[1]]
        self.path_mapping_movies = [x for x in settings.general.path_mappings_movie if x[0] != x[1]]

    @overload
    def path_replace(self, path: str) -> str: ...

    @overload
    def path_replace(self, path: None) -> None: ...

    def path_replace(self, path: str | None) -> str | None:
        """
        Replace a path prefix according to the configured path mapping series.

        Iterates over the path mapping pairs stored in ``path_mapping_series``
        and applies the first mapping whose source segment is contained in the
        given path. Mappings whose source and target are identical, or that
        contain an empty string, are skipped. After the replacement the
        directory separators are normalized: paths that look like UNC paths or
        Windows drive paths are converted to backslashes, while paths starting
        with a forward slash are converted to forward slashes. Only the first
        matching mapping is applied.

        :param path: The path to transform, or ``None`` if no path is
            available.
        :return: The transformed path with normalized separators, the original
            path if no mapping matched, or ``None`` if the input was ``None``.
        """
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
        """
        Reverse-map a path using the configured path mapping series.

        Iterates over ``self.path_mapping_series`` and, for the first mapping whose
        second element (the mapped/target form) is contained in the given path,
        replaces that element with the first element (the original/source form).
        Mappings whose two elements are identical, or that contain an empty string,
        are skipped. After the replacement, path separators are normalized: paths
        that look like Windows paths (UNC paths starting with ``\\\\`` or
        drive-letter paths such as ``C:\\``) are converted to use backslashes,
        while POSIX-style paths starting with ``/`` are converted to use forward
        slashes. Only the first matching mapping is applied.

        :param path: The path to reverse-map. May be ``None``, in which case no
            processing is performed.
        :return: The reverse-mapped path with normalized separators, the original
            path unchanged if no mapping matched, or ``None`` if ``path`` was
            ``None``.
        """
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
        """
        Apply the configured movie path mappings to the given path.

        Iterates over the path mapping pairs defined in ``path_mapping_movies``
        and replaces the first matching source prefix with its corresponding
        destination value. Mappings whose source and destination are identical
        or that contain an empty string are ignored. After a replacement is
        performed, the path separators are normalized according to the
        resulting path style: Windows-style paths (UNC paths or paths starting
        with a drive letter) are converted to use backslashes, while POSIX-style
        paths starting with a slash are converted to use forward slashes. Only
        the first matching mapping is applied.

        :param path: The original movie path to be remapped, or ``None`` if no
            path is available.
        :return: The remapped and separator-normalized path, the original path
            if no mapping matched, or ``None`` if the input was ``None``.
        """
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
        """
        Reverse the configured movie path mapping on the given path.

        Iterates over the movie path mappings and, for the first mapping whose
        target component is contained in the path, substitutes it with the
        corresponding source component. Mappings whose source and target are
        identical, or that contain an empty component, are skipped. After the
        substitution, path separators are normalized: Windows-style paths
        (UNC paths or paths starting with a drive letter) are converted to use
        backslashes, while POSIX-style paths starting with a slash are converted
        to use forward slashes. Only the first matching mapping is applied.

        :param path: The movie file path to reverse-map, or ``None`` if no path
            is available.
        :return: The path with the reverse movie mapping applied and separators
            normalized, the unchanged path if no mapping matched, or ``None`` if
            the input path was ``None``.
        """
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
