# coding=utf-8

import os
import logging
import re
import platform
import warnings

from logging.handlers import TimedRotatingFileHandler
from get_args import args
from config import settings


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

    if not debug:
        log_level = "INFO"
    else:
        log_level = "DEBUG"
    
    logger.handlers = []
    
    logger.setLevel(log_level)
    
    # Console logging
    ch = logging.StreamHandler()
    cf = (debug and logging.Formatter or NoExceptionFormatter)(
        '%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(module)s:%(lineno)d) - %(message)s')
    ch.setFormatter(cf)
    
    ch.setLevel(log_level)
    logger.addHandler(ch)
    
    # File Logging
    global fh
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
