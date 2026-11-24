# coding=utf-8

from typing import Any

from flask import request
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from werkzeug.datastructures import FileStorage

from utilities.backup import (get_backup_files, prepare_restore, delete_backup_file, backup_to_zip,
                              save_uploaded_backup, BackupUploadError, BACKUP_UPLOAD_MAX_BYTES)

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
    @api_ns_system_backups.expect(None)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    def get(self):
        """List backup files"""
        backups = get_backup_files(fullpath=False)
        return marshal(backups, self.get_response_model, envelope='data')

    @authenticate
    @api_ns_system_backups.expect(None)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    def post(self):
        """Create a new backup"""
        backup_to_zip()
        return '', 204

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('filename', type=str, required=True, help='Backups to restore filename')

    @authenticate
    @api_ns_system_backups.expect(patch_request_parser)
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
    @api_ns_system_backups.expect(delete_request_parser)
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


_MULTIPART_OVERHEAD_BYTES = 1024 * 1024


@api_ns_system_backups.route('system/backups/upload')
class SystemBackupsUpload(Resource):
    upload_request_parser = reqparse.RequestParser()
    upload_request_parser.add_argument('file', type=FileStorage, location='files', required=True,
                                       help='Backup archive to upload')

    def dispatch_request(self, *args: object, **kwargs: object) -> Any:
        """
        Apply the upload size limit before any part of the request body is read.

        ``@authenticate`` reads ``request.form``, which parses the multipart
        body, so the limit has to be in place before the decorated method runs.
        Werkzeug enforces it while reading and answers 413 when it is exceeded.
        """
        request.max_content_length = BACKUP_UPLOAD_MAX_BYTES + _MULTIPART_OVERHEAD_BYTES
        return super().dispatch_request(*args, **kwargs)

    @authenticate
    @api_ns_system_backups.expect(upload_request_parser)
    @api_ns_system_backups.response(204, 'Success')
    @api_ns_system_backups.response(400, 'Invalid filename or not a valid backup archive')
    @api_ns_system_backups.response(401, 'Not Authenticated')
    @api_ns_system_backups.response(409, 'A backup with this name already exists')
    @api_ns_system_backups.response(413, 'Backup archive is too large')
    def post(self) -> tuple[str, int]:
        """Upload a backup archive into the backup directory"""
        args = self.upload_request_parser.parse_args()
        uploaded_file = args.get('file')
        try:
            save_uploaded_backup(uploaded_file.stream, uploaded_file.filename)
        except BackupUploadError as error:
            return str(error), error.status_code
        return '', 204
