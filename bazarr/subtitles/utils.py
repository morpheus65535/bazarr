# coding=utf-8
# fmt: off

import logging
import os
import json

from subzero.language import Language
from subzero.video import parse_video
from guessit.jsonutils import GuessitEncoder

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

    try:
        logging.debug(f'BAZARR guessing video object using video file path: {path}')
        skip_hashing = settings.general.skip_hashing
        video = parse_video(path, hints=hints, skip_hashing=skip_hashing, dry_run=False, providers=providers)
        if sceneName != "None":
            # refine the video object using the sceneName and update the video object accordingly
            scenename_with_extension = sceneName + os.path.splitext(path)[1]
            logging.debug(f'BAZARR guessing video object using scene name: {scenename_with_extension}')
            scenename_video = parse_video(scenename_with_extension, hints=hints, dry_run=True)
            refine_video_with_scenename(initial_video=video, scenename_video=scenename_video)
            logging.debug('BAZARR resulting video object once refined using scene name: %s',
                          json.dumps(vars(video), cls=GuessitEncoder, indent=4, ensure_ascii=False))

        for key, refiner in registered_refiners.items():
            logging.debug("Running refiner: %s", key)
            refiner(path, video)

        logging.debug('BAZARR is using these video object properties: %s', json.dumps(vars(video),
                                                                                      cls=GuessitEncoder, indent=4,
                                                                                      ensure_ascii=False))
        return video

    except Exception as error:
        logging.exception("BAZARR Error (%s) trying to get video information for this file: %s", error, path)


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


def refine_video_with_scenename(initial_video, scenename_video):
    for key, value in vars(scenename_video).items():
        if value and getattr(initial_video, key) in [None, (), {}, []]:
            setattr(initial_video, key, value)
    return initial_video
