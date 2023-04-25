# coding=utf-8

import operator

from functools import reduce
from flask_restx import Resource, Namespace, fields

from app.database import get_exclusion_clause, TableEpisodes, TableShows, TableMovies, database, select
from app.get_providers import get_throttled_providers
from app.signalr_client import sonarr_signalr_client, radarr_signalr_client
from app.announcements import get_all_announcements
from utilities.health import get_health_issues

from ..utils import authenticate

api_ns_badges = Namespace('Badges', description='Get badges count to update the UI (episodes and movies wanted '
                                                'subtitles, providers with issues, health issues and announcements.')


@api_ns_badges.route('badges')
class Badges(Resource):
    get_model = api_ns_badges.model('BadgesGet', {
        'episodes': fields.Integer(),
        'movies': fields.Integer(),
        'providers': fields.Integer(),
        'status': fields.Integer(),
        'sonarr_signalr': fields.String(),
        'radarr_signalr': fields.String(),
        'announcements': fields.Integer(),
    })

    @authenticate
    @api_ns_badges.marshal_with(get_model, code=200)
    @api_ns_badges.response(401, 'Not Authenticated')
    @api_ns_badges.doc(parser=None)
    def get(self):
        """Get badges count to update the UI"""
        episodes_conditions = [(TableEpisodes.missing_subtitles.is_not(None)),
                               (TableEpisodes.missing_subtitles != '[]')]
        episodes_conditions += get_exclusion_clause('series')
        missing_episodes = database.execute(
            select(TableShows.tags,
                   TableShows.seriesType,
                   TableEpisodes.monitored)
            .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
            .where(reduce(operator.and_, episodes_conditions))) \
            .all()

        movies_conditions = [(TableMovies.missing_subtitles.is_not(None)),
                             (TableMovies.missing_subtitles != '[]')]
        movies_conditions += get_exclusion_clause('movie')
        missing_movies = database.execute(
            select(TableMovies.tags, TableMovies.monitored)
            .where(reduce(operator.and_, movies_conditions)))\
            .all()

        throttled_providers = len(get_throttled_providers())

        health_issues = len(get_health_issues())

        result = {
            "episodes": len(missing_episodes),
            "movies": len(missing_movies),
            "providers": throttled_providers,
            "status": health_issues,
            'sonarr_signalr': "LIVE" if sonarr_signalr_client.connected else "",
            'radarr_signalr': "LIVE" if radarr_signalr_client.connected else "",
            'announcements': len(get_all_announcements()),
        }
        return result
