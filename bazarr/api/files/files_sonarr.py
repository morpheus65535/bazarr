# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from sonarr.filesystem import browse_sonarr_filesystem

from ..utils import authenticate

api_ns_files_sonarr = Namespace('Files Browser for Sonarr', description='Browse content of file system as seen by '
                                                                        'Sonarr')


@api_ns_files_sonarr.route('files/sonarr')
class BrowseSonarrFS(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('path', type=str, default='', help='Path to browse')

    get_response_model = api_ns_files_sonarr.model('SonarrFileBrowserGetResponse', {
        'name': fields.String(),
        'children': fields.Boolean(),
        'path': fields.String(),
    })

    @authenticate
    @api_ns_files_sonarr.marshal_with(get_response_model, code=200)
    @api_ns_files_sonarr.response(401, 'Not Authenticated')
    @api_ns_files_sonarr.doc(parser=get_request_parser)
    def get(self):
        """List Sonarr file system content"""
        args = self.get_request_parser.parse_args()
        path = args.get('path')
        data = []
        try:
            result = browse_sonarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return []
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return data
