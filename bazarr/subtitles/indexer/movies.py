# coding=utf-8

import gc
import os
import logging
import ast

from subliminal_patch import core, search_external_subtitles

from languages.custom_lang import CustomLanguage
from app.database import get_profiles_list, get_profile_cutoff, TableMovies, get_audio_profile_languages, database, \
    update, select
from languages.get_languages import alpha2_from_alpha3, get_language_set
from app.config import settings
from utilities.helper import get_subtitle_destination_folder
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_subs_reader
from app.event_handler import event_stream, show_progress, hide_progress
from subtitles.indexer.utils import guess_external_subtitles, get_external_subtitles_path

gc.enable()


def store_subtitles_movie(original_path, reversed_path, use_cache=True):
    logging.debug(f'BAZARR started subtitles indexing for this file: {reversed_path}')
    actual_subtitles = []
    if os.path.exists(reversed_path):
        if settings.general.use_embedded_subs:
            logging.debug("BAZARR is trying to index embedded subtitles.")
            item = database.execute(
                select(TableMovies.movie_file_id, TableMovies.file_size)
                .where(TableMovies.path == original_path)) \
                .first()
            if not item:
                logging.exception(f"BAZARR error when trying to select this movie from database: {reversed_path}")
            else:
                try:
                    subtitle_languages = embedded_subs_reader(reversed_path,
                                                              file_size=item.file_size,
                                                              movie_file_id=item.movie_file_id,
                                                              use_cache=use_cache)
                    for subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                        try:
                            if (settings.general.ignore_pgs_subs and subtitle_codec.lower() == "pgs") or \
                                    (settings.general.ignore_vobsub_subs and subtitle_codec.lower() ==
                                     "vobsub") or \
                                    (settings.general.ignore_ass_subs and subtitle_codec.lower() ==
                                     "ass"):
                                logging.debug("BAZARR skipping %s sub for language: %s" % (subtitle_codec, alpha2_from_alpha3(subtitle_language)))
                                continue

                            if alpha2_from_alpha3(subtitle_language) is not None:
                                lang = str(alpha2_from_alpha3(subtitle_language))
                                if subtitle_forced:
                                    lang = f'{lang}:forced'
                                if subtitle_hi:
                                    lang = f'{lang}:hi'
                                logging.debug(f"BAZARR embedded subtitles detected: {lang}")
                                actual_subtitles.append([lang, None, None])
                        except Exception as error:
                            logging.debug(f"BAZARR unable to index this unrecognized language: {subtitle_language} "
                                          f"({error})")
                except Exception:
                    logging.exception(
                        f"BAZARR error when trying to analyze this {os.path.splitext(reversed_path)[1]} file: "
                        f"{reversed_path}")

        try:
            dest_folder = get_subtitle_destination_folder()
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []

            # get previously indexed subtitles that haven't changed:
            item = database.execute(
                select(TableMovies.subtitles)
                .where(TableMovies.path == original_path))\
                .first()
            if not item:
                previously_indexed_subtitles_to_exclude = []
            else:
                previously_indexed_subtitles = ast.literal_eval(item.subtitles) if item.subtitles else []
                previously_indexed_subtitles_to_exclude = [x for x in previously_indexed_subtitles
                                                           if len(x) == 3 and
                                                           x[1] and
                                                           os.path.isfile(path_mappings.path_replace(x[1])) and
                                                           os.stat(path_mappings.path_replace(x[1])).st_size == x[2]]

            subtitles = search_external_subtitles(reversed_path, languages=get_language_set(),
                                                  only_one=settings.general.single_language)
            full_dest_folder_path = os.path.dirname(reversed_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(reversed_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles, "movie",
                                                 previously_indexed_subtitles_to_exclude)
        except Exception:
            logging.exception("BAZARR unable to index external subtitles.")
        else:
            for subtitle, language in subtitles.items():
                valid_language = False
                if language:
                    if hasattr(language, 'alpha3'):
                        valid_language = alpha2_from_alpha3(language.alpha3)
                else:
                    logging.debug(f"Skipping subtitles because we are unable to define language: {subtitle}")
                    continue

                if not valid_language:
                    logging.debug(f'{language.alpha3} is an unsupported language code.')
                    continue

                subtitle_path = get_external_subtitles_path(reversed_path, subtitle)
                custom = CustomLanguage.found_external(subtitle, subtitle_path)

                if custom is not None:
                    actual_subtitles.append([custom, path_mappings.path_replace_reverse_movie(subtitle_path),
                                             os.stat(subtitle_path).st_size])

                elif str(language.basename) != 'und':
                    if language.forced:
                        language_str = f'{language}:forced'
                    elif language.hi:
                        language_str = f'{language}:hi'
                    else:
                        language_str = str(language)
                    logging.debug(f"BAZARR external subtitles detected: {language_str}")
                    actual_subtitles.append([language_str, path_mappings.path_replace_reverse_movie(subtitle_path),
                                             os.stat(subtitle_path).st_size])

        database.execute(
            update(TableMovies)
            .values(subtitles=str(actual_subtitles))
            .where(TableMovies.path == original_path))
        matching_movies = database.execute(
            select(TableMovies.radarrId)
            .where(TableMovies.path == original_path))\
            .all()

        for movie in matching_movies:
            if movie:
                logging.debug(f"BAZARR storing those languages to DB: {actual_subtitles}")
                list_missing_subtitles_movies(no=movie.radarrId)
            else:
                logging.debug(f"BAZARR haven't been able to update existing subtitles to DB: {actual_subtitles}")
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")

    logging.debug(f'BAZARR ended subtitles indexing for this file: {reversed_path}')

    return actual_subtitles


def list_missing_subtitles_movies(no=None, send_event=True):
    stmt = select(TableMovies.radarrId,
                  TableMovies.subtitles,
                  TableMovies.profileId,
                  TableMovies.audio_language)

    if no:
        movies_subtitles = database.execute(stmt.where(TableMovies.radarrId == no)).all()
    else:
        movies_subtitles = database.execute(stmt).all()

    use_embedded_subs = settings.general.use_embedded_subs

    matches_audio = lambda language: any(x['code2'] == language['language'] for x in get_audio_profile_languages(
                                movie_subtitles.audio_language))

    for movie_subtitles in movies_subtitles:
        missing_subtitles_text = '[]'
        if movie_subtitles.profileId:
            # get desired subtitles
            desired_subtitles_temp = get_profiles_list(profile_id=movie_subtitles.profileId)
            desired_subtitles_list = []
            if desired_subtitles_temp:
                for language in desired_subtitles_temp['items']:
                    if language['audio_exclude'] == "True":
                        if matches_audio(language):
                            continue
                    if language['audio_only_include'] == "True":
                        if not matches_audio(language):
                            continue
                    desired_subtitles_list.append({'language': language['language'],
                                                   'forced': language['forced'],
                                                   'hi': language['hi']})

            # get existing subtitles
            actual_subtitles_list = []
            if movie_subtitles.subtitles is not None:
                if use_embedded_subs:
                    actual_subtitles_temp = ast.literal_eval(movie_subtitles.subtitles)
                else:
                    actual_subtitles_temp = [x for x in ast.literal_eval(movie_subtitles.subtitles) if x[1]]

                for subtitles in actual_subtitles_temp:
                    subtitles = subtitles[0].split(':')
                    lang = subtitles[0]
                    forced = False
                    hi = False
                    if len(subtitles) > 1:
                        if subtitles[1] == 'forced':
                            forced = True
                            hi = False
                        elif subtitles[1] == 'hi':
                            forced = False
                            hi = True
                    actual_subtitles_list.append({'language': lang,
                                                  'forced': str(forced),
                                                  'hi': str(hi)})

            # check if cutoff is reached and skip any further check
            cutoff_met = False
            cutoff_temp_list = get_profile_cutoff(profile_id=movie_subtitles.profileId)

            if cutoff_temp_list:
                for cutoff_temp in cutoff_temp_list:
                    cutoff_language = {'language': cutoff_temp['language'],
                                       'forced': cutoff_temp['forced'],
                                       'hi': cutoff_temp['hi']}
                    if cutoff_temp['audio_only_include'] == 'True' and not matches_audio(cutoff_temp):
                        # We don't want subs in this language unless it matches
                        # the audio. Don't use it to meet the cutoff.
                        continue
                    elif cutoff_temp['audio_exclude'] == 'True' and matches_audio(cutoff_temp):
                        # The cutoff is met through one of the audio tracks.
                        cutoff_met = True
                    elif cutoff_language in actual_subtitles_list:
                        cutoff_met = True
                    # HI is considered as good as normal
                    elif (cutoff_language and
                          {'language': cutoff_language['language'],
                           'forced': 'False',
                           'hi': 'True'} in actual_subtitles_list):
                        cutoff_met = True

            if cutoff_met:
                missing_subtitles_text = str([])
            else:
                # get difference between desired and existing subtitles
                missing_subtitles_list = []
                for item in desired_subtitles_list:
                    if item not in actual_subtitles_list:
                        missing_subtitles_list.append(item)

                    # remove missing that have forced or hi subtitles for this language in existing
                for item in actual_subtitles_list:
                    if item['hi'] == 'True':
                        try:
                            missing_subtitles_list.remove({'language': item['language'],
                                                           'forced': 'False',
                                                           'hi': 'False'})
                        except ValueError:
                            pass

                # make the missing languages list looks like expected
                missing_subtitles_output_list = []
                for item in missing_subtitles_list:
                    lang = item['language']
                    if item['forced'] == 'True':
                        lang += ':forced'
                    elif item['hi'] == 'True':
                        lang += ':hi'
                    missing_subtitles_output_list.append(lang)

                missing_subtitles_text = str(missing_subtitles_output_list)

        database.execute(
            update(TableMovies)
            .values(missing_subtitles=missing_subtitles_text)
            .where(TableMovies.radarrId == movie_subtitles.radarrId))

        if send_event:
            event_stream(type='movie', payload=movie_subtitles.radarrId)
            event_stream(type='movie-wanted', action='update', payload=movie_subtitles.radarrId)
    if send_event:
        event_stream(type='badges')


def movies_full_scan_subtitles(use_cache=None):
    if use_cache is None:
        use_cache = settings.radarr.use_ffprobe_cache

    movies = database.execute(
        select(TableMovies.path))\
        .all()

    count_movies = len(movies)
    for i, movie in enumerate(movies):
        show_progress(id='movies_disk_scan',
                      header='Full disk scan...',
                      name='Movies subtitles',
                      value=i,
                      count=count_movies)
        store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path), use_cache=use_cache)

    show_progress(id='movies_disk_scan',
                  header='Full disk scan...',
                  name='Movies subtitles',
                  value=count_movies,
                  count=count_movies)

    gc.collect()


def movies_scan_subtitles(no):
    movies = database.execute(
        select(TableMovies.path)
        .where(TableMovies.radarrId == no)
        .order_by(TableMovies.radarrId)) \
        .all()

    for movie in movies:
        store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path), use_cache=False)
