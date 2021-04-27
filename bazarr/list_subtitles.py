# coding=utf-8

import gc
import os
import logging
import ast
import re
from guess_language import guess_language
from subliminal_patch import core, search_external_subtitles
from subzero.language import Language

from database import database, get_profiles_list, get_profile_cutoff
from get_languages import alpha2_from_alpha3, language_from_alpha2, get_language_set
from config import settings
from helper import path_mappings, get_subtitle_destination_folder

from embedded_subs_reader import embedded_subs_reader
from event_handler import event_stream
from charamel import Detector

gc.enable()

global hi_regex
hi_regex = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\(\{].{3,}[\]\)\}](?<!{\\an\d})')


def store_subtitles(original_path, reversed_path):
    logging.debug('BAZARR started subtitles indexing for this file: ' + reversed_path)
    actual_subtitles = []
    if os.path.exists(reversed_path):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(reversed_path, original_path)
                for subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        if (settings.general.getboolean("ignore_pgs_subs") and subtitle_codec.lower() == "pgs") or \
                                (settings.general.getboolean("ignore_vobsub_subs") and subtitle_codec.lower() ==
                                 "vobsub"):
                            logging.debug("BAZARR skipping %s sub for language: %s" % (subtitle_codec, alpha2_from_alpha3(subtitle_language)))
                            continue

                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ":forced"
                            if subtitle_hi:
                                lang = lang + ":hi"
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(reversed_path)[1], reversed_path))
                pass

        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        simplified_chinese_fuzzy = [u"简", u"双语"]
        simplified_chinese = [".chs", ".sc", ".zhs",".zh-hans",".hans",".zh_hans",".zhhans",".gb",".simplified"]
        simplified_chinese_forced = [".chs.forced", ".sc.forced", ".zhs.forced", "hans.forced", ".gb.forced", u"简体中文.forced", u"双语.forced"]
        traditional_chinese_fuzzy = [u"繁", u"雙語"]
        traditional_chinese = [".cht", ".tc", ".zh-tw", ".zht",".zh-hant",".zhhant",".zh_hant",".hant", ".big5", ".traditional"]
        traditional_chinese_forced = [".cht.forced", ".tc.forced", ".zht.forced", "hant.forced", ".big5.forced", u"繁體中文.forced", u"雙語.forced", "zh-tw.forced"]

        try:
            dest_folder = get_subtitle_destination_folder()
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(reversed_path, languages=get_language_set(),
                                                  only_one=settings.general.getboolean('single_language'))
            full_dest_folder_path = os.path.dirname(reversed_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(reversed_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.items():
                subtitle_path = get_external_subtitles_path(reversed_path, subtitle)
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"), path_mappings.path_replace_reverse(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)):
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append(
                        [str("pb:forced"), path_mappings.path_replace_reverse(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(simplified_chinese)) or (str(subtitle_path).lower())[:-5] in simplified_chinese_fuzzy:
                    logging.debug("BAZARR external subtitles detected: " + "zh")
                    actual_subtitles.append(
                        [str("zh"), path_mappings.path_replace_reverse(subtitle_path)])
                elif any(ext in (str(os.path.splitext(subtitle)[0]).lower())[-12:] for ext in simplified_chinese_forced):
                    logging.debug("BAZARR external subtitles detected: " + "zh:forced")
                    actual_subtitles.append(
                        [str("zh:forced"), path_mappings.path_replace_reverse(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(traditional_chinese)) or (str(subtitle_path).lower())[:-5] in traditional_chinese_fuzzy:
                    logging.debug("BAZARR external subtitles detected: " + "zt")
                    actual_subtitles.append(
                        [str("zt"), path_mappings.path_replace_reverse(subtitle_path)])
                elif any(ext in (str(os.path.splitext(subtitle)[0]).lower())[-12:] for ext in traditional_chinese_forced):
                    logging.debug("BAZARR external subtitles detected: " + "zt:forced")
                    actual_subtitles.append(
                        [str("zt:forced"), path_mappings.path_replace_reverse(subtitle_path)])
                elif not language:
                    continue
                elif str(language) != 'und':
                    if language.forced:
                        language_str = str(language)
                    elif language.hi:
                        language_str = str(language) + ':hi'
                    else:
                        language_str = str(language)
                    logging.debug("BAZARR external subtitles detected: " + language_str)
                    actual_subtitles.append([language_str, path_mappings.path_replace_reverse(subtitle_path)])

        database.execute("UPDATE table_episodes SET subtitles=? WHERE path=?",
                         (str(actual_subtitles), original_path))
        matching_episodes = database.execute("SELECT sonarrEpisodeId, sonarrSeriesId FROM table_episodes WHERE path=?",
                                   (original_path,))

        for episode in matching_episodes:
            if episode:
                logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
                list_missing_subtitles(epno=episode['sonarrEpisodeId'])
            else:
                logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")

    logging.debug('BAZARR ended subtitles indexing for this file: ' + reversed_path)

    return actual_subtitles


def store_subtitles_movie(original_path, reversed_path):
    logging.debug('BAZARR started subtitles indexing for this file: ' + reversed_path)
    actual_subtitles = []
    if os.path.exists(reversed_path):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(reversed_path, original_path)
                for subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        if (settings.general.getboolean("ignore_pgs_subs") and subtitle_codec.lower() == "pgs") or \
                                (settings.general.getboolean("ignore_vobsub_subs") and subtitle_codec.lower() ==
                                 "vobsub"):
                            logging.debug("BAZARR skipping %s sub for language: %s" % (subtitle_codec, alpha2_from_alpha3(subtitle_language)))
                            continue

                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ':forced'
                            if subtitle_hi:
                                lang = lang + ':hi'
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(reversed_path)[1], reversed_path))
                pass

        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        simplified_chinese_fuzzy = [u"简", u"双语"]
        simplified_chinese = [".chs", ".sc", ".zhs",".zh-hans",".hans",".zh_hans",".zhhans",".gb",".simplified"]
        simplified_chinese_forced = [".chs.forced", ".sc.forced", ".zhs.forced", "hans.forced", ".gb.forced", u"简体中文.forced", u"双语.forced"]
        traditional_chinese_fuzzy = [u"繁", u"雙語"]
        traditional_chinese = [".cht", ".tc", ".zh-tw", ".zht",".zh-hant",".zhhant",".zh_hant",".hant", ".big5", ".traditional"]
        traditional_chinese_forced = [".cht.forced", ".tc.forced", ".zht.forced", "hant.forced", ".big5.forced", u"繁體中文.forced", u"雙語.forced", "zh-tw.forced"]
        try:
            dest_folder = get_subtitle_destination_folder() or ''
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(reversed_path, languages=get_language_set())
            full_dest_folder_path = os.path.dirname(reversed_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(reversed_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.items():
                subtitle_path = get_external_subtitles_path(reversed_path, subtitle)
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append([str("pb"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)):
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append([str("pb:forced"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(simplified_chinese)) or (str(subtitle_path).lower())[:-5] in simplified_chinese_fuzzy:
                    logging.debug("BAZARR external subtitles detected: " + "zh")
                    actual_subtitles.append([str("zh"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif any(ext in (str(os.path.splitext(subtitle)[0]).lower())[-12:] for ext in simplified_chinese_forced):
                    logging.debug("BAZARR external subtitles detected: " + "zh:forced")
                    actual_subtitles.append([str("zh:forced"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(traditional_chinese)) or (str(subtitle_path).lower())[:-5] in traditional_chinese_fuzzy:
                    logging.debug("BAZARR external subtitles detected: " + "zt")
                    actual_subtitles.append([str("zt"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif any(ext in (str(os.path.splitext(subtitle)[0]).lower())[-12:] for ext in traditional_chinese_forced):
                    logging.debug("BAZARR external subtitles detected: " + "zt:forced")
                    actual_subtitles.append([str("zt:forced"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif not language:
                    continue
                elif str(language.basename) != 'und':
                    if language.forced:
                        language_str = str(language)
                    elif language.hi:
                        language_str = str(language) + ':hi'
                    else:
                        language_str = str(language)
                    logging.debug("BAZARR external subtitles detected: " + language_str)
                    actual_subtitles.append([language_str, path_mappings.path_replace_reverse_movie(subtitle_path)])

        database.execute("UPDATE table_movies SET subtitles=? WHERE path=?",
                         (str(actual_subtitles), original_path))
        matching_movies = database.execute("SELECT radarrId FROM table_movies WHERE path=?", (original_path,))

        for movie in matching_movies:
            if movie:
                logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
                list_missing_subtitles_movies(no=movie['radarrId'])
            else:
                logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + reversed_path)

    return actual_subtitles


def list_missing_subtitles(no=None, epno=None, send_event=True):
    if epno is not None:
        episodes_subtitles_clause = " WHERE table_episodes.sonarrEpisodeId=" + str(epno)
    elif no is not None:
        episodes_subtitles_clause = " WHERE table_episodes.sonarrSeriesId=" + str(no)
    else:
        episodes_subtitles_clause = ""
    episodes_subtitles = database.execute("SELECT table_shows.sonarrSeriesId, table_episodes.sonarrEpisodeId, "
                                          "table_episodes.subtitles, table_shows.profileId, "
                                          "table_episodes.audio_language FROM table_episodes "
                                          "LEFT JOIN table_shows on table_episodes.sonarrSeriesId = "
                                          "table_shows.sonarrSeriesId" + episodes_subtitles_clause)
    if isinstance(episodes_subtitles, str):
        logging.error("BAZARR list missing subtitles query to DB returned this instead of rows: " + episodes_subtitles)
        return

    use_embedded_subs = settings.general.getboolean('use_embedded_subs')

    for episode_subtitles in episodes_subtitles:
        missing_subtitles_text = '[]'
        if episode_subtitles['profileId']:
            # get desired subtitles
            desired_subtitles_temp = get_profiles_list(profile_id=episode_subtitles['profileId'])
            desired_subtitles_list = []
            if desired_subtitles_temp:
                for language in desired_subtitles_temp['items']:
                    if language['audio_exclude'] == "True":
                        cutoff_lang_temp = get_profile_cutoff(profile_id=episode_subtitles['profileId'])
                        if cutoff_lang_temp:
                            if language_from_alpha2(cutoff_lang_temp[0]['language']) in ast.literal_eval(
                                    episode_subtitles['audio_language']):
                                desired_subtitles_list = []
                                break
                        if language_from_alpha2(language['language']) in ast.literal_eval(
                                episode_subtitles['audio_language']):
                            continue
                    desired_subtitles_list.append([language['language'], language['forced'], language['hi']])

            # get existing subtitles
            actual_subtitles_list = []
            if episode_subtitles['subtitles'] is not None:
                if use_embedded_subs:
                    actual_subtitles_temp = ast.literal_eval(episode_subtitles['subtitles'])
                else:
                    actual_subtitles_temp = [x for x in ast.literal_eval(episode_subtitles['subtitles']) if x[1]]

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
                    actual_subtitles_list.append([lang, str(forced), str(hi)])

            # check if cutoff is reached and skip any further check
            cutoff_met = False
            cutoff_temp_list = get_profile_cutoff(profile_id=episode_subtitles['profileId'])

            if cutoff_temp_list:
                for cutoff_temp in cutoff_temp_list:
                    cutoff_language = [cutoff_temp['language'], cutoff_temp['forced'], cutoff_temp['hi']]
                    if cutoff_language in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])
                    elif cutoff_language and [cutoff_language[0], 'True', 'False'] in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])
                    elif cutoff_language and [cutoff_language[0], 'False', 'True'] in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])

            if not cutoff_met:
                # if cutoff isn't met or None, we continue

                # get difference between desired and existing subtitles
                missing_subtitles_list = []
                for item in desired_subtitles_list:
                    if item not in actual_subtitles_list:
                        missing_subtitles_list.append(item)

                # remove missing that have forced or hi subtitles for this language in existing
                for item in actual_subtitles_list:
                    if item[1] == 'True' or item[2] == 'True':
                        try:
                            missing_subtitles_list.remove([item[0], 'False', 'False'])
                        except ValueError:
                            pass

                # make the missing languages list looks like expected
                missing_subtitles_output_list = []
                for item in missing_subtitles_list:
                    lang = item[0]
                    if item[1] == 'True':
                        lang += ':forced'
                    elif item[2] == 'True':
                        lang += ':hi'
                    missing_subtitles_output_list.append(lang)

                missing_subtitles_text = str(missing_subtitles_output_list)

        database.execute("UPDATE table_episodes SET missing_subtitles=? WHERE sonarrEpisodeId=?",
                         (missing_subtitles_text, episode_subtitles['sonarrEpisodeId']))

        if send_event:
            event_stream(type='episode', action='update', series=episode_subtitles['sonarrSeriesId'],
                         episode=episode_subtitles['sonarrEpisodeId'])
            event_stream(type='badges_series')


def list_missing_subtitles_movies(no=None, epno=None, send_event=True):
    if no is not None:
        movies_subtitles_clause = " WHERE radarrId=" + str(no)
    else:
        movies_subtitles_clause = ""

    movies_subtitles = database.execute("SELECT radarrId, subtitles, profileId, audio_language FROM table_movies" +
                                        movies_subtitles_clause)
    if isinstance(movies_subtitles, str):
        logging.error("BAZARR list missing subtitles query to DB returned this instead of rows: " + movies_subtitles)
        return


    use_embedded_subs = settings.general.getboolean('use_embedded_subs')

    for movie_subtitles in movies_subtitles:
        missing_subtitles_text = '[]'
        if movie_subtitles['profileId']:
            # get desired subtitles
            desired_subtitles_temp = get_profiles_list(profile_id=movie_subtitles['profileId'])
            desired_subtitles_list = []
            if desired_subtitles_temp:
                for language in desired_subtitles_temp['items']:
                    if language['audio_exclude'] == "True":
                        cutoff_lang_temp = get_profile_cutoff(profile_id=movie_subtitles['profileId'])
                        if cutoff_lang_temp:
                            if language_from_alpha2(cutoff_lang_temp[0]['language']) in ast.literal_eval(
                                    movie_subtitles['audio_language']):
                                desired_subtitles_list = []
                                break
                        if language_from_alpha2(language['language']) in ast.literal_eval(
                                movie_subtitles['audio_language']):
                            continue
                    desired_subtitles_list.append([language['language'], language['forced'], language['hi']])

            # get existing subtitles
            actual_subtitles_list = []
            if movie_subtitles['subtitles'] is not None:
                if use_embedded_subs:
                    actual_subtitles_temp = ast.literal_eval(movie_subtitles['subtitles'])
                else:
                    actual_subtitles_temp = [x for x in ast.literal_eval(movie_subtitles['subtitles']) if x[1]]

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
                    actual_subtitles_list.append([lang, str(forced), str(hi)])

            # check if cutoff is reached and skip any further check
            cutoff_met = False
            cutoff_temp_list = get_profile_cutoff(profile_id=movie_subtitles['profileId'])

            if cutoff_temp_list:
                for cutoff_temp in cutoff_temp_list:
                    cutoff_language = [cutoff_temp['language'], cutoff_temp['forced'], cutoff_temp['hi']]
                    if cutoff_language in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])
                    elif cutoff_language and [cutoff_language[0], 'True', 'False'] in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])
                    elif cutoff_language and [cutoff_language[0], 'False', 'True'] in actual_subtitles_list:
                        cutoff_met = True
                        missing_subtitles_text = str([])

            if not cutoff_met:
                # get difference between desired and existing subtitles
                missing_subtitles_list = []
                for item in desired_subtitles_list:
                    if item not in actual_subtitles_list:
                        missing_subtitles_list.append(item)

                # remove missing that have forced or hi subtitles for this language in existing
                for item in actual_subtitles_list:
                    if item[1] == 'True' or item[2] == 'True':
                        try:
                            missing_subtitles_list.remove([item[0], 'False', 'False'])
                        except ValueError:
                            pass

                # make the missing languages list looks like expected
                missing_subtitles_output_list = []
                for item in missing_subtitles_list:
                    lang = item[0]
                    if item[1] == 'True':
                        lang += ':forced'
                    elif item[2] == 'True':
                        lang += ':hi'
                    missing_subtitles_output_list.append(lang)

                missing_subtitles_text = str(missing_subtitles_output_list)

        database.execute("UPDATE table_movies SET missing_subtitles=? WHERE radarrId=?",
                         (missing_subtitles_text, movie_subtitles['radarrId']))

        if send_event:
            event_stream(type='movie', action='update', movie=movie_subtitles['radarrId'])
            event_stream(type='badges_movies')


def series_full_scan_subtitles():
    episodes = database.execute("SELECT path FROM table_episodes")

    for i, episode in enumerate(episodes, 1):
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))

    gc.collect()


def movies_full_scan_subtitles():
    movies = database.execute("SELECT path FROM table_movies")

    for i, movie in enumerate(movies, 1):
        store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))

    gc.collect()


def series_scan_subtitles(no):
    episodes = database.execute("SELECT path FROM table_episodes WHERE sonarrSeriesId=? ORDER BY sonarrEpisodeId",
                                (no,))

    for episode in episodes:
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))


def movies_scan_subtitles(no):
    movies = database.execute("SELECT path FROM table_movies WHERE radarrId=? ORDER BY radarrId", (no,))

    for movie in movies:
        store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))


def get_external_subtitles_path(file, subtitle):
    fld = os.path.dirname(file)

    if settings.general.subfolder == "current":
        path = os.path.join(fld, subtitle)
    elif settings.general.subfolder == "absolute":
        custom_fld = settings.general.subfolder_custom
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    elif settings.general.subfolder == "relative":
        custom_fld = os.path.join(fld, settings.general.subfolder_custom)
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    else:
        path = None

    return path


def guess_external_subtitles(dest_folder, subtitles):
    for subtitle, language in subtitles.items():
        if not language:
            subtitle_path = os.path.join(dest_folder, subtitle)
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                logging.debug("BAZARR falling back to file content analysis to detect language.")
                detected_language = None

                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > 1*1024*1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                    detected_language = guess_language(text)
                    #add simplified and traditional chinese detection
                    if detected_language == 'zh':
                        traditional_chinese_fuzzy = [u"繁", u"雙語"]
                        traditional_chinese = [".cht", ".tc", ".zh-tw", ".zht",".zh-hant",".zhhant",".zh_hant",".hant", ".big5", ".traditional"]
                        if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(traditional_chinese)) or (str(subtitle_path).lower())[:-5] in traditional_chinese_fuzzy:
                            detected_language == 'zt'
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except:
                            logging.debug(
                                "BAZARR skipping this subtitles because we can't decode the file using the "
                                "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue
                    detected_language = guess_language(text)
                except:
                    logging.debug('BAZARR was unable to detect encoding for this subtitles file: %r', subtitle_path)
                finally:
                    if detected_language:
                        logging.debug("BAZARR external subtitles detected and guessed this language: " + str(
                            detected_language))
                        try:
                            subtitles[subtitle] = Language.rebuild(Language.fromietf(detected_language), forced=False,
                                                                   hi=False)
                        except:
                            pass

        # If language is still None (undetected), skip it
        if not language:
            pass

        # Skip HI detection if forced
        elif language.forced:
            pass

        # Detect hearing-impaired external subtitles not identified in filename
        elif not subtitles[subtitle].hi:
            subtitle_path = os.path.join(dest_folder, subtitle)

            # check if file exist:
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > 1 * 1024 * 1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except:
                            logging.debug("BAZARR skipping this subtitles because we can't decode the file using the "
                                          "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue

                if bool(re.search(hi_regex, text)):
                    subtitles[subtitle] = Language.rebuild(subtitles[subtitle], forced=False, hi=True)
    return subtitles
