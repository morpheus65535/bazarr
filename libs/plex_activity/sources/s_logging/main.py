from plex import Plex
from plex_activity.sources.base import Source
from plex_activity.sources.s_logging.parsers import NowPlayingParser, ScrobbleParser

from asio import ASIO
from asio.file import SEEK_ORIGIN_CURRENT
from io import BufferedReader
import inspect
import logging
import os
import platform
import time

log = logging.getLogger(__name__)

PATH_HINTS = {
    'Darwin': [
        lambda: os.path.join(os.getenv('HOME'), 'Library/Logs/Plex Media Server.log')
    ],
    'FreeBSD': [
        # FreeBSD
        '/usr/local/plexdata/Plex Media Server/Logs/Plex Media Server.log',
        '/usr/local/plexdata-plexpass/Plex Media Server/Logs/Plex Media Server.log',

        # FreeNAS
        '/usr/pbi/plexmediaserver-amd64/plexdata/Plex Media Server/Logs/Plex Media Server.log',
        '/var/db/plexdata/Plex Media Server/Logs/Plex Media Server.log',
        '/var/db/plexdata-plexpass/Plex Media Server/Logs/Plex Media Server.log'
    ],
    'Linux': [
        # QNAP
        '/share/HDA_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/Logs/Plex Media Server.log',

        # Debian
        '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'
    ],
    'Windows': [
        lambda: os.path.join(os.getenv('LOCALAPPDATA'), 'Plex Media Server\\Logs\\Plex Media Server.log')
    ]
}


class Logging(Source):
    name = 'logging'
    events = [
        'logging.playing',
        'logging.action.played',
        'logging.action.unplayed'
    ]

    parsers = []

    path = None
    path_hints = PATH_HINTS

    def __init__(self, activity):
        super(Logging, self).__init__()

        self.parsers = [p(self) for p in Logging.parsers]

        self.file = None
        self.reader = None

        self.path = None

        # Pipe events to the main activity instance
        self.pipe(self.events, activity)

    def run(self):
        line = self.read_line_retry(ping=True, stale_sleep=0.5)
        if not line:
            log.info('Unable to read log file')
            return

        log.debug('Ready')

        while True:
            # Grab the next line of the log
            line = self.read_line_retry(ping=True)

            if line:
                self.process(line)
            else:
                log.info('Unable to read log file')

    def process(self, line):
        for parser in self.parsers:
            if parser.process(line):
                return True

        return False

    def read_line(self):
        if not self.file:
            path = self.get_path()
            if not path:
                raise Exception('Unable to find the location of "Plex Media Server.log"')

            # Open file
            self.file = ASIO.open(path, opener=False)
            self.file.seek(self.file.get_size(), SEEK_ORIGIN_CURRENT)

            # Create buffered reader
            self.reader = BufferedReader(self.file)

            self.path = self.file.get_path()
            log.info('Opened file path: "%s"' % self.path)

        return self.reader.readline()

    def read_line_retry(self, timeout=60, ping=False, stale_sleep=1.0):
        line = None
        stale_since = None

        while not line:
            line = self.read_line()

            if line:
                stale_since = None
                time.sleep(0.05)
                break

            if stale_since is None:
                stale_since = time.time()
                time.sleep(stale_sleep)
                continue
            elif (time.time() - stale_since) > timeout:
                return None
            elif (time.time() - stale_since) > timeout / 2:
                # Nothing returned for 5 seconds
                if self.file.get_path() != self.path:
                    log.debug("Log file moved (probably rotated), closing")
                    self.close()
                elif ping:
                    # Ping server to see if server is still active
                    Plex.detail()
                    ping = False

            time.sleep(stale_sleep)

        return line

    def close(self):
        if not self.file:
            return

        try:
            # Close the buffered reader
            self.reader.close()
        except Exception as ex:
            log.error('reader.close() - raised exception: %s', ex, exc_info=True)
        finally:
            self.reader = None

        try:
            # Close the file handle
            self.file.close()
        except OSError as ex:
            if ex.errno == 9:
                # Bad file descriptor, already closed?
                log.info('file.close() - ignoring raised exception: %s (already closed)', ex)
            else:
                log.error('file.close() - raised exception: %s', ex, exc_info=True)
        except Exception as ex:
            log.error('file.close() - raised exception: %s', ex, exc_info=True)
        finally:
            self.file = None

    @classmethod
    def get_path(cls):
        if cls.path:
            return cls.path

        hints = cls.get_hints()

        log.debug('hints: %r', hints)

        if not hints:
            log.error('Unable to find any hints for "%s", operating system not supported', platform.system())
            return None

        for hint in hints:
            log.debug('Testing if "%s" exists', hint)

            if os.path.exists(hint):
                cls.path = hint
                break

        if cls.path:
            log.debug('Using the path: %r', cls.path)
        else:
            log.error('Unable to find a valid path for "Plex Media Server.log"', extra={
                'data': {
                    'hints': hints
                }
            })

        return cls.path

    @classmethod
    def add_hint(cls, path, system=None):
        if system not in cls.path_hints:
            cls.path_hints[system] = []

        cls.path_hints[system].append(path)

    @classmethod
    def get_hints(cls):
        # Retrieve system hints
        hints_system = PATH_HINTS.get(platform.system(), [])

        # Retrieve global hints
        hints_global = PATH_HINTS.get(None, [])

        # Retrieve hint from server preferences (if available)
        data_path = Plex[':/prefs'].get('LocalAppDataPath')

        if data_path:
            hints_global.append(os.path.join(data_path.value, "Plex Media Server", "Logs", "Plex Media Server.log"))
        else:
            log.info('Unable to retrieve "LocalAppDataPath" from server')

        hints = []

        for hint in (hints_global + hints_system):
            # Resolve hint function
            if inspect.isfunction(hint):
                hint = hint()

            # Check for duplicate
            if hint in hints:
                continue

            hints.append(hint)

        return hints

    @classmethod
    def test(cls):
        # TODO "Logging" source testing
        return True

    @classmethod
    def register(cls, parser):
        cls.parsers.append(parser)


Logging.register(NowPlayingParser)
Logging.register(ScrobbleParser)
