from plex_activity.core.helpers import str_format
from plex_activity.sources.s_logging.parsers.base import Parser, LOG_PATTERN, REQUEST_HEADER_PATTERN

import logging
import re

log = logging.getLogger(__name__)

PLAYING_HEADER_PATTERN = str_format(REQUEST_HEADER_PATTERN, method="GET", path="/:/(?P<type>timeline|progress)/?(?:\?(?P<query>.*?))?\s")
PLAYING_HEADER_REGEX = re.compile(PLAYING_HEADER_PATTERN, re.IGNORECASE)

RANGE_REGEX = re.compile(str_format(LOG_PATTERN, message=r'Request range: \d+ to \d+'), re.IGNORECASE)
CLIENT_REGEX = re.compile(str_format(LOG_PATTERN, message=r'Client \[(?P<machineIdentifier>.*?)\].*?'), re.IGNORECASE)

NOW_USER_REGEX = re.compile(str_format(LOG_PATTERN, message=r'\[Now\] User is (?P<user_name>.+) \(ID: (?P<user_id>\d+)\)'), re.IGNORECASE)
NOW_CLIENT_REGEX = re.compile(str_format(LOG_PATTERN, message=r'\[Now\] Device is (?P<product>.+?) \((?P<client>.+)\)\.'), re.IGNORECASE)


class NowPlayingParser(Parser):
    required_info = [
        'ratingKey',
        'state', 'time'
    ]

    extra_info = [
        'duration',

        'user_name', 'user_id',
        'machineIdentifier', 'client'
    ]

    events = [
        'logging.playing'
    ]

    def __init__(self, main):
        super(NowPlayingParser, self).__init__(main)

        # Pipe events to the main logging activity instance
        self.pipe(self.events, main)

    def process(self, line):
        header_match = PLAYING_HEADER_REGEX.match(line)
        if not header_match:
            return False

        activity_type = header_match.group('type')

        # Get a match from the activity entries
        if activity_type == 'timeline':
            match = self.timeline()
        elif activity_type == 'progress':
            match = self.progress()
        else:
            log.warn('Unknown activity type "%s"', activity_type)
            return True

        print match, activity_type

        if match is None:
            match = {}

        # Extend match with query info
        self.query(match, header_match.group('query'))

        # Ensure we successfully matched a result
        if not match:
            return True

        # Sanitize the activity result
        info = {
            'address': header_match.group('address'),
            'port': header_match.group('port')
        }

        # - Get required info parameters
        for key in self.required_info:
            if key in match and match[key] is not None:
                info[key] = match[key]
            else:
                log.info('Invalid activity match, missing key %s (matched keys: %s)', key, match.keys())
                return True

        # - Add in any extra info parameters
        for key in self.extra_info:
            if key in match:
                info[key] = match[key]
            else:
                info[key] = None

        # Update the scrobbler with the current state
        self.emit('logging.playing', info)
        return True

    def timeline(self):
        return self.read_parameters(
            lambda line: self.regex_match(CLIENT_REGEX, line),
            lambda line: self.regex_match(RANGE_REGEX, line),

            # [Now]* entries
            lambda line: self.regex_match(NOW_USER_REGEX, line),
            lambda line: self.regex_match(NOW_CLIENT_REGEX, line),
        )

    def progress(self):
        data = self.read_parameters()

        if not data:
            return {}

        # Translate parameters into timeline-style form
        return {
            'state': data.get('state'),
            'ratingKey': data.get('key'),
            'time': data.get('time')
        }
