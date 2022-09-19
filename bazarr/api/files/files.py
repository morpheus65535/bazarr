# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from utilities.filesystem import browse_bazarr_filesystem

from ..utils import authenticate

api_ns_files = Namespace('Files Browser for Bazarr', description='Browse content of file system as seen by Bazarr')


@api_ns_files.route('files')
class BrowseBazarrFS(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('path', type=str, default='', help='Path to browse')

    get_response_model = api_ns_files.model('BazarrFileBrowserGetResponse', {
        'name': fields.String(),
        'children': fields.Boolean(),
        'path': fields.String(),
    })

    @authenticate
    @api_ns_files.marshal_with(get_response_model, code=200)
    @api_ns_files.response(401, 'Not Authenticated')
    @api_ns_files.doc(parser=get_request_parser)
    def get(self):
        args = self.get_request_parser.parse_args()
        path = args.get('path')
        data = []
        try:
            result = browse_bazarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return []
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return data
