# coding=utf-8

from flask_restx import Resource, Namespace, reqparse
from unidecode import unidecode

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
        query = unidecode(args.get('query')).lower()
        search_list = []

        if query:
            if settings.general.use_sonarr:
                # Get matching series
                search_list += database.execute(
                    select(TableShows.title,
                           TableShows.sonarrSeriesId,
                           TableShows.year)
                    .order_by(TableShows.title)) \
                    .all()

            if settings.general.use_radarr:
                # Get matching movies
                search_list += database.execute(
                    select(TableMovies.title,
                           TableMovies.radarrId,
                           TableMovies.year)
                    .order_by(TableMovies.title)) \
                    .all()

        results = []

        for x in search_list:
            if query in unidecode(x.title).lower():
                result = {
                    'title': x.title,
                    'year': x.year,
                }

                if hasattr(x, 'sonarrSeriesId'):
                    result['sonarrSeriesId'] = x.sonarrSeriesId
                else:
                    result['radarrId'] = x.radarrId

                results.append(result)

        return results
