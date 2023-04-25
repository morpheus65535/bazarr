# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from app.config import settings
from app.database import TableShows, TableMovies, database, select

from ..utils import authenticate

api_ns_system_searches = Namespace('System Searches', description='Search for series or movies by name')


@api_ns_system_searches.route('system/searches')
class Searches(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('query', type=str, required=True, help='Series or movie name to search for')

    @authenticate
    @api_ns_system_searches.doc(parser=get_request_parser)
    @api_ns_system_searches.response(200, 'Success')
    @api_ns_system_searches.response(401, 'Not Authenticated')
    def get(self):
        """List results from query"""
        args = self.get_request_parser.parse_args()
        query = f"%{args.get('query')}%"
        search_list = []

        if query:
            if settings.general.getboolean('use_sonarr'):
                # Get matching series
                search_list += [{
                    'title': x.title,
                    'sonarrSeriesId': x.sonarrSeriesId,
                    'year': x.year,
                } for x in database.execute(
                    select(TableShows.title,
                           TableShows.sonarrSeriesId,
                           TableShows.year)
                    .where(TableShows.title.ilike(query))
                    .order_by(TableShows.title))
                    .all()]

            if settings.general.getboolean('use_radarr'):
                # Get matching movies
                search_list += [{
                    'title': x.title,
                    'radarrId': x.radarrId,
                    'year': x.year,
                } for x in database.execute(
                    select(TableMovies.title,
                           TableMovies.radarrId,
                           TableMovies.year)
                    .where(TableMovies.title.ilike(query))
                    .order_by(TableMovies.title))
                    .all()]

        return search_list
