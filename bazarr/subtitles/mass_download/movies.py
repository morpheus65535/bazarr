# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableMovies
from app.event_handler import show_progress, hide_progress

from ..download import generate_subtitles


def movies_download_subtitles(no):
    conditions = [(TableMovies.radarrId == no)]
    conditions += get_exclusion_clause('movie')
    movies = TableMovies.select(TableMovies.path,
                                TableMovies.missing_subtitles,
                                TableMovies.audio_language,
                                TableMovies.radarrId,
                                TableMovies.sceneName,
                                TableMovies.title,
                                TableMovies.tags,
                                TableMovies.monitored)\
        .where(reduce(operator.and_, conditions))\
        .dicts()
    if not len(movies):
        logging.debug("BAZARR no movie with that radarrId can be found in database:", str(no))
        return
    else:
        movie = movies[0]

    if ast.literal_eval(movie['missing_subtitles']):
        count_movie = len(ast.literal_eval(movie['missing_subtitles']))
    else:
        count_movie = 0

    audio_language_list = get_audio_profile_languages(movie['audio_language'])
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []

    for language in ast.literal_eval(movie['missing_subtitles']):
        providers_list = get_providers()

        if providers_list:
            if language is not None:
                hi_ = "True" if language.endswith(':hi') else "False"
                forced_ = "True" if language.endswith(':forced') else "False"
                languages.append((language.split(":")[0], hi_, forced_))
        else:
            logging.info("BAZARR All providers are throttled")
            break

    show_progress(id='movie_search_progress_{}'.format(no),
                  header='Searching missing subtitles...',
                  name=movie['title'],
                  value=0,
                  count=count_movie)

    for result in generate_subtitles(path_mappings.path_replace_movie(movie['path']),
                                     languages,
                                     audio_language,
                                     str(movie['sceneName']),
                                     movie['title'],
                                     'movie',
                                     check_if_still_required=True):

        if result:
            message = result[0]
            path = result[1]
            forced = result[5]
            if result[8]:
                language_code = result[2] + ":hi"
            elif forced:
                language_code = result[2] + ":forced"
            else:
                language_code = result[2]
            provider = result[3]
            score = result[4]
            subs_id = result[6]
            subs_path = result[7]
            store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
            history_log_movie(1, no, message, path, language_code, provider, score, subs_id, subs_path)
            send_notifications_movie(no, message)

    hide_progress(id='movie_search_progress_{}'.format(no))
