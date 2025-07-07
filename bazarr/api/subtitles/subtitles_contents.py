# coding=utf-8
import logging
import srt

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from ..utils import authenticate


api_ns_subtitle_contents = Namespace('Subtitle Contents', description='Retrieve contents of subtitle file')


@api_ns_subtitle_contents.route('subtitles/contents')
class SubtitleNameContents(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('subtitlePath', type=str, required=True, help='Subtitle filepath')

    time_modal = api_ns_subtitle_contents.model('time_modal', {
        'hours': fields.Integer(),
        'minutes': fields.Integer(),
        'seconds': fields.Integer(),
        'total_seconds': fields.Integer(),
        'microseconds': fields.Integer(),
    })

    get_response_model = api_ns_subtitle_contents.model('SubtitlesContentsGetResponse', {
        'index': fields.Integer(),
        'content': fields.String(),
        'proprietary': fields.String(),
        'start': fields.Nested(time_modal),
        'end': fields.Nested(time_modal),
        # 'duration': fields.Nested(time_modal),
    })

    @authenticate
    @api_ns_subtitle_contents.response(200, 'Success')
    @api_ns_subtitle_contents.response(401, 'Not Authenticated')
    @api_ns_subtitle_contents.doc(parser=get_request_parser)
    def get(self):
        """Retrieve subtitle file contents"""

        args = self.get_request_parser.parse_args()
        path = args.get('subtitlePath')

        results = []

        # Load the SRT content
        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # Map contents
        for sub in srt.parse(file_content):

            start_total_seconds = int(sub.start.total_seconds())
            end_total_seconds = int(sub.end.total_seconds())
            duration_timedelta = sub.end - sub.start

            results.append(dict(
                index=sub.index,
                content=sub.content,
                proprietary=sub.proprietary,
                start=dict(
                    hours = start_total_seconds // 3600,
                    minutes = (start_total_seconds % 3600) // 60,
                    seconds = start_total_seconds % 60,
                    total_seconds=int(sub.start.total_seconds()),
                    microseconds = sub.start.microseconds
                ),
                end=dict(
                    hours = end_total_seconds // 3600,
                    minutes = (end_total_seconds % 3600) // 60,
                    seconds = end_total_seconds % 60,
                    total_seconds=int(sub.end.total_seconds()),
                    microseconds = sub.end.microseconds
                ),
                # duration=dict(
                #     seconds=int(duration_timedelta.total_seconds()),
                #     microseconds=duration_timedelta.microseconds
                # ),
            ))
        
        return marshal(results, self.get_response_model, envelope='data')
