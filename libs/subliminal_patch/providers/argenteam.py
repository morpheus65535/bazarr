# coding=utf-8
from __future__ import absolute_import
import logging
import os
import io
import time

from zipfile import ZipFile
from guessit import guessit
from requests import Session
from subliminal import Episode, Movie
from subliminal.utils import sanitize
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subzero.language import Language

BASE_URL = "https://argenteam.net/"
API_URL = BASE_URL + "api/v1/"

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(Subtitle):
    provider_name = "argenteam"
    hearing_impaired_verifiable = False

    def __init__(self, language, page_link, download_link, release_info, matches):
        super(ArgenteamSubtitle, self).__init__(language, page_link=page_link)
        self.page_link = page_link
        self.download_link = download_link
        self.found_matches = matches
        self.release_info = release_info

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        # Download links always have the srt filename with the release info.
        # We combine it with the release info as guessit will return the first key match.
        new_file = self.download_link.split("/")[-1] + self.release_info
        self.found_matches |= guess_matches(video, guessit(new_file))
        return self.found_matches


class ArgenteamProvider(Provider, ProviderSubtitleArchiveMixin):
    provider_name = "argenteam"
    languages = {Language.fromalpha2(l) for l in ["es"]}
    video_types = (Episode, Movie)
    subtitle_class = ArgenteamSubtitle
    hearing_impaired_verifiable = False
    language_list = list(languages)

    multi_result_throttle = 2  # seconds

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            "User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")
        }

    def terminate(self):
        self.session.close()

    def search_ids(self, title, **kwargs):
        query = title
        titles = kwargs.get("titles") or []

        is_episode = False
        if kwargs.get("season") and kwargs.get("episode"):
            is_episode = True
            query = f"{title} S{kwargs['season']:02}E{kwargs['episode']:02}"

        logger.info(f"Searching ID (episode: {is_episode}) for {query}")

        r = self.session.get(API_URL + "search", params={"q": query}, timeout=10)
        r.raise_for_status()

        results = r.json()
        match_ids = []
        if results["total"] >= 1:
            for result in results["results"]:
                if (result["type"] == "episode" and not is_episode) or (
                    result["type"] == "movie" and is_episode
                ):
                    continue

                # shortcut in case of matching imdb id (don't match NoneType)
                if not is_episode and f"tt{result.get('imdb', 'n/a')}" == kwargs.get(
                    "imdb_id"
                ):
                    logger.debug(f"Movie matched by IMDB ID, taking shortcut")
                    match_ids = [result["id"]]
                    break

                # advanced title check in case of multiple movie results
                if results["total"] > 1:
                    if not is_episode and kwargs.get("year"):
                        if result["title"] and not (
                            sanitize(result["title"])
                            in (
                                "%s %s" % (sanitize(name), kwargs.get("year"))
                                for name in titles
                            )
                        ):
                            continue

                match_ids.append(result["id"])
        else:
            logger.error(f"No episode ID found for {query}")

        if match_ids:
            logger.debug(
                f"Found matching IDs: {', '.join(str(id) for id in match_ids)}"
            )

        return match_ids

    def get_query_matches(self, video, **kwargs):
        matches = set()
        if isinstance(video, Episode) and kwargs.get("movie_kind") == "episode":
            if video.series and (
                sanitize(kwargs.get("title"))
                in (
                    sanitize(name) for name in [video.series] + video.alternative_series
                )
            ):
                matches.add("series")

            if video.season and kwargs.get("season") == video.season:
                matches.add("season")

            if video.episode and kwargs.get("episode") == video.episode:
                matches.add("episode")

            if video.tvdb_id and kwargs.get("tvdb_id") == str(video.tvdb_id):
                matches.add("tvdb_id")

            # year (year is not available for series, but we assume it matches)
            matches.add("year")

        elif isinstance(video, Movie) and kwargs.get("movie_kind") == "movie":
            if video.title and (
                sanitize(kwargs.get("title"))
                in (sanitize(name) for name in [video.title] + video.alternative_titles)
            ):
                matches.add("title")

            if video.imdb_id and f"tt{kwargs.get('imdb_id')}" == str(video.imdb_id):
                matches.add("imdb_id")

            if video.year and kwargs.get("year") == video.year:
                matches.add("year")
        else:
            logger.info(f"{kwargs.get('movie_kind')} is not a valid movie_kind")

        return matches

    def combine_release_info(self, release_dict):
        keys = ("source", "codec", "tags", "team")
        combine = [release_dict.get(key) for key in keys if release_dict.get(key)]
        if combine:
            return ".".join(combine)
        return "Unknown"

    def query(self, title, video, titles=None):
        is_episode = isinstance(video, Episode)
        season = episode = None
        url = API_URL + "movie"
        if is_episode:
            season = video.season
            episode = video.episode
            url = API_URL + "episode"
            argenteam_ids = self.search_ids(
                title, season=season, episode=episode, titles=titles
            )

        else:
            argenteam_ids = self.search_ids(
                title, year=video.year, imdb_id=video.imdb_id, titles=titles
            )

        if not argenteam_ids:
            return []

        language = self.language_list[0]
        subtitles = []
        has_multiple_ids = len(argenteam_ids) > 1
        for aid in argenteam_ids:
            response = self.session.get(url, params={"id": aid}, timeout=10)
            response.raise_for_status()
            content = response.json()
            if not content:
                continue

            imdb_id = year = None
            returned_title = title
            if not is_episode and "info" in content:
                imdb_id = content["info"].get("imdb")
                year = content["info"].get("year")
                returned_title = content["info"].get("title", title)

            for r in content["releases"]:
                for s in r["subtitles"]:
                    movie_kind = "episode" if is_episode else "movie"
                    page_link = f"{BASE_URL}{movie_kind}/{aid}"
                    release_info = self.combine_release_info(r)
                    download_link = s["uri"].replace("http", "https")

                    matches_ = self.get_query_matches(
                        video,
                        movie_kind=movie_kind,
                        season=season,
                        episode=episode,
                        title=returned_title,
                        year=year,
                        imdb_id=imdb_id,
                        tvdb_id=content.get("tvdb"),
                    )
                    subtitles.append(
                        ArgenteamSubtitle(
                            language,
                            page_link,
                            download_link,
                            release_info,
                            matches_,
                        )
                    )

            if has_multiple_ids:
                time.sleep(self.multi_result_throttle)

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series[:2]
        else:
            titles = [video.title] + video.alternative_titles[:2]

        for title in titles:
            subs = self.query(title, video, titles=titles)
            if subs:
                return subs
            time.sleep(self.multi_result_throttle)

        return []

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info("Downloading subtitle %r", subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            subtitle.content = self.get_subtitle_from_archive(subtitle, zf)
