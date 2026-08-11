# coding=utf-8
import logging
import pysubs2
import srt

from datetime import timedelta
from flask_restx import Resource, Namespace, reqparse, fields, marshal

from ..utils import authenticate
from subtitles.indexer.utils import detect_encoding


api_ns_subtitle_contents = Namespace('Subtitle Contents', description='Retrieve contents of subtitle file')


def times_dict_from_ms(ms):
    total_seconds = ms // 1000
    return dict(
        hours=total_seconds // 3600,
        minutes=(total_seconds % 3600) // 60,
        seconds=total_seconds % 60,
        total_seconds=total_seconds,
        microseconds=(ms % 1000) * 1000
    )


def map_contents(lines):
    return [dict(
        index=index,
        content=content,
        proprietary=proprietary,
        start=times_dict_from_ms(start_ms),
        end=times_dict_from_ms(end_ms),
    ) for index, content, proprietary, start_ms, end_ms in lines]


def parse_srt_contents(file_content):
    return map_contents(
        (sub.index, sub.content, sub.proprietary,
         sub.start // timedelta(milliseconds=1), sub.end // timedelta(milliseconds=1))
        for sub in srt.parse(file_content))


def parse_ssa_contents(file_content):
    events = pysubs2.SSAFile.from_string(file_content).get_text_events()
    return map_contents(
        (index, event.text, '', event.start, event.end)
        for index, event in enumerate(events, start=1))


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
    @api_ns_subtitle_contents.response(400, 'Invalid subtitle file encoding')
    @api_ns_subtitle_contents.response(401, 'Not Authenticated')
    @api_ns_subtitle_contents.doc(parser=get_request_parser)
    def get(self):
        """Retrieve subtitle file contents"""

        args = self.get_request_parser.parse_args()
        path = args.get('subtitlePath')

        # Detect subtitles file encoding
        encoding = detect_encoding(path)
        if encoding is None:
            return 'Invalid subtitle file encoding', 400

        # Load the subtitles content
        with open(path, "r", encoding=encoding) as f:
            file_content = f.read()

        try:
            results = parse_srt_contents(file_content)
        except (srt.SRTParseError, srt.TimestampParseError):
            results = parse_ssa_contents(file_content)

        return marshal(results, self.get_response_model, envelope='data')
