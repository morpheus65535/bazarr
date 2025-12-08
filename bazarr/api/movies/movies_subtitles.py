# coding=utf-8

import os
import time

from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableMovies, get_profile_id, database, select
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.mass_download.movies import movie_download_specific_subtitles
from subtitles.download import generate_subtitles
from subtitles.tools.delete import delete_subtitles
from app.event_handler import event_stream
from app.config import settings
from app.jobs_queue import jobs_queue

from ..utils import authenticate

api_ns_movies_subtitles = Namespace('Movies Subtitles', description='Download, upload or delete movies subtitles')


@api_ns_movies_subtitles.route('movies/subtitles')
class MoviesSubtitles(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    patch_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=patch_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_movies_subtitles.response(500, 'Custom error messages')
    def patch(self):
        """Download a movie subtitles"""
        args = self.patch_request_parser.parse_args()

        job_id = movie_download_specific_subtitles(radarr_id=args.get('radarrid'), language=args.get('language'),
                                                   hi=args.get('hi').capitalize(),
                                                   forced=args.get('forced').capitalize(), job_id=None)

        # Wait for the job to complete or fail
        while jobs_queue.get_job_status(job_id=job_id) in ['pending', 'running']:
            time.sleep(1)

        return jobs_queue.get_job_returned_value(job_id=job_id)

    # POST: Upload Subtitles
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    post_request_parser.add_argument('file', type=FileStorage, location='files', required=True,
                                     help='Subtitles file as file upload object')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=post_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_movies_subtitles.response(500, 'Movie file not found. Path mapping issue?')
    def post(self):
        """Upload a movie subtitles"""
        # TODO: Support Multiply Upload
        args = self.post_request_parser.parse_args()

        _, ext = os.path.splitext(args.get('file').filename)

        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        radarrId = args.get('radarrid')
        movieInfo = database.execute(
            select(TableMovies.path, TableMovies.audio_language)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        if not os.path.exists(moviePath):
            return 'Movie file not found. Path mapping issue?', 500

        job_id = manual_upload_subtitle(path=moviePath,
                                        language=args.get('language'),
                                        forced=True if args.get('forced') == 'true' else False,
                                        hi=True if args.get('hi') == 'true' else False,
                                        media_type='movie',
                                        subtitle=args.get('file'),
                                        audio_language=movieInfo.audio_language,
                                        radarrId=radarrId)

        # Wait for the job to complete or fail
        while jobs_queue.get_job_status(job_id=job_id) in ['pending', 'running']:
            time.sleep(1)

        return jobs_queue.get_job_returned_value(job_id=job_id)

    # DELETE: Delete Subtitles
    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    delete_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    delete_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    delete_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    delete_request_parser.add_argument('path', type=str, required=True, help='Path of the subtitles file')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=delete_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(500, 'Subtitles file not found or permission issue.')
    def delete(self):
        """Delete a movie subtitles"""
        args = self.delete_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = database.execute(
            select(TableMovies.path)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse_movie(subtitlesPath)

        if delete_subtitles(media_type='movie',
                            language=language,
                            forced=forced,
                            hi=hi,
                            media_path=moviePath,
                            subtitles_path=subtitlesPath,
                            radarr_id=radarrId):
            return '', 204
        else:
            return 'Subtitles file not found or permission issue.', 500

