# coding=utf-8

import logging
import types
import os
import datetime

from guessit import guessit
from requests.compat import urljoin, quote
from subliminal import Episode, Movie, region
from subliminal_patch.core import remove_crap_from_fn
from subliminal_patch.http import CertifiSession

logger = logging.getLogger(__name__)


class DroneAPIClient(object):
    api_url = None
    _fill_attrs = None

    def __init__(self, version=1, session=None, headers=None, timeout=10, base_url=None, api_key=None,
                 ssl_no_verify=False):
        headers = dict(headers or {}, **{"X-Api-Key": api_key})

        #: Session for the requests
        self.session = session or CertifiSession()
        if ssl_no_verify:
            self.session.verify = False

        self.session.timeout = timeout
        self.session.headers.update(headers or {})

        if not base_url.endswith("/"):
            base_url += "/"

        if not base_url.startswith("http"):
            base_url = "http://%s" % base_url

        if not base_url.endswith("api/"):
            self.api_url = urljoin(base_url, "api/")

    def get_guess(self, video, scene_name):
        raise NotImplemented

    def get_additional_data(self, video):
        raise NotImplemented

    def build_params(self, params):
        """
        quotes values and converts keys of params to camelCase from underscore
        :param params: dict
        :return:
        """
        out = {}
        for key, value in params.iteritems():
            if not isinstance(value, types.StringTypes):
                value = str(value)

            elif isinstance(value, unicode):
                value = value.encode("utf-8")

            key = key.split('_')[0] + ''.join(x.capitalize() for x in key.split('_')[1:])
            out[key] = quote(value)
        return out

    def get(self, endpoint, requests_kwargs=None, **params):
        url = urljoin(self.api_url, endpoint)
        params = self.build_params(params)

        # perform the request
        r = self.session.get(url, params=params, **(requests_kwargs or {}))
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j:
            return j
        return []

    def status(self, **kwargs):
        return self.get("system/status", requests_kwargs=kwargs)

    def update_video(self, video, scene_name):
        """
        update video attributes based on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        scene_fn, guess = self.get_guess(video, scene_name)
        video_fn = os.path.basename(video.name)
        for attr in self._fill_attrs:
            if attr in guess:
                value = guess.get(attr)
                logger.debug(u"%s: Filling attribute %s: %s", video_fn, attr, value)
                setattr(video, attr, value)

        video.original_name = scene_fn


def sonarr_series_cache_key(namespace, fn, **kw):
    def generate_key(*arg):
        return "sonarr_series"
    return generate_key


class SonarrClient(DroneAPIClient):
    needs_attrs_to_work = ("series", "season", "episode",)
    _fill_attrs = ("release_group", "format",)
    cfg_name = "sonarr"

    def __init__(self, base_url="http://127.0.0.1:8989/", **kwargs):
        super(SonarrClient, self).__init__(base_url=base_url, **kwargs)

    @region.cache_on_arguments(should_cache_fn=lambda x: bool(x),
                               function_key_generator=sonarr_series_cache_key)
    def get_all_series(self):
        return self.get("series")

    def get_show_id(self, video):
        def is_correct_show(s):
            return s["title"] == video.series or (video.series_tvdb_id and "tvdbId" in s and
                                                  s["tvdbId"] == video.series_tvdb_id)

        for show in self.get_all_series():
            if is_correct_show(show):
                return show["id"]

        logger.debug(u"%s: Show not found, refreshing cache: %s", video.name, video.series)
        for show in self.get_all_series.refresh(self):
            if is_correct_show(show):
                return show["id"]

    def get_additional_data(self, video):
        for attr in self.needs_attrs_to_work:
            if getattr(video, attr, None) is None:
                logger.debug(u"%s: Not enough data available for Sonarr", video.name)
                return

        found_show_id = self.get_show_id(video)

        if not found_show_id:
            logger.debug(u"%s: Show not found in Sonarr: %s", video.name, video.series)
            return

        episode_fn = os.path.basename(video.name)

        for episode in self.get("episode", series_id=found_show_id):
            episode_file = episode.get("episodeFile", {})
            if os.path.basename(episode_file.get("relativePath", "")) == episode_fn:
                scene_name = episode_file.get("sceneName")
                original_filepath = episode_file.get("originalFilePath")

                data = {}
                if scene_name:
                    logger.debug(u"%s: Got scene filename from Sonarr: %s", episode_fn, scene_name)
                    data["scene_name"] = scene_name

                if original_filepath:
                    logger.debug(u"%s: Got original file path from Sonarr: %s", episode_fn, original_filepath)
                    data["original_filepath"] = original_filepath

                if data:
                    return data

                logger.debug(u"%s: Can't get original filename, sceneName-attribute not set", episode_fn)
                return

        logger.debug(u"%s: Episode not found in Sonarr: S%02dE%02d", episode_fn, video.season, video.episode)

    def get_guess(self, video, scene_name):
        """
        run guessit on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        ext = os.path.splitext(video.name)[1]
        guess_from = remove_crap_from_fn(scene_name + ext)

        # guess
        hints = {
            "single_value": True,
            "type": "episode",
        }

        return guess_from, guessit(guess_from, options=hints)


def radarr_movies_cache_key(namespace, fn, **kw):
    def generate_key(*arg):
        return "radarr_movies"
    return generate_key


class RadarrClient(DroneAPIClient):
    needs_attrs_to_work = ("title",)
    _fill_attrs = ("release_group", "format",)
    cfg_name = "radarr"

    def __init__(self, base_url="http://127.0.0.1:7878/", **kwargs):
        super(RadarrClient, self).__init__(base_url=base_url, **kwargs)

    @region.cache_on_arguments(should_cache_fn=lambda x: bool(x["data"]), function_key_generator=radarr_movies_cache_key)
    def get_all_movies(self):
        return {"d": datetime.datetime.now(), "data": self.get("movie")}

    def get_movie(self, movie_fn, movie_path):
        def is_correct_movie(m):
            movie_file = movie.get("movieFile", {})
            if os.path.basename(movie_file.get("relativePath", "")) == movie_fn:
                return m

        res = self.get_all_movies()
        try:
            # get creation date of movie_path to see whether our cache is still valid
            ctime = os.path.getctime(movie_path)
            created = datetime.datetime.fromtimestamp(ctime)
            if created < res["d"]:
                for movie in res["data"]:
                    if is_correct_movie(movie):
                        return movie
        except TypeError:
            # legacy cache data
            pass

        logger.debug(u"%s: Movie not found, refreshing cache", movie_fn)
        res = self.get_all_movies.refresh(self)
        for movie in res["data"]:
            if is_correct_movie(movie):
                return movie

    def get_additional_data(self, video):
        for attr in self.needs_attrs_to_work:
            if getattr(video, attr, None) is None:
                logger.debug(u"%s: Not enough data available for Radarr")
                return
        movie_fn = os.path.basename(video.name)

        movie = self.get_movie(movie_fn, video.name)
        if not movie:
            logger.debug(u"%s: Movie not found", movie_fn)

        else:
            movie_file = movie.get("movieFile", {})
            scene_name = movie_file.get("sceneName")
            release_group = movie_file.get("releaseGroup")

            additional_data = {}
            if scene_name:
                logger.debug(u"%s: Got scene filename from Radarr: %s", movie_fn, scene_name)
                additional_data["scene_name"] = scene_name

            if release_group:
                logger.debug(u"%s: Got release group from Radarr: %s", movie_fn, release_group)
                additional_data["release_group"] = release_group

            return additional_data

    def get_guess(self, video, scene_name):
        """
        run guessit on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        ext = os.path.splitext(video.name)[1]
        guess_from = remove_crap_from_fn(scene_name + ext)

        # guess
        hints = {
            "single_value": True,
            "type": "movie",
        }

        return guess_from, guessit(guess_from, options=hints)


class DroneManager(object):
    registry = {
        Episode: SonarrClient,
        Movie: RadarrClient,
    }

    @classmethod
    def get_client(cls, video, cfg_kwa):
        media_type = type(video)
        client_cls = cls.registry.get(media_type)
        if not client_cls:
            raise NotImplementedError("Media type not supported: %s", media_type)

        return client_cls(**cfg_kwa[client_cls.cfg_name])


def refine(video, **kwargs):
    """

    :param video:
    :param embedded_subtitles:
    :param kwargs:
    :return:
    """

    client = DroneManager.get_client(video, kwargs)

    additional_data = client.get_additional_data(video)

    if additional_data:
        if "scene_name" in additional_data:
            client.update_video(video, additional_data["scene_name"])

        elif "original_filepath" in additional_data:
            client.update_video(video, os.path.splitext(additional_data["original_filepath"])[0])

        if "release_group" in additional_data and not video.release_group:
            video.release_group = remove_crap_from_fn(additional_data["release_group"])
