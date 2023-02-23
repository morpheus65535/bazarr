# coding=utf-8

import os
import sys
import logging
import re
import platform
import warnings

from logging.handlers import TimedRotatingFileHandler
from pytz_deprecation_shim import PytzUsageWarning

from .get_args import args
from .config import settings


logger = logging.getLogger()


class FileHandlerFormatter(logging.Formatter):
    """Formatter that removes apikey from logs."""
    APIKEY_RE = re.compile(r'apikey(?:=|%3D)([a-zA-Z0-9]+)')
    IPv4_RE = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]'
                         r'[0-9]|[1-9]?[0-9])\b')

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

    def format(self, record):
        s = super(FileHandlerFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '') + '|'

        s = self.formatApikey(s)
        s = self.formatIPv4(s)

        return s


class NoExceptionFormatter(logging.Formatter):
    def format(self, record):
        record.exc_text = ''  # ensure formatException gets called
        return super(NoExceptionFormatter, self).format(record)

    def formatException(self, record):
        return ''


def configure_logging(debug=False):
    warnings.simplefilter('ignore', category=ResourceWarning)
    warnings.simplefilter('ignore', category=PytzUsageWarning)

    if not debug:
        log_level = "INFO"
    else:
        log_level = "DEBUG"

    logger.handlers = []

    logger.setLevel(log_level)

    # Console logging
    ch = logging.StreamHandler(sys.stdout)
    cf = (debug and logging.Formatter or NoExceptionFormatter)(
        '%(asctime)-15s - %(module)s.%(funcName)s :  %(levelname)s (%(module)s:%(lineno)d) - %(message)s')
    ch.setFormatter(cf)

    ch.setLevel(log_level)
    logger.addHandler(ch)

    # File Logging
    global fh
    if sys.version_info >= (3, 9):
        fh = PatchedTimedRotatingFileHandler(os.path.join(args.config_dir, 'log/bazarr.log'), when="midnight",
                                             interval=1, backupCount=7, delay=True, encoding='utf-8')
    else:
        fh = TimedRotatingFileHandler(os.path.join(args.config_dir, 'log/bazarr.log'), when="midnight", interval=1,
                                      backupCount=7, delay=True, encoding='utf-8')
    f = FileHandlerFormatter('%(asctime)s|%(levelname)-8s|%(name)-32s|%(message)s|',
                             '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    fh.setLevel(log_level)
    logger.addHandler(fh)

    if debug:
        logging.getLogger("peewee").setLevel(logging.DEBUG)
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
        logging.getLogger("srt").setLevel(logging.DEBUG)
        logging.debug('Bazarr version: %s', os.environ["BAZARR_VERSION"])
        logging.debug('Bazarr branch: %s', settings.general.branch)
        logging.debug('Operating system: %s', platform.platform())
        logging.debug('Python version: %s', platform.python_version())
    else:
        logging.getLogger("peewee").setLevel(logging.CRITICAL)
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
        logging.getLogger("srt").setLevel(logging.ERROR)
        logging.getLogger("SignalRCoreClient").setLevel(logging.CRITICAL)
        logging.getLogger("websocket").setLevel(logging.CRITICAL)

    logging.getLogger("waitress").setLevel(logging.ERROR)
    logging.getLogger("knowit").setLevel(logging.CRITICAL)
    logging.getLogger("enzyme").setLevel(logging.CRITICAL)
    logging.getLogger("guessit").setLevel(logging.WARNING)
    logging.getLogger("rebulk").setLevel(logging.WARNING)
    logging.getLogger("stevedore.extension").setLevel(logging.CRITICAL)


def empty_log():
    fh.doRollover()
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
        prefix = n + '.'
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
