# coding=utf-8

import operator
import ast

from functools import reduce
from flask_restx import Resource, Namespace, fields, marshal

from app.database import (get_exclusion_clause, TableEpisodes, TableShows, TableMovies, TableSportsEvents,
                          TableSportsLeagues, database, select)
from app.config import settings

from app.get_providers import get_throttled_providers
from app.signalr_client import sonarr_signalr_client, radarr_signalr_client
from sportarr.sse_client import sportarr_sse_client
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
        'sports': fields.Integer(),
        'providers': fields.Integer(),
        'status': fields.Integer(),
        'sonarr_signalr': fields.String(),
        'radarr_signalr': fields.String(),
        'sportarr_sse': fields.String(),
        'announcements': fields.Integer(),
    })

    @authenticate
    @api_ns_badges.response(401, 'Not Authenticated')
    @api_ns_badges.doc(parser=None)
    def get(self):
        """Get badges count to update the UI"""
        episodes_conditions = [(TableEpisodes.missing_subtitles.is_not(None)),
                               (TableEpisodes.missing_subtitles != '[]')]
        episodes_conditions += get_exclusion_clause('series')
        missing_episodes = database.execute(
            select(TableEpisodes.missing_subtitles)
            .select_from(TableEpisodes)
            .join(TableShows)
            .where(reduce(operator.and_, episodes_conditions))) \
            .all()
        missing_episodes_count = 0
        for episode in missing_episodes:
            missing_episodes_count += len(ast.literal_eval(episode.missing_subtitles))

        movies_conditions = [(TableMovies.missing_subtitles.is_not(None)),
                             (TableMovies.missing_subtitles != '[]')]
        movies_conditions += get_exclusion_clause('movie')
        missing_movies = database.execute(
            select(TableMovies.missing_subtitles)
            .select_from(TableMovies)
            .where(reduce(operator.and_, movies_conditions))) \
            .all()
        missing_movies_count = 0
        for movie in missing_movies:
            missing_movies_count += len(ast.literal_eval(movie.missing_subtitles))

        # Counted per playable file, because a sports row is one part. An event
        # with two parts wants subtitles for both.
        sports_conditions = [(TableSportsEvents.missing_subtitles.is_not(None)),
                             (TableSportsEvents.missing_subtitles != '[]')]
        sports_conditions += get_exclusion_clause('sports')
        missing_sports = database.execute(
            select(TableSportsEvents.missing_subtitles)
            .select_from(TableSportsEvents)
            .join(TableSportsLeagues)
            .where(reduce(operator.and_, sports_conditions))) \
            .all()
        missing_sports_count = 0
        for event in missing_sports:
            missing_sports_count += len(ast.literal_eval(event.missing_subtitles))

        throttled_providers = len(get_throttled_providers())

        health_issues = len(get_health_issues())

        live_str = "LIVE" if settings.general.show_live_badge else ""

        result = {
            "episodes": missing_episodes_count,
            "movies": missing_movies_count,
            "sports": missing_sports_count,
            "providers": throttled_providers,
            "status": health_issues,
            'sonarr_signalr': live_str if sonarr_signalr_client.connected else "DOWN",
            'radarr_signalr': live_str if radarr_signalr_client.connected else "DOWN",
            'sportarr_sse': live_str if sportarr_sse_client.connected else "DOWN",
            'announcements': len(get_all_announcements()),
        }
        return marshal(result, self.get_model)
