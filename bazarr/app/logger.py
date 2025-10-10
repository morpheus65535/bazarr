# coding=utf-8

import os
import sys
import logging
import re
import platform
import warnings

from logging.handlers import TimedRotatingFileHandler
from utilities.central import get_log_file_path
from pytz_deprecation_shim import PytzUsageWarning

from .config import settings


logger = logging.getLogger()


class FileHandlerFormatter(logging.Formatter):
    """Formatter that removes apikey from logs."""
    APIKEY_RE = re.compile(r'apikey(?:=|%3D)([a-zA-Z0-9]+)')
    IPv4_RE = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]'
                         r'[0-9]|[1-9]?[0-9])\b')
    PLEX_URL_RE = re.compile(r'(?:https?://)?[0-9\-]+\.[a-f0-9]+\.plex\.direct(?::\d+)?')

    def formatException(self, exc_info):
        """
        Format an exception so that it prints on a single line.
        """
        result = super(FileHandlerFormatter, self).formatException(exc_info)
        return repr(result)  # or format into one line however you want to

    def formatApikey(self, s):
        return re.sub(self.APIKEY_RE, 'apikey=(removed)', s)

    def formatIPv4(self, s):
        return re.sub(self.IPv4_RE, '***.***.***.***', s)

    def formatPlexUrl(self, s):
        def sanitize_plex_url(match):
            url = match.group(0)
            # Extract protocol and port for reconstruction
            if '://' in url:
                protocol = url.split('://')[0] + '://'
                domain_part = url.split('://')[1]
            else:
                protocol = ''
                domain_part = url
            
            # Extract port if present
            if ':' in domain_part and domain_part.split(':')[-1].isdigit():
                port = ':' + domain_part.split(':')[-1]
                domain_part = domain_part.rsplit(':', 1)[0]
            else:
                port = ''
            
            # Extract the part before .plex.direct
            if '.plex.direct' in domain_part:
                plex_prefix = domain_part.replace('.plex.direct', '')
                # Show first 4 and last 4 characters with asterisks in between
                if len(plex_prefix) > 8:
                    sanitized_domain = f"{plex_prefix[:4]}{'*' * 6}{plex_prefix[-4:]}.plex.direct"
                else:
                    sanitized_domain = f"***{plex_prefix[-4:]}.plex.direct" if len(plex_prefix) >= 4 else "***.plex.direct"
            else:
                sanitized_domain = domain_part
            
            return f"{protocol}{sanitized_domain}{port}"
        
        return re.sub(self.PLEX_URL_RE, sanitize_plex_url, s)

    def format(self, record):
        s = super(FileHandlerFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '') + '|'

        s = self.formatApikey(s)
        s = self.formatIPv4(s)
        s = self.formatPlexUrl(s)

        return s


class NoExceptionFormatter(FileHandlerFormatter):
    def format(self, record):
        record.exc_text = ''  # ensure formatException gets called
        return super(NoExceptionFormatter, self).format(record)

    def formatException(self, record):
        return ''


class UnwantedWaitressMessageFilter(logging.Filter):
    def filter(self, record):
        if settings.general.debug or "BAZARR" in record.msg:
            # no filtering in debug mode or if originating from us
            return True

        if record.levelno < logging.ERROR:
            return False

        unwantedMessages = [
            "Exception while serving /api/socket.io/",
            ['Session is disconnected', 'Session not found'],

            "Exception while serving /api/socket.io/",
            ["'Session is disconnected'", "'Session not found'"],

            "Exception while serving /api/socket.io/",
            ['"Session is disconnected"', '"Session not found"'],

            "Exception when servicing %r",
            [],
        ]

        wanted = True
        listLength = len(unwantedMessages)
        for i in range(0, listLength, 2):
            if record.msg == unwantedMessages[i]:
                exceptionTuple = record.exc_info
                if exceptionTuple is not None:
                    if len(unwantedMessages[i+1]) == 0 or str(exceptionTuple[1]) in unwantedMessages[i+1]:
                        wanted = False
                        break

        return wanted


def configure_logging(debug=False):
    warnings.simplefilter('ignore', category=ResourceWarning)
    warnings.simplefilter('ignore', category=PytzUsageWarning)
    # warnings.simplefilter('ignore', category=SAWarning)

    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger.handlers = []

    logger.setLevel(log_level)

    # Console logging
    ch = logging.StreamHandler()
    cf = (debug and FileHandlerFormatter or NoExceptionFormatter)(
        '%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(module)s:%(lineno)d) - %(message)s')
    ch.setFormatter(cf)

    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    # File Logging
    global fh
    if sys.version_info >= (3, 9):
        fh = PatchedTimedRotatingFileHandler(get_log_file_path(), when="midnight",
                                             interval=1, backupCount=7, delay=True, encoding='utf-8')
    else:
        fh = TimedRotatingFileHandler(get_log_file_path(), when="midnight", interval=1,
                                      backupCount=7, delay=True, encoding='utf-8')
    f = FileHandlerFormatter('%(asctime)s|%(levelname)-8s|%(name)-32s|%(message)s|',
                             '%Y-%m-%d %H:%M:%S')
    fh.setFormatter(f)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    if debug:
        logging.getLogger("alembic.runtime.migration").setLevel(logging.DEBUG)
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)
        logging.getLogger("subliminal").setLevel(logging.DEBUG)
        logging.getLogger("subliminal_patch").setLevel(logging.DEBUG)
        logging.getLogger("subzero").setLevel(logging.DEBUG)
        logging.getLogger("git").setLevel(logging.DEBUG)
        logging.getLogger("apprise").setLevel(logging.DEBUG)
        logging.getLogger("engineio.server").setLevel(logging.DEBUG)
        logging.getLogger("socketio.server").setLevel(logging.DEBUG)
        logging.getLogger("ffsubsync.subtitle_parser").setLevel(logging.DEBUG)
        logging.getLogger("ffsubsync.speech_transformers").setLevel(logging.DEBUG)
        logging.getLogger("ffsubsync.ffsubsync").setLevel(logging.DEBUG)
        logging.getLogger("ffsubsync.aligners").setLevel(logging.DEBUG)
        logging.getLogger("srt").setLevel(logging.DEBUG)
        logging.debug('Bazarr version: %s', os.environ["BAZARR_VERSION"])
        logging.debug('Bazarr branch: %s', settings.general.branch)
        logging.debug('Operating system: %s', platform.platform())
        logging.debug('Python version: %s', platform.python_version())
    else:
        logging.getLogger("alembic.runtime.migration").setLevel(logging.CRITICAL)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("apprise").setLevel(logging.WARNING)
        logging.getLogger("subliminal").setLevel(logging.CRITICAL)
        logging.getLogger("subliminal_patch").setLevel(logging.CRITICAL)
        logging.getLogger("subzero").setLevel(logging.ERROR)
        logging.getLogger("engineio.server").setLevel(logging.ERROR)
        logging.getLogger("socketio.server").setLevel(logging.ERROR)
        logging.getLogger("ffsubsync.subtitle_parser").setLevel(logging.ERROR)
        logging.getLogger("ffsubsync.speech_transformers").setLevel(logging.ERROR)
        logging.getLogger("ffsubsync.ffsubsync").setLevel(logging.ERROR)
        logging.getLogger("ffsubsync.aligners").setLevel(logging.ERROR)
        logging.getLogger("srt").setLevel(logging.ERROR)
        logging.getLogger("SignalRCoreClient").setLevel(logging.CRITICAL)
        logging.getLogger("websocket").setLevel(logging.CRITICAL)
        logging.getLogger("ga4mp.ga4mp").setLevel(logging.ERROR)

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("waitress").addFilter(UnwantedWaitressMessageFilter())
    logging.getLogger("knowit").setLevel(logging.CRITICAL)
    logging.getLogger("enzyme").setLevel(logging.CRITICAL)
    logging.getLogger("guessit").setLevel(logging.WARNING)
    logging.getLogger("rebulk").setLevel(logging.WARNING)
    logging.getLogger("stevedore.extension").setLevel(logging.CRITICAL)
    logging.getLogger("plexapi").setLevel(logging.ERROR)

def empty_file(filename):
    # Open the log file in write mode to clear its contents
    with open(filename, 'w'):
        pass  # Just opening and closing the file will clear it

def empty_log():
    fh.doRollover()
    empty_file(get_log_file_path())
    logging.info('BAZARR Log file emptied')


class PatchedTimedRotatingFileHandler(TimedRotatingFileHandler):
    # This super classed version of logging.TimedRotatingFileHandler is required to fix a bug in earlier version of
    # Python 3.9, 3.10 and 3.11 where log rotation isn't working as expected and do not delete backup log files.

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 atTime=None, errors=None):
        super(PatchedTimedRotatingFileHandler, self).__init__(filename, when, interval, backupCount, encoding, delay, utc,
                                                              atTime, errors)

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.
        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        # See bpo-44753: Don't use the extension when computing the prefix.
        n, e = os.path.splitext(baseName)
        prefix = f'{n}.'
        plen = len(prefix)
        for fileName in fileNames:
            if self.namer is None:
                # Our files will always start with baseName
                if not fileName.startswith(baseName):
                    continue
            else:
                # Our files could be just about anything after custom naming, but
                # likely candidates are of the form
                # foo.log.DATETIME_SUFFIX or foo.DATETIME_SUFFIX.log
                if (not fileName.startswith(baseName) and fileName.endswith(e) and
                        len(fileName) > (plen + 1) and not fileName[plen+1].isdigit()):
                    continue

            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                # See bpo-45628: The date/time suffix could be anywhere in the
                # filename
                parts = suffix.split('.')
                for part in parts:
                    if self.extMatch.match(part):
                        result.append(os.path.join(dirName, fileName))
                        break
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result
