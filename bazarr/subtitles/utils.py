# coding=utf-8
# fmt: off

import logging
import os

from subzero.language import Language
from subzero.video import parse_video

from app.config import settings
from languages.custom_lang import CustomLanguage
from app.database import get_profiles_list
from subtitles.tools.score import movie_score, series_score

from .refiners import registered as registered_refiners


def get_video(path, title, sceneName, providers=None, media_type="movie"):
    """
    Construct `Video` instance
    :param path: path to video
    :param title: series/movie title
    :param sceneName: sceneName
    :param providers: provider list for selective hashing
    :param media_type: movie/series
    :return: `Video` instance
    """
    hints = {"title": title, "type": "movie" if media_type == "movie" else "episode"}
    used_scene_name = False
    original_path = path
    original_name = os.path.basename(path)
    hash_from = None
    if sceneName != "None":
        # use the sceneName but keep the folder structure for better guessing
        path = os.path.join(os.path.dirname(path), sceneName + os.path.splitext(path)[1])
        used_scene_name = True
        hash_from = original_path

    try:
        skip_hashing = settings.general.skip_hashing
        video = parse_video(path, hints=hints, skip_hashing=skip_hashing, dry_run=used_scene_name, providers=providers,
                            hash_from=hash_from)
        video.used_scene_name = used_scene_name
        video.original_name = original_name
        video.original_path = original_path

        for key, refiner in registered_refiners.items():
            logging.debug("Running refiner: %s", key)
            refiner(original_path, video)

        logging.debug('BAZARR is using these video object properties: %s', vars(video))
        return video

    except Exception as error:
        logging.exception("BAZARR Error (%s) trying to get video information for this file: %s", error, original_path)


def _get_download_code3(subtitle):
    custom = CustomLanguage.from_value(subtitle.language, "language")
    if custom is None:
        return subtitle.language.alpha3
    return custom.alpha3


def _get_lang_obj(alpha3):
    sub = CustomLanguage.from_value(alpha3, "alpha3")
    if sub is None:
        return Language(alpha3)

    return sub.subzero_language()


def _get_scores(media_type, min_movie=None, min_ep=None):
    series = "series" == media_type
    handler = series_score if series else movie_score
    min_movie = min_movie or (60 * 100 / handler.max_score)
    min_ep = min_ep or (240 * 100 / handler.max_score)
    min_score_ = int(min_ep if series else min_movie)
    return handler.get_scores(min_score_)


def get_ban_list(profile_id):
    if profile_id:
        profile = get_profiles_list(profile_id)
        if profile:
            return {'must_contain': profile['mustContain'] or [],
                    'must_not_contain': profile['mustNotContain'] or []}
    return None


def _set_forced_providers(pool, also_forced=False, forced_required=False):
    # TODO: maybe a separate pool for forced configs? also_foreign/only_foreign is hardcoded
    # in get_providers and this causes updating the pool on every call
    if also_forced and forced_required:
        logging.debug('also_forced and forced_required cannot be both True. also_forced will prevail.')
        forced_required = False
    pool.provider_configs.update(
        {
            "podnapisi": {'also_foreign': also_forced, "only_foreign": forced_required},
            "opensubtitles": {'also_foreign': also_forced, "only_foreign": forced_required}
        }
    )
