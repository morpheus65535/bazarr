# coding=utf-8

import gc
import os
import logging

from subliminal_patch import core, search_external_subtitles

from languages.custom_lang import CustomLanguage
from app.database import get_profiles_list, get_profile_cutoff, TableEpisodes, TableShows, TableEpisodesSubtitles, \
    get_audio_profile_languages, database, update, select, get_subtitles, insert, delete
from languages.get_languages import alpha2_from_alpha3, get_language_set
from app.config import settings
from utilities.helper import get_subtitle_destination_folder
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_subs_reader
from app.event_handler import event_stream
from subtitles.indexer.utils import guess_external_subtitles, get_external_subtitles_path
from app.jobs_queue import jobs_queue

gc.enable()


def store_subtitles(sonarr_episode_id, use_cache=True):
    item = database.execute(
        select(TableEpisodes.sonarrSeriesId,
               TableEpisodes.path,
               TableEpisodes.episode_file_id,
               TableEpisodes.file_size)
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)
    ).first()

    if not item:
        logging.warning(f"BAZARR could not find episode with ID {sonarr_episode_id} in the database.")
        return
    else:
        original_path = item.path
        mapped_path = path_mappings.path_replace(original_path)

    logging.debug(f'BAZARR started subtitles indexing for this file: {mapped_path}')
    embedded_subtitles = []
    external_subtitles = []

    if os.path.exists(mapped_path):
        if settings.general.use_embedded_subs:
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                # Get all embedded subtitles
                subtitle_languages = embedded_subs_reader(mapped_path,
                                                          file_size=item.file_size,
                                                          episode_file_id=item.episode_file_id,
                                                          use_cache=use_cache)
                for track_id, subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        # Skip subtitles track using codecs that the user doesn't want to index
                        if (settings.general.ignore_pgs_subs and subtitle_codec.lower() == "pgs") or \
                                (settings.general.ignore_vobsub_subs and subtitle_codec.lower() ==
                                 "vobsub") or \
                                (settings.general.ignore_ass_subs and subtitle_codec.lower() ==
                                 "ass"):
                            logging.debug(f"BAZARR skipping {subtitle_codec} sub for language: "
                                          f"{alpha2_from_alpha3(subtitle_language)}")
                            continue

                        # Index embedded subtitles with defined and supported language
                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = alpha2_from_alpha3(subtitle_language)
                            logging.debug(f"BAZARR embedded subtitles detected: {lang}"
                                          f"{':forced' if subtitle_forced else ''}{':hi' if subtitle_hi else ''}")
                            embedded_subtitles.append({'sonarrSeriesId': item.sonarrSeriesId,
                                                       'sonarrEpisodeId': sonarr_episode_id,
                                                       'language': lang,
                                                       'forced': subtitle_forced,
                                                       'hi': subtitle_hi,
                                                       'embedded_track_id': track_id})
                    except Exception as error:
                        logging.debug(f"BAZARR unable to index this unrecognized language: {subtitle_language} "
                                      f"({error})")

                database.execute(
                    # Delete prior indexed embedded subtitles lacking track ID
                    delete(TableEpisodesSubtitles)
                    .where(TableEpisodesSubtitles.sonarrSeriesId == item.sonarrSeriesId)
                    .where(TableEpisodesSubtitles.sonarrEpisodeId == sonarr_episode_id)
                    .where(TableEpisodesSubtitles.path.is_(None))
                    .where(TableEpisodesSubtitles.embedded_track_id.is_(None))
                )
                if len(embedded_subtitles):
                    # Insert new embedded subtitles or update existing ones
                    embedded_stmt = insert(TableEpisodesSubtitles).values(embedded_subtitles)
                    embedded_stmt = embedded_stmt.on_conflict_do_update(
                        index_elements=['embedded_track_id', 'sonarrSeriesId', 'sonarrEpisodeId', 'language',
                                        'forced', 'hi'],
                        set_={
                            'language': embedded_stmt.excluded.language,
                            'forced': embedded_stmt.excluded.forced,
                            'hi': embedded_stmt.excluded.hi,
                            'size': embedded_stmt.excluded.size,
                            'embedded_track_id': embedded_stmt.excluded.embedded_track_id
                        },
                        index_where=TableEpisodesSubtitles.path.is_(None)
                    )
                    database.execute(embedded_stmt)

                    # Delete prior indexed embedded subtitles that don't exist anymore
                    embedded_subtitles_id_list = [x['embedded_track_id'] for x in embedded_subtitles]
                    if len(embedded_subtitles_id_list):
                        database.execute(
                            delete(TableEpisodesSubtitles)
                            .where(TableEpisodesSubtitles.sonarrEpisodeId == sonarr_episode_id)
                            .where(TableEpisodesSubtitles.path.is_(None))
                            .where(TableEpisodesSubtitles.embedded_track_id.not_in(embedded_subtitles_id_list))
                        )
            except Exception:
                logging.exception(f"BAZARR error when trying to analyze this {os.path.splitext(mapped_path)[1]} file: "
                                  f"{mapped_path}")
                pass

        try:
            dest_folder = get_subtitle_destination_folder()
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []

            # Get previously indexed subtitles that haven't changed:
            previously_indexed_subtitles = get_subtitles(sonarr_episode_id=sonarr_episode_id)
            previously_indexed_subtitles_to_exclude = \
                [x for x in previously_indexed_subtitles
                 if x['path'] and
                 os.path.isfile(x['path']) and
                 os.stat(x['path']).st_size == x['file_size']]

            # Get previously indexed subtitles that no longer exist:
            previously_indexed_subtitles_to_delete = \
                [path_mappings.path_replace_reverse(x['path']) for x in previously_indexed_subtitles
                 if x['path'] and not os.path.isfile(x['path'])]

            if previously_indexed_subtitles_to_delete:
                database.execute(
                    delete(TableEpisodesSubtitles)
                    .where(TableEpisodesSubtitles.path.in_(previously_indexed_subtitles_to_delete)))

            # Search for external subtitles:
            subtitles = search_external_subtitles(mapped_path, languages=get_language_set(),
                                                  only_one=settings.general.single_language)
            full_dest_folder_path = os.path.dirname(mapped_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(mapped_path), dest_folder)

            # Guess external subtitles language if not specified in the file name:
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles,
                                                 previously_indexed_subtitles_to_exclude)
        except Exception as e:
            logging.exception(f"BAZARR unable to index external subtitles for this file {mapped_path}: {repr(e)}")
        else:
            # For each external subtitle, store it in the database
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

                subtitle_path = get_external_subtitles_path(mapped_path, subtitle)

                # We get custom language external subtitles
                try:
                    subtitle_size = os.stat(subtitle_path).st_size
                except FileNotFoundError:
                    logging.debug(f"BAZARR skipping missing subtitle file: {subtitle_path}")
                    continue

                custom = CustomLanguage.found_external(subtitle, subtitle_path)
                if custom is not None:
                    logging.debug(f"BAZARR external subtitles detected: {custom}")
                    external_subtitles.append({'sonarrSeriesId': item.sonarrSeriesId,
                                               'sonarrEpisodeId': sonarr_episode_id,
                                               'language': custom.split(':')[0],
                                               'forced': custom.endswith(':forced'),
                                               'hi': custom.endswith(':hi'),
                                               'path': path_mappings.path_replace_reverse(subtitle_path),
                                               'size': subtitle_size})

                # We get defined and supported language external subtitles
                elif str(language.basename) != 'und':
                    logging.debug(f"BAZARR external subtitles detected: {language}"
                                  f"{':forced' if language.forced else ''}"
                                  f"{':hi' if language.hi else ''}")
                    external_subtitles.append({'sonarrSeriesId': item.sonarrSeriesId,
                                               'sonarrEpisodeId': sonarr_episode_id,
                                               'language': language.basename,
                                               'forced': language.forced,
                                               'hi': language.hi,
                                               'path': path_mappings.path_replace_reverse(subtitle_path),
                                               'size': subtitle_size})

            # We store external subtitles in the database or update existing ones
            if len(external_subtitles):
                stmt = insert(TableEpisodesSubtitles).values(external_subtitles)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['path', 'sonarrSeriesId', 'sonarrEpisodeId', 'language', 'forced', 'hi'],
                    set_={
                        'language': stmt.excluded.language,
                        'forced': stmt.excluded.forced,
                        'hi': stmt.excluded.hi,
                        'size': stmt.excluded.size
                    }
                )
                database.execute(stmt)
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
        return

    # We store actual subtitles for this episode in the database
    logging.debug(f"BAZARR has stored those languages to DB: {embedded_subtitles + external_subtitles}")

    # We list missing subtitles for this episode and store them in the database
    list_missing_subtitles(epno=sonarr_episode_id)

    logging.debug(f'BAZARR ended subtitles indexing for this file: {mapped_path}')


def list_missing_subtitles(no=None, epno=None):
    stmt = select(TableShows.sonarrSeriesId,
                  TableEpisodes.sonarrEpisodeId,
                  TableShows.profileId,
                  TableEpisodes.audio_language) \
        .select_from(TableEpisodes) \
        .join(TableShows)

    if epno is not None:
        episodes_subtitles = database.execute(stmt.where(TableEpisodes.sonarrEpisodeId == epno)).all()
    elif no is not None:
        episodes_subtitles = database.execute(stmt.where(TableEpisodes.sonarrSeriesId == no)).all()
    else:
        episodes_subtitles = database.execute(stmt).all()

    use_embedded_subs = settings.general.use_embedded_subs

    matches_audio = lambda language: any(x['code2'] == language['language'] for x in get_audio_profile_languages(
                                episode_subtitles.audio_language))

    for episode_subtitles in episodes_subtitles:
        missing_subtitles_text = '[]'
        if episode_subtitles.profileId:
            # get desired subtitles
            desired_subtitles_temp = get_profiles_list(profile_id=episode_subtitles.profileId)
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
                                                   'forced': str(language['forced']),
                                                   'hi': str(language['hi'])})

            # get existing subtitles
            actual_subtitles_list = []
            actual_subtitles_temp = get_subtitles(sonarr_episode_id=episode_subtitles.sonarrEpisodeId)
            if not use_embedded_subs:
                actual_subtitles_temp = [x for x in actual_subtitles_temp if x['path']]

            for subtitles in actual_subtitles_temp:
                actual_subtitles_list.append({'language': subtitles['code2'],
                                              'forced': str(subtitles['forced']),
                                              'hi': str(subtitles['hi'])})

            # check if cutoff is reached and skip any further check
            cutoff_met = False
            cutoff_temp_list = get_profile_cutoff(profile_id=episode_subtitles.profileId)

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
                # if cutoff isn't met or None, we continue

                # get difference between desired and existing subtitles
                missing_subtitles_list = []
                for item in desired_subtitles_list:
                    if item not in actual_subtitles_list:
                        missing_subtitles_list.append(item)

                # remove missing that have hi subtitles for this language in existing
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
            update(TableEpisodes)
            .values(missing_subtitles=missing_subtitles_text)
            .where(TableEpisodes.sonarrEpisodeId == episode_subtitles.sonarrEpisodeId))

        event_stream(type='episode', payload=episode_subtitles.sonarrEpisodeId)
        event_stream(type='episode-wanted', action='update', payload=episode_subtitles.sonarrEpisodeId)
    event_stream(type='badges')


def series_full_scan_subtitles(job_id=None, use_cache=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Indexing all existing episodes subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    if use_cache is None:
        use_cache = settings.sonarr.use_ffprobe_cache

    episodes = database.execute(
        select(TableEpisodes.path,
               TableShows.title,
               TableEpisodes.title.label("episodeTitle"),
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.sonarrEpisodeId)
        .select_from(TableEpisodes)
        .join(TableShows)
    ).all()

    jobs_queue.update_job_progress(job_id=job_id, progress_max=len(episodes), progress_message='Indexing')
    for i, episode in enumerate(episodes, start=1):
        jobs_queue.update_job_progress(
            job_id=job_id, progress_value=i,
            progress_message=f"{episode.title} - S{episode.season:02d}E{episode.episode:02d} - {episode.episodeTitle}")
        store_subtitles(episode.sonarrEpisodeId, use_cache=use_cache)

    logging.info('BAZARR All existing episode subtitles indexed from disk.')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Indexed all existing series subtitles")

    gc.collect()


def series_scan_subtitles(no):
    episodes = database.execute(
        select(TableEpisodes.sonarrEpisodeId)
        .where(TableEpisodes.sonarrSeriesId == no)
        .order_by(TableEpisodes.sonarrEpisodeId))\
        .all()

    for episode in episodes:
        store_subtitles(episode.sonarrEpisodeId, use_cache=False)
