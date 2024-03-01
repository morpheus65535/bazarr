# coding=utf-8

import io
import re

from flask_restx import Resource, Namespace, fields, marshal

from app.config import settings
from app.logger import empty_log
from app.get_args import args

from utilities.central import get_log_file_path
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
        include = str(settings.log.include_filter)
        exclude = str(settings.log.exclude_filter)
        ignore_case = settings.log.ignore_case
        regex = settings.log.use_regex
        if regex:
            # pre-compile regular expressions for better performance
            if ignore_case:
                flags = re.IGNORECASE
            else:
                flags = 0
            if len(include) > 0:
                try:
                    include_compiled = re.compile(include, flags)
                except Exception:
                    include_compiled = None
            if len(exclude) > 0:
                try:
                    exclude_compiled = re.compile(exclude, flags)
                except Exception:
                    exclude_compiled = None
        elif ignore_case:
            include = include.casefold()
            exclude = exclude.casefold()

        with io.open(get_log_file_path(), encoding='UTF-8') as file:
            raw_lines = file.read()
            lines = raw_lines.split('|\n')
            for line in lines:
                if line == '':
                    continue
                if ignore_case and not regex:
                    compare_line = line.casefold()
                else:
                    compare_line = line
                if len(include) > 0:
                    if regex:
                        if include_compiled is None:
                            # if invalid re, keep the line
                            keep = True
                        else:
                            keep = include_compiled.search(compare_line)
                    else:
                        keep = include in compare_line
                    if not keep:
                        continue
                if len(exclude) > 0:
                    if regex:
                        if exclude_compiled is None:
                            # if invalid re, keep the line
                            skip = False
                        else:
                            skip = exclude_compiled.search(compare_line)
                    else:
                        skip = exclude in compare_line
                    if skip:
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
