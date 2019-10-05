# coding=utf-8

import logging
import os

from babelfish.exceptions import LanguageError
from subzero.language import Language, language_from_stream
from subliminal_patch import scan_video, refine, search_external_subtitles

logger = logging.getLogger(__name__)


def has_external_subtitle(part_id, stored_subs, language):
    stored_sub = stored_subs.get_any(part_id, language)
    if stored_sub and stored_sub.storage_type == "filesystem":
        return True


def set_existing_languages(video, video_info, external_subtitles=False, embedded_subtitles=False, known_embedded=None,
                           stored_subs=None, languages=None, only_one=False, known_metadata_subs=None,
                           match_strictness="strict"):
    logger.debug(u"Determining existing subtitles for %s", video.name)

    external_langs_found = set()
    # scan for external subtitles
    if known_metadata_subs:
        # existing metadata subtitles
        external_langs_found = known_metadata_subs

    external_langs_found.update(set(search_external_subtitles(video.name, languages=languages,
                                                              only_one=only_one,
                                                              match_strictness=match_strictness).values()))

    # found external subtitles should be considered?
    if external_subtitles:
        # |= is update, thanks plex
        video.subtitle_languages.update(external_langs_found)
        video.external_subtitle_languages.update(external_langs_found)

    else:
        # did we already download subtitles for this?
        if stored_subs and external_langs_found:
            for lang in external_langs_found:
                if has_external_subtitle(video_info["plex_part"].id, stored_subs, lang):
                    logger.info("Not re-downloading subtitle for language %s, it already exists on the filesystem",
                                lang)
                    video.subtitle_languages.add(lang)

    # add known embedded subtitles
    if embedded_subtitles and known_embedded:
        # mp4 and stuff, check burned in
        for language in known_embedded:
            logger.debug('Found embedded subtitle %r', language)
            video.subtitle_languages.add(language)


def parse_video(fn, hints, skip_hashing=False, dry_run=False, providers=None, hash_from=None):
    logger.debug("Parsing video: %s, hints: %s", os.path.basename(fn), hints)
    return scan_video(fn, hints=hints, dont_use_actual_file=dry_run, providers=providers,
                      skip_hashing=skip_hashing, hash_from=hash_from)


def refine_video(video, no_refining=False, refiner_settings=None):
    refiner_settings = refiner_settings or {}
    video_info = video.plexapi_metadata
    hints = video.hints

    if no_refining:
        logger.debug("Taking parse_video shortcut")
        return video

    # refiners
    refine_kwargs = {
        "episode_refiners": ['sz_tvdb', 'sz_omdb',],
        "movie_refiners": ['sz_omdb',],
        "embedded_subtitles": False,
    }
    refine_kwargs.update(refiner_settings)

    if "filebot" in refiner_settings:
        # filebot always comes first
        refine_kwargs["episode_refiners"].insert(0, "filebot")
        refine_kwargs["movie_refiners"].insert(0, "filebot")

    if "symlinks" in refiner_settings:
        refine_kwargs["episode_refiners"].insert(0, "symlinks")
        refine_kwargs["movie_refiners"].insert(0, "symlinks")

    if "file_info_file" in refiner_settings:
        # file_info_file always comes first
        refine_kwargs["episode_refiners"].insert(0, "file_info_file")
        refine_kwargs["movie_refiners"].insert(0, "file_info_file")

    if "sonarr" in refiner_settings:
        # drone always comes last
        refine_kwargs["episode_refiners"].append("drone")

    if "radarr" in refiner_settings:
        refine_kwargs["movie_refiners"].append("drone")

    # our own metadata refiner :)
    if "stream" in video_info:
        for key, value in video_info["stream"].iteritems():
            if hasattr(video, key) and not getattr(video, key):
                logger.info(u"Adding stream %s info: %s", key, value)
                setattr(video, key, value)

    plex_title = video_info.get("original_title") or video_info.get("title")
    if hints["type"] == "episode":
        plex_title = video_info.get("original_title") or video_info.get("series")

    year = video_info.get("year")
    if not video.year and year:
        logger.info(u"Adding PMS year info: %s", year)
        video.year = year

    refine(video, **refine_kwargs)
    logger.info(u"Using filename: %s", video.original_name)

    if hints["type"] == "movie" and not video.imdb_id:
        if plex_title:
            logger.info(u"Adding PMS title/original_title info: %s", plex_title)
            old_title = video.title
            video.title = plex_title.replace(" - ", " ").replace(" -", " ").replace("- ", " ")

            # re-refine with new info
            logger.info(u"Re-refining with movie title: '%s' instead of '%s'", plex_title, old_title)
            refine(video, **refine_kwargs)

            video.alternative_titles.append(old_title)

        # still no match? add our own data
        if not video.imdb_id:
            video.imdb_id = video_info.get("imdb_id")
            if video.imdb_id:
                logger.info(u"Adding PMS imdb_id info: %s", video.imdb_id)

    elif hints["type"] == "movie" and plex_title:
        pt = plex_title.replace(" - ", " ").replace(" -", " ").replace("- ", " ")
        if pt != video.title:
            video.alternative_titles.append(pt)

    if hints["type"] == "episode":
        video.season = video_info.get("season", video.season)
        video.episode = video_info.get("episode", video.episode)
        if not video.series_tvdb_id and not video.tvdb_id and plex_title:
            # add our title
            logger.info(u"Adding PMS title/original_title info: %s", plex_title)
            old_title = video.series
            video.series = plex_title

            # re-refine with new info
            logger.info(u"Re-refining with series title: '%s' instead of '%s'", plex_title, old_title)
            refine(video, **refine_kwargs)

            video.alternative_series.append(old_title)

        elif plex_title and video.series != plex_title:
            video.alternative_series.append(plex_title)

        # still no match? add our own data
        if not video.series_tvdb_id or not video.tvdb_id:
            logger.info(u"Adding PMS year info: %s", video_info.get("year"))
            video.year = video_info.get("year")

        if not video.series_tvdb_id and video_info.get("series_tvdb_id"):
            logger.info(u"Adding PMS series_tvdb_id info: %s", video_info.get("series_tvdb_id"))
            video.series_tvdb_id = video_info.get("series_tvdb_id")

        if not video.tvdb_id and video_info.get("tvdb_id"):
            logger.info(u"Adding PMS tvdb_id info: %s", video_info.get("tvdb_id"))
            video.tvdb_id = video_info.get("tvdb_id")

    # did it match?
    if (hints["type"] == "episode" and not video.series_tvdb_id and not video.tvdb_id) \
            or (hints["type"] == "movie" and not video.imdb_id):
        logger.warning("Couldn't find corresponding series/movie in online databases, continuing")

    # guess special
    if hints["type"] == "episode":
        if video.season == 0 or video.episode == 0:
            video.is_special = True
        else:
            # check parent folder name
            if os.path.dirname(video.name).split(os.path.sep)[-1].lower() in ("specials", "season 00"):
                video.is_special = True

    return video
