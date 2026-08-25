# coding=utf-8

import os

from io import BytesIO
from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableSportsEvents, database, select
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.mass_download.sports import sports_event_download_specific_subtitles
from subtitles.tools.delete import delete_subtitles

from ..utils import authenticate

api_ns_sports_subtitles = Namespace('Sports Subtitles', description='Download, upload or delete sports events '
                                                                    'subtitles')


@api_ns_sports_subtitles.route('sports/subtitles')
class SportsSubtitles(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('leagueid', type=int, required=True, help='League ID')
    patch_request_parser.add_argument('eventid', type=int, required=True, help='Sports event ID')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    patch_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')

    @authenticate
    @api_ns_sports_subtitles.doc(parser=patch_request_parser)
    @api_ns_sports_subtitles.response(204, 'Success')
    @api_ns_sports_subtitles.response(401, 'Not Authenticated')
    @api_ns_sports_subtitles.response(404, 'Sports event not found')
    @api_ns_sports_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_sports_subtitles.response(500, 'Custom error messages')
    def patch(self):
        """Download a sports event subtitles"""
        args = self.patch_request_parser.parse_args()

        sports_event_download_specific_subtitles(sportarr_league_id=args.get('leagueid'),
                                                 sports_event_id=args.get('eventid'),
                                                 language=args.get('language'), hi=args.get('hi').capitalize(),
                                                 forced=args.get('forced').capitalize(), job_id=None)

        return '', 204

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('leagueid', type=int, required=True, help='League ID')
    post_request_parser.add_argument('eventid', type=int, required=True, help='Sports event ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    post_request_parser.add_argument('file', type=FileStorage, location='files', required=True,
                                     help='Subtitles file as file upload object')

    @authenticate
    @api_ns_sports_subtitles.doc(parser=post_request_parser)
    @api_ns_sports_subtitles.response(204, 'Success')
    @api_ns_sports_subtitles.response(401, 'Not Authenticated')
    @api_ns_sports_subtitles.response(404, 'Sports event not found')
    @api_ns_sports_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_sports_subtitles.response(500, 'Sports event file not found. Path mapping issue?')
    def post(self):
        """Upload a sports event subtitles"""
        args = self.post_request_parser.parse_args()

        uploaded_file = args.get('file')
        _, ext = os.path.splitext(uploaded_file.filename)

        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        sportarrLeagueId = args.get('leagueid')
        sportsEventId = args.get('eventid')
        eventInfo = database.execute(
            select(TableSportsEvents.path,
                   TableSportsEvents.audio_language)
            .where(TableSportsEvents.id == sportsEventId)) \
            .first()

        if not eventInfo:
            return 'Sports event not found', 404

        eventPath = path_mappings.path_replace_sports(eventInfo.path)

        if not os.path.exists(eventPath):
            return 'Sports event file not found. Path mapping issue?', 500

        subtitle_content = BytesIO(uploaded_file.read())

        manual_upload_subtitle(path=eventPath,
                               language=args.get('language'),
                               forced=True if args.get('forced') == 'true' else False,
                               hi=True if args.get('hi') == 'true' else False,
                               media_type='sports',
                               subtitle=subtitle_content,
                               filename=uploaded_file.filename,
                               audio_language=eventInfo.audio_language,
                               sportarrLeagueId=sportarrLeagueId,
                               sportsEventId=sportsEventId)

        return '', 204

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('leagueid', type=int, required=True, help='League ID')
    delete_request_parser.add_argument('eventid', type=int, required=True, help='Sports event ID')
    delete_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    delete_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    delete_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    delete_request_parser.add_argument('path', type=str, required=True, help='Path of the subtitles file')

    @authenticate
    @api_ns_sports_subtitles.doc(parser=delete_request_parser)
    @api_ns_sports_subtitles.response(204, 'Success')
    @api_ns_sports_subtitles.response(401, 'Not Authenticated')
    @api_ns_sports_subtitles.response(404, 'Sports event not found')
    @api_ns_sports_subtitles.response(500, 'Subtitles file not found or permission issue.')
    def delete(self):
        """Delete a sports event subtitles"""
        args = self.delete_request_parser.parse_args()
        sportarrLeagueId = args.get('leagueid')
        sportsEventId = args.get('eventid')
        eventInfo = database.execute(
            select(TableSportsEvents.path)
            .where(TableSportsEvents.id == sportsEventId)) \
            .first()

        if not eventInfo:
            return 'Sports event not found', 404

        eventPath = path_mappings.path_replace_sports(eventInfo.path)

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse_sports(subtitlesPath)

        if delete_subtitles(media_type='sports',
                            language=language,
                            forced=forced,
                            hi=hi,
                            media_path=eventPath,
                            subtitles_path=subtitlesPath,
                            sportarr_league_id=sportarrLeagueId,
                            sports_event_id=sportsEventId):
            return '', 204
        else:
            return 'Subtitles file not found or permission issue.', 500
