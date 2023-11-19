# coding=utf-8

import os
import logging

from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableShows, TableEpisodes, get_audio_profile_languages, get_profile_id, database, select
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.download import generate_subtitles
from subtitles.tools.delete import delete_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from subtitles.indexer.series import store_subtitles
from app.event_handler import event_stream, show_message
from app.config import settings

from ..utils import authenticate

api_ns_episodes_subtitles = Namespace('Episodes Subtitles', description='Download, upload or delete episodes subtitles')


@api_ns_episodes_subtitles.route('episodes/subtitles')
class EpisodesSubtitles(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('seriesid', type=int, required=True, help='Series ID')
    patch_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    patch_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')

    @authenticate
    @api_ns_episodes_subtitles.doc(parser=patch_request_parser)
    @api_ns_episodes_subtitles.response(204, 'Success')
    @api_ns_episodes_subtitles.response(401, 'Not Authenticated')
    @api_ns_episodes_subtitles.response(404, 'Episode not found')
    @api_ns_episodes_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_episodes_subtitles.response(500, 'Custom error messages')
    def patch(self):
        """Download an episode subtitles"""
        args = self.patch_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = database.execute(
            select(TableEpisodes.path,
                   TableEpisodes.sceneName,
                   TableEpisodes.audio_language,
                   TableShows.title)
            .select_from(TableEpisodes)
            .join(TableShows)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        episodePath = path_mappings.path_replace(episodeInfo.path)

        if not os.path.exists(episodePath):
            return 'Episode file not found. Path mapping issue?', 500

        sceneName = episodeInfo.sceneName or "None"

        title = episodeInfo.title

        language = args.get('language')
        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()
        if hi == 'True':
            language_str = f'{language}:hi'
        elif forced == 'True':
            language_str = f'{language}:forced'
        else:
            language_str = language

        audio_language_list = get_audio_profile_languages(episodeInfo.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = list(generate_subtitles(episodePath, [(language, hi, forced)], audio_language, sceneName,
                                             title, 'series', profile_id=get_profile_id(episode_id=sonarrEpisodeId)))
            if isinstance(result, list) and len(result):
                result = result[0]
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                history_log(1, sonarrSeriesId, sonarrEpisodeId, result)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, result.message)
                store_subtitles(result.path, episodePath)
            else:
                event_stream(type='episode', payload=sonarrEpisodeId)
                show_message(f'No {language_str.upper()} subtitles found')
                return '', 204
        except OSError:
            return 'Unable to save subtitles file. Permission or path mapping issue?', 409
        else:
            return '', 204

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('seriesid', type=int, required=True, help='Series ID')
    post_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    post_request_parser.add_argument('file', type=FileStorage, location='files', required=True,
                                     help='Subtitles file as file upload object')

    @authenticate
    @api_ns_episodes_subtitles.doc(parser=post_request_parser)
    @api_ns_episodes_subtitles.response(204, 'Success')
    @api_ns_episodes_subtitles.response(401, 'Not Authenticated')
    @api_ns_episodes_subtitles.response(404, 'Episode not found')
    @api_ns_episodes_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_episodes_subtitles.response(500, 'Episode file not found. Path mapping issue?')
    def post(self):
        """Upload an episode subtitles"""
        args = self.post_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = database.execute(
            select(TableEpisodes.path,
                   TableEpisodes.audio_language)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        episodePath = path_mappings.path_replace(episodeInfo.path)

        if not os.path.exists(episodePath):
            return 'Episode file not found. Path mapping issue?', 500

        audio_language = get_audio_profile_languages(episodeInfo.audio_language)
        if len(audio_language) and isinstance(audio_language[0], dict):
            audio_language = audio_language[0]
        else:
            audio_language = {'name': '', 'code2': '', 'code3': ''}

        language = args.get('language')
        forced = True if args.get('forced') == 'true' else False
        hi = True if args.get('hi') == 'true' else False
        subFile = args.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=episodePath,
                                            language=language,
                                            forced=forced,
                                            hi=hi,
                                            media_type='series',
                                            subtitle=subFile,
                                            audio_language=audio_language)

            if not result:
                logging.debug(f"BAZARR unable to process subtitles for this episode: {episodePath}")
            else:
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                provider = "manual"
                score = 360
                history_log(4, sonarrSeriesId, sonarrEpisodeId, result, fake_provider=provider, fake_score=score)
                if not settings.general.dont_notify_manual_actions:
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, result.message)
                store_subtitles(result.path, episodePath)
        except OSError:
            return 'Unable to save subtitles file. Permission or path mapping issue?', 409
        else:
            return '', 204

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('seriesid', type=int, required=True, help='Series ID')
    delete_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')
    delete_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    delete_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    delete_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    delete_request_parser.add_argument('path', type=str, required=True, help='Path of the subtitles file')

    @authenticate
    @api_ns_episodes_subtitles.doc(parser=delete_request_parser)
    @api_ns_episodes_subtitles.response(204, 'Success')
    @api_ns_episodes_subtitles.response(401, 'Not Authenticated')
    @api_ns_episodes_subtitles.response(404, 'Episode not found')
    @api_ns_episodes_subtitles.response(500, 'Subtitles file not found or permission issue.')
    def delete(self):
        """Delete an episode subtitles"""
        args = self.delete_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = database.execute(
            select(TableEpisodes.path)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        episodePath = path_mappings.path_replace(episodeInfo.path)

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse(subtitlesPath)

        if delete_subtitles(media_type='series',
                            language=language,
                            forced=forced,
                            hi=hi,
                            media_path=episodePath,
                            subtitles_path=subtitlesPath,
                            sonarr_series_id=sonarrSeriesId,
                            sonarr_episode_id=sonarrEpisodeId):
            return '', 204
        else:
            return 'Subtitles file not found or permission issue.', 500
