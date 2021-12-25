# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from database import TableEpisodes, TableShows, get_audio_profile_languages, get_profile_id
from get_providers import get_providers, get_providers_auth
from get_subtitle import manual_search, manual_download_subtitle
from utils import history_log
from config import settings
from notifier import send_notifications
from list_subtitles import store_subtitles

from ..utils import authenticate


class ProviderEpisodes(Resource):
    @authenticate
    def get(self):
        # Manual Search
        episodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableShows.profileId) \
            .join(TableShows) \
            .where(TableEpisodes.episodeId == episodeId) \
            .dicts() \
            .get()

        title = episodeInfo['title']
        episodePath = episodeInfo['path']
        profileId = episodeInfo['profileId']

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(episodePath, profileId, providers_list, providers_auth, title, 'series')
        if not data:
            data = []
        return jsonify(data=data)

    @authenticate
    def post(self):
        # Manual Download
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path) \
            .where(TableEpisodes.episodeId == episodeId) \
            .dicts() \
            .get()

        title = episodeInfo['title']
        episodePath = episodeInfo['path']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')
        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(episode_id=episodeId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(episodePath, language, audio_language, hi, forced, subtitle,
                                              selected_provider, providers_auth, title, 'series',
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
                history_log(2, seriesId, episodeId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(seriesId, episodeId, message)
                store_subtitles(episodePath)
            return result, 201
        except OSError:
            pass

        return '', 204
