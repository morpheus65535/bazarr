# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from utilities.backup import get_backup_files, prepare_restore, delete_backup_file, backup_to_zip

from ..utils import authenticate

api_ns_system_backups = Namespace('System Backups', description='List, create, restore or delete backups')


@api_ns_system_backups.route('system/backups')
class SystemBackups(Resource):
    get_response_model = api_ns_system_backups.model('SystemBackupsGetResponse', {
        'date': fields.String(),
        'filename': fields.String(),
        'size': fields.String(),
        'type': fields.String(),
    })

    @authenticate
    @api_ns_system_backups.doc(parser=None)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    def get(self):
        """List backup files"""
        backups = get_backup_files(fullpath=False)
        return marshal(backups, self.get_response_model, envelope='data')

    @authenticate
    @api_ns_system_backups.doc(parser=None)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    def post(self):
        """Create a new backup"""
        backup_to_zip()
        return '', 204

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('filename', type=str, required=True, help='Backups to restore filename')

    @authenticate
    @api_ns_system_backups.doc(parser=patch_request_parser)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(400, 'Filename not provided')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    @api_ns_system_backups.response(500, 'Error while restoring backup. Check logs.')
    def patch(self):
        """Restore a backup file"""
        args = self.patch_request_parser.parse_args()
        filename = args.get('filename')
        if filename:
            restored = prepare_restore(filename)
            if restored:
                return '', 204
            else:
                return 'Error while restoring backup. Check logs.', 500
        else:
            return 'Filename not provided', 400

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('filename', type=str, required=True, help='Backups to delete filename')

    @authenticate
    @api_ns_system_backups.doc(parser=delete_request_parser)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(400, 'Filename not provided')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    def delete(self):
        """Delete a backup file"""
        args = self.delete_request_parser.parse_args()
        filename = args.get('filename')
        if filename:
            deleted = delete_backup_file(filename)
            if deleted:
                return '', 204
        return 'Filename not provided', 400
