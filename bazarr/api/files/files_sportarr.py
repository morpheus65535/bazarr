# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from sportarr.filesystem import browse_sportarr_filesystem

from ..utils import authenticate

api_ns_files_sportarr = Namespace('Files Browser for Sportarr',
                                  description='Browse content of file system as seen by Sportarr')


@api_ns_files_sportarr.route('files/sportarr')
class BrowseSportarrFS(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('path', type=str, default='', help='Path to browse')

    get_response_model = api_ns_files_sportarr.model('SportarrFileBrowserGetResponse', {
        'name': fields.String(),
        'children': fields.Boolean(),
        'path': fields.String(),
    })

    @authenticate
    @api_ns_files_sportarr.response(401, 'Not Authenticated')
    @api_ns_files_sportarr.doc(parser=get_request_parser)
    def get(self):
        """List Sportarr file system content"""
        args = self.get_request_parser.parse_args()
        path = args.get('path')
        data = []
        try:
            result = browse_sportarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return []
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return marshal(data, self.get_response_model)
