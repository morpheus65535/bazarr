# coding=utf-8

import os
import logging
import re
import types
import platform

from logging.handlers import TimedRotatingFileHandler
from get_args import args
from config import settings


logger = logging.getLogger()


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


def configure_logging(debug=False):
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
    # ch.addFilter(MyFilter())
    logger.addHandler(ch)
    
    # File Logging
    global fh
    fh = TimedRotatingFileHandler(os.path.join(args.config_dir, 'log/bazarr.log'), when="midnight", interval=1,
                                  backupCount=7)
    f = OneLineExceptionFormatter('%(asctime)s|%(levelname)-8s|%(name)-32s|%(message)s|',
                                  '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    fh.addFilter(BlacklistFilter())
    fh.addFilter(PublicIPFilter())
    fh.setLevel(log_level)
    logger.addHandler(fh)
    
    if debug:
        logging.getLogger("sqlite3worker").setLevel(logging.DEBUG)
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)
        logging.getLogger("subliminal").setLevel(logging.DEBUG)
        logging.getLogger("subliminal_patch").setLevel(logging.DEBUG)
        logging.getLogger("subzero").setLevel(logging.DEBUG)
        logging.getLogger("git").setLevel(logging.DEBUG)
        logging.getLogger("apprise").setLevel(logging.DEBUG)
        logging.debug('Bazarr version: %s', os.environ["BAZARR_VERSION"])
        logging.debug('Bazarr branch: %s', settings.general.branch)
        logging.debug('Operating system: %s', platform.platform())
        logging.debug('Python version: %s', platform.python_version())
    else:
        logging.getLogger("sqlite3worker").setLevel(logging.CRITICAL)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("subliminal").setLevel(logging.CRITICAL)
        logging.getLogger("subliminal_patch").setLevel(logging.CRITICAL)
        logging.getLogger("subzero").setLevel(logging.ERROR)
    
    logging.getLogger("enzyme").setLevel(logging.CRITICAL)
    logging.getLogger("guessit").setLevel(logging.WARNING)
    logging.getLogger("rebulk").setLevel(logging.WARNING)
    logging.getLogger("stevedore.extension").setLevel(logging.CRITICAL)
    logging.getLogger("geventwebsocket.handler").setLevel(logging.WARNING)


class MyFilter(logging.Filter):
    def __init__(self):
        super(MyFilter, self).__init__()
    
    def filter(self, record):
        if record.name != 'root':
            return 0
        return 1


class ArgsFilteringFilter(logging.Filter):
    def filter_args(self, record, func):
        if isinstance(record.args, (types.ListType, types.TupleType)):
            final_args = []
            for arg in record.args:
                if not isinstance(arg, basestring):
                    final_args.append(arg)
                    continue
                
                final_args.append(func(arg))
            record.args = type(record.args)(final_args)
        elif isinstance(record.args, dict):
            for key, arg in record.args.items():
                if not isinstance(arg, basestring):
                    continue
                
                record.args[key] = func(arg)


class BlacklistFilter(ArgsFilteringFilter):
    """
    Log filter for blacklisted tokens and passwords
    """
    APIKEY_RE = re.compile(r'apikey(?:=|%3D)([a-zA-Z0-9]+)')
    
    def __init__(self):
        super(BlacklistFilter, self).__init__()
    
    def filter(self, record):
        def mask_apikeys(s):
            apikeys = self.APIKEY_RE.findall(s)
            for apikey in apikeys:
                s = s.replace(apikey, 8 * '*' + apikey[-2:])
            return s
        
        try:
            record.msg = mask_apikeys(record.msg)
            self.filter_args(record, mask_apikeys)
        except:
            pass
        return 1


class PublicIPFilter(ArgsFilteringFilter):
    """
    Log filter for public IP addresses
    """
    IPV4_RE = re.compile(r'[0-9]+(?:\.[0-9]+){3}(?!\d*-[a-z0-9]{6})')
    
    def __init__(self):
        super(PublicIPFilter, self).__init__()
    
    def filter(self, record):
        def mask_ipv4(s):
            ipv4 = self.IPV4_RE.findall(s)
            for ip in ipv4:
                s = s.replace(ip, ip.partition('.')[0] + '.***.***.***')
            return s
        
        try:
            # Currently only checking for ipv4 addresses
            record.msg = mask_ipv4(record.msg)
            self.filter_args(record, mask_ipv4)
        except:
            pass
        
        return 1


def empty_log():
    fh.doRollover()
