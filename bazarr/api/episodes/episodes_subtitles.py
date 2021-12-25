# coding=utf-8

import os

from flask import request
from flask_restful import Resource
from subliminal_patch.core import SUBTITLE_EXTENSIONS

from database import TableEpisodes, get_audio_profile_languages, get_profile_id
from ..utils import authenticate
from get_providers import get_providers, get_providers_auth
from get_subtitle import download_subtitle, manual_upload_subtitle
from utils import history_log, delete_subtitles
from notifier import send_notifications
from list_subtitles import store_subtitles
from event_handler import event_stream
from config import settings


# PATCH: Download Subtitles
# POST: Upload Subtitles
# DELETE: Delete Subtitles
class EpisodesSubtitles(Resource):
    @authenticate
    def patch(self):
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.episodeId == episodeId)\
            .dicts()\
            .get()

        title = episodeInfo['title']
        episodePath = episodeInfo['path']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(episode_id=episodeId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = download_subtitle(episodePath, language, audio_language, hi, forced, providers_list,
                                       providers_auth, title, 'series',
                                       profile_id=get_profile_id(episode_id=episodeId))
            if result is not None:
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
                history_log(1, seriesId, episodeId, message, path, language_code, provider, score, subs_id,
                            subs_path)
                send_notifications(seriesId, episodeId, message)
                store_subtitles(episodePath)
            else:
                event_stream(type='episode', payload=episodeId)

        except OSError:
            pass

        return '', 204

    @authenticate
    def post(self):
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.episodeId == episodeId)\
            .dicts()\
            .get()

        title = episodeInfo['title']
        episodePath = episodeInfo['path']
        audio_language = episodeInfo['audio_language']

        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'true' else False
        hi = True if request.form.get('hi') == 'true' else False
        subFile = request.files.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=episodePath,
                                            language=language,
                                            forced=forced,
                                            hi=hi,
                                            title=title,
                                            media_type='series',
                                            subtitle=subFile,
                                            audio_language=audio_language)

            if result is not None:
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
                history_log(4, seriesId, episodeId, message, path, language_code, provider, score,
                            subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(seriesId, episodeId, message)
                store_subtitles(episodePath)

        except OSError:
            pass

        return '', 204

    @authenticate
    def delete(self):
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.episodeId == episodeId)\
            .dicts()\
            .get()

        episodePath = episodeInfo['path']

        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('path')

        delete_subtitles(media_type='series',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=episodePath,
                         subtitles_path=subtitlesPath,
                         series_id=seriesId,
                         episode_id=episodeId)

        return '', 204
