# coding=utf-8

import os
import logging

from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableShows, TableEpisodes, get_audio_profile_languages, get_profile_id
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.download import generate_subtitles
from subtitles.tools.delete import delete_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from subtitles.indexer.series import store_subtitles
from app.event_handler import event_stream
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
    def patch(self):
        """Download an episode subtitles"""
        args = self.patch_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = TableEpisodes.select(
            TableEpisodes.path,
            TableEpisodes.sceneName,
            TableEpisodes.audio_language,
            TableShows.title) \
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId) \
            .dicts() \
            .get_or_none()

        if not episodeInfo:
            return 'Episode not found', 404

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['sceneName'] or "None"

        language = args.get('language')
        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()

        audio_language_list = get_audio_profile_languages(episodeInfo["audio_language"])
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = list(generate_subtitles(episodePath, [(language, hi, forced)], audio_language, sceneName,
                                             title, 'series', profile_id=get_profile_id(episode_id=sonarrEpisodeId)))
            if result:
                result = result[0]
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
                history_log(1, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id,
                            subs_path)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            else:
                event_stream(type='episode', payload=sonarrEpisodeId)

        except OSError:
            pass

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
    def post(self):
        """Upload an episode subtitles"""
        args = self.post_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.sceneName,
                                           TableEpisodes.audio_language) \
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId) \
            .dicts() \
            .get_or_none()

        if not episodeInfo:
            return 'Episode not found', 404

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['sceneName'] or "None"
        audio_language = episodeInfo['audio_language']

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
                                            title=title,
                                            sceneName=sceneName,
                                            media_type='series',
                                            subtitle=subFile,
                                            audio_language=audio_language)

            if not result:
                logging.debug(f"BAZARR unable to process subtitles for this episode: {episodePath}")
            else:
                message = result[0]
                path = result[1]
                subs_path = result[2]
                if hi:
                    language_code = language + ":hi"
                elif forced:
                    language_code = language + ":forced"
                else:
                    language_code = language
                provider = "manual"
                score = 360
                history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score,
                            subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)

        except OSError:
            pass

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
    def delete(self):
        """Delete an episode subtitles"""
        args = self.delete_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.sceneName,
                                           TableEpisodes.audio_language) \
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId) \
            .dicts() \
            .get_or_none()

        if not episodeInfo:
            return 'Episode not found', 404

        episodePath = path_mappings.path_replace(episodeInfo['path'])

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse(subtitlesPath)

        delete_subtitles(media_type='series',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=episodePath,
                         subtitles_path=subtitlesPath,
                         sonarr_series_id=sonarrSeriesId,
                         sonarr_episode_id=sonarrEpisodeId)

        return '', 204
