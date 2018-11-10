import os
import sys
import logging
import re

from logging.handlers import TimedRotatingFileHandler
from get_argv import config_dir
from get_settings import get_general_settings

logger = logging.getLogger()

debug = get_general_settings()[4]
if debug is False:
    log_level = "INFO"
else:
    log_level = "DEBUG"

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
    logger.handlers = []
    
    logger.setLevel(log_level)

    # Console logging
    ch = logging.StreamHandler()
    cf = NoExceptionFormatter('%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(module)s:%(lineno)d) '
                               '- %(message)s')
    ch.setFormatter(cf)

    ch.setLevel(log_level)
    # ch.addFilter(MyFilter())
    logger.addHandler(ch)
    
    #File Logging
    global fh
    fh = TimedRotatingFileHandler(os.path.join(config_dir, 'log/bazarr.log'), when="midnight", interval=1,
                                  backupCount=7)
    f = OneLineExceptionFormatter('%(asctime)s|%(levelname)-8s|%(name)-32s|%(message)s|',
                                  '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    fh.addFilter(BlacklistFilter())
    fh.addFilter(PublicIPFilter())

    if debug is True:
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
    fh.setLevel(log_level)
    logger.addHandler(fh)
    

class MyFilter(logging.Filter):
    def __init__(self):
        pass
    
    def filter(self, record):
        if record.name != 'root':
            return False
        return True
    

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


class PublicIPFilter(logging.Filter):
    """
    Log filter for public IP addresses
    """
    def __init__(self):
        pass

    def filter(self, record):
        try:
            # Currently only checking for ipv4 addresses
            ipv4 = re.findall(r'[0-9]+(?:\.[0-9]+){3}(?!\d*-[a-z0-9]{6})', record.msg)
            for ip in ipv4:
                record.msg = record.msg.replace(ip, ip.partition('.')[0] + '.***.***.***')

            args = []
            for arg in record.args:
                ipv4 = re.findall(r'[0-9]+(?:\.[0-9]+){3}(?!\d*-[a-z0-9]{6})', arg) if isinstance(arg, basestring) else []
                for ip in ipv4:
                    arg = arg.replace(ip, ip.partition('.')[0] + '.***.***.***')
                args.append(arg)
            record.args = tuple(args)
        except:
            pass

        return True


def empty_log():
    fh.doRollover()
    

def update_settings(debug):
    if debug == 'False':
        level = "INFO"
    else:
        level = "DEBUG"
    print debug, level
    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)
