# coding=utf-8

import io
import os

from flask_restx import Resource, Namespace, fields, marshal

from app.logger import empty_log
from app.get_args import args

from ..utils import authenticate

api_ns_system_logs = Namespace('System Logs', description='List log file entries or empty log file')


@api_ns_system_logs.route('system/logs')
class SystemLogs(Resource):
    get_response_model = api_ns_system_logs.model('SystemBackupsGetResponse', {
        'timestamp': fields.String(),
        'type': fields.String(),
        'message': fields.String(),
        'exception': fields.String(),
    })

    @authenticate
    @api_ns_system_logs.doc(parser=None)
    @api_ns_system_logs.response(200, 'Success')
    @api_ns_system_logs.response(401, 'Not Authenticated')
    def get(self):
        """List log entries"""
        logs = []
        with io.open(os.path.join(args.config_dir, 'log', 'bazarr.log'), encoding='UTF-8') as file:
            raw_lines = file.read()
            lines = raw_lines.split('|\n')
            for line in lines:
                if line == '':
                    continue
                raw_message = line.split('|')
                raw_message_len = len(raw_message)
                if raw_message_len > 3:
                    log = dict()
                    log["timestamp"] = raw_message[0]
                    log["type"] = raw_message[1].rstrip()
                    log["message"] = raw_message[3]
                    if raw_message_len > 4 and raw_message[4] != '\n':
                        log['exception'] = raw_message[4].strip('\'').replace('  ', '\u2003\u2003')
                    else:
                        log['exception'] = None
                logs.append(log)

            logs.reverse()
        return marshal(logs, self.get_response_model, envelope='data')

    @authenticate
    @api_ns_system_logs.doc(parser=None)
    @api_ns_system_logs.response(204, 'Success')
    @api_ns_system_logs.response(401, 'Not Authenticated')
    def delete(self):
        """Force log rotation and create a new log file"""
        empty_log()
        return '', 204
