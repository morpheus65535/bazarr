# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableEpisodes, TableShows, get_audio_profile_languages, get_profile_id, database, select
from utilities.path_mappings import path_mappings
from app.get_providers import get_providers
from subtitles.manual import manual_search, manual_download_subtitle
from sonarr.history import history_log
from app.config import settings
from app.notifier import send_notifications
from subtitles.indexer.series import store_subtitles

from ..utils import authenticate

api_ns_providers_episodes = Namespace('Providers Episodes', description='List and download episodes subtitles manually')


@api_ns_providers_episodes.route('providers/episodes')
class ProviderEpisodes(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')

    get_response_model = api_ns_providers_episodes.model('ProviderEpisodesGetResponse', {
        'dont_matches': fields.List(fields.String),
        'forced': fields.String(),
        'hearing_impaired': fields.String(),
        'language': fields.String(),
        'matches': fields.List(fields.String),
        'original_format': fields.String(),
        'orig_score': fields.Integer(),
        'provider': fields.String(),
        'release_info': fields.List(fields.String),
        'score': fields.Integer(),
        'score_without_hash': fields.Integer(),
        'subtitle': fields.String(),
        'uploader': fields.String(),
        'url': fields.String(),
    })

    @authenticate
    @api_ns_providers_episodes.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_providers_episodes.response(401, 'Not Authenticated')
    @api_ns_providers_episodes.response(404, 'Episode not found')
    @api_ns_providers_episodes.doc(parser=get_request_parser)
    def get(self):
        """Search manually for an episode subtitles"""
        args = self.get_request_parser.parse_args()
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = database.execute(
            select(TableEpisodes.path,
                   TableEpisodes.sceneName,
                   TableShows.title,
                   TableShows.profileId)
            .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        title = episodeInfo.title
        episodePath = path_mappings.path_replace(episodeInfo.path)
        sceneName = episodeInfo.sceneName or "None"
        profileId = episodeInfo.profileId

        providers_list = get_providers()

        data = manual_search(episodePath, profileId, providers_list, sceneName, title, 'series')
        if not data:
            data = []
        return data

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('seriesid', type=int, required=True, help='Series ID')
    post_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI subtitles from ["True", "False"]')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced subtitles from ["True", "False"]')
    post_request_parser.add_argument('original_format', type=str, required=True,
                                     help='Use original subtitles format from ["True", "False"]')
    post_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    post_request_parser.add_argument('subtitle', type=str, required=True, help='Pickled subtitles as return by GET')

    @authenticate
    @api_ns_providers_episodes.doc(parser=post_request_parser)
    @api_ns_providers_episodes.response(204, 'Success')
    @api_ns_providers_episodes.response(401, 'Not Authenticated')
    @api_ns_providers_episodes.response(404, 'Episode not found')
    def post(self):
        """Manually download an episode subtitles"""
        args = self.post_request_parser.parse_args()
        sonarrSeriesId = args.get('seriesid')
        sonarrEpisodeId = args.get('episodeid')
        episodeInfo = database.execute(
            select(
                TableEpisodes.audio_language,
                TableEpisodes.path,
                TableEpisodes.sceneName,
                TableShows.title)
            .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        title = episodeInfo.title
        episodePath = path_mappings.path_replace(episodeInfo.path)
        sceneName = episodeInfo.sceneName or "None"

        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()
        use_original_format = args.get('original_format').capitalize()
        selected_provider = args.get('provider')
        subtitle = args.get('subtitle')

        audio_language_list = get_audio_profile_languages(episodeInfo.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(episodePath, audio_language, hi, forced, subtitle, selected_provider,
                                              sceneName, title, 'series', use_original_format,
                                              profile_id=get_profile_id(episode_id=sonarrEpisodeId))
            if result:
                history_log(2, sonarrSeriesId, sonarrEpisodeId, result)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, result.message)
                store_subtitles(result.path, episodePath)
        except OSError:
            pass

        return '', 204
