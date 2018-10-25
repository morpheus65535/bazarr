import os
import sys
import logging
import re

from logging.handlers import TimedRotatingFileHandler
from get_argv import config_dir
from get_settings import get_general_settings

log_level = get_general_settings()[4]
if log_level is None:
    log_level = "INFO"


class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        """
        Format an exception so that it prints on a single line.
        """
        result = super(OneLineExceptionFormatter, self).formatException(exc_info)
        return repr(result)  # or format into one line however you want to
    
    def format(self, record):
        s = super(OneLineExceptionFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '') + '|'
        return s


class NoExceptionFormatter(logging.Formatter):
    def format(self, record):
        record.exc_text = ''  # ensure formatException gets called
        return super(NoExceptionFormatter, self).format(record)
    
    def formatException(self, record):
        return ''


def configure_logging():
    log = logging.getLogger()
    log.handlers = []
    
    global fh
    fh = TimedRotatingFileHandler(os.path.join(config_dir, 'log/bazarr.log'), when="midnight", interval=1,
                                  backupCount=7)
    f = OneLineExceptionFormatter('%(asctime)s|%(levelname)-8s|%(name)-32s|%(message)s|',
                                  '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    fh.addFilter(BlacklistFilter())

    if log_level == 'debug':
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)
        logging.getLogger("subliminal").setLevel(logging.DEBUG)
        logging.getLogger("git").setLevel(logging.DEBUG)
        logging.getLogger("apprise").setLevel(logging.DEBUG)
    else:
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("subliminal").setLevel(logging.CRITICAL)
        
    logging.getLogger("enzyme").setLevel(logging.CRITICAL)
    logging.getLogger("guessit").setLevel(logging.WARNING)
    logging.getLogger("rebulk").setLevel(logging.WARNING)
    logging.getLogger("stevedore.extension").setLevel(logging.CRITICAL)
    log.setLevel(log_level)
    log.addHandler(fh)

    ch = logging.StreamHandler()
    cf = NoExceptionFormatter('%(asctime)s - %(levelname)s :: %(message)s',
                                          '%Y-%m-%d %H:%M:%S')
    ch.setFormatter(cf)
    ch.setLevel(logging.INFO)
    log.addHandler(ch)
    

class BlacklistFilter(logging.Filter):
    """
    Log filter for blacklisted tokens and passwords
    """
    def __init__(self):
        pass

    def filter(self, record):
        try:
            apikeys = re.findall(r'apikey(?:=|%3D)([a-zA-Z0-9]+)', record.msg)
            for apikey in apikeys:
                record.msg = record.msg.replace(apikey, 8 * '*' + apikey[-2:])
    
            args = []
            for arg in record.args:
                apikeys = re.findall(r'apikey(?:=|%3D)([a-zA-Z0-9]+)', arg) if isinstance(arg, basestring) else []
                for apikey in apikeys:
                    arg = arg.replace(apikey, 8 * '*' + apikey[-2:])
                args.append(arg)
            record.args = tuple(args)
        except:
            pass
        return True


def empty_log():
    fh.doRollover()

