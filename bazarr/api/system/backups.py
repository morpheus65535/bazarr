# coding=utf-8

from flask import jsonify, request
from flask_restful import Resource

from utilities.backup import get_backup_files, prepare_restore, delete_backup_file, backup_to_zip

from ..utils import authenticate


class SystemBackups(Resource):
    @authenticate
    def get(self):
        backups = get_backup_files(fullpath=False)
        return jsonify(data=backups)

    @authenticate
    def post(self):
        backup_to_zip()
        return '', 204

    @authenticate
    def patch(self):
        filename = request.form.get('filename')
        if filename:
            restored = prepare_restore(filename)
            if restored:
                return '', 204
        return 'Filename not provided', 400

    @authenticate
    def delete(self):
        filename = request.form.get('filename')
        if filename:
            deleted = delete_backup_file(filename)
            if deleted:
                return '', 204
        return 'Filename not provided', 400
