# coding=utf-8

import io
import re

from flask_restx import Resource, Namespace, fields, marshal

from app.config import settings
from app.logger import empty_log

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

    def handle_record(self, logs, multi_line_record):
        # finalize the multi line record
        if logs:
            # update the exception of the last entry 
            last_log = logs[-1]
            last_log["exception"] += "\n".join(multi_line_record)
        else:
            # multiline record is first entry in log
            last_log = dict()
            last_log["type"] = "ERROR"
            last_log["message"] = "See exception"
            last_log["exception"] = "\n".join(multi_line_record)
            logs.append(last_log)

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

        # regular expression to identify the start of a log record (timestamp-based)
        record_start_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

        with io.open(get_log_file_path(), encoding='UTF-8') as file:
            raw_lines = file.read()
            lines = raw_lines.split('|\n')
            multi_line_record = []
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
                # check if the line has a timestamp that matches the start of a new log record
                if record_start_pattern.match(line):
                    if multi_line_record:
                        self.handle_record(logs, multi_line_record)
                        # reset for the next multi-line record
                        multi_line_record = []
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
                else:
                    # accumulate lines that do not have new record header timestamps
                    multi_line_record.append(line.strip())

            if multi_line_record:
                # finalize the multi line record and update the exception of the last entry 
                self.handle_record(logs, multi_line_record)

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
