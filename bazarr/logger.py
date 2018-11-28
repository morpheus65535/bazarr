# coding=utf-8

import os
import logging
import re
import types

from logging.handlers import TimedRotatingFileHandler
from get_args import args

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

    if debug:
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)
        logging.getLogger("subliminal").setLevel(logging.DEBUG)
        logging.getLogger("subliminal_patch").setLevel(logging.DEBUG)
        logging.getLogger("subzero").setLevel(logging.DEBUG)
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
        super(MyFilter, self).__init__()

    def filter(self, record):
        if record.name != 'root':
            return 0
        return 1


class BlacklistFilter(logging.Filter):
    """
    Log filter for blacklisted tokens and passwords
    """

    def __init__(self):
        super(BlacklistFilter, self).__init__()

    def filter(self, record):
        def mask_apikeys(s):
            apikeys = re.findall(r'apikey(?:=|%3D)([a-zA-Z0-9]+)', s)
            for apikey in apikeys:
                s = arg.replace(apikey, 8 * '*' + apikey[-2:])
            return s

        try:
            apikeys = re.findall(r'apikey(?:=|%3D)([a-zA-Z0-9]+)', record.msg)
            for apikey in apikeys:
                record.msg = record.msg.replace(apikey, 8 * '*' + apikey[-2:])

            if isinstance(record.args, (types.ListType, types.TupleType)):
                final_args = []
                for arg in record.args:
                    if not isinstance(arg, basestring):
                        final_args.append(arg)
                        continue

                    final_args.append(mask_apikeys(arg))
                record.args = record.args = type(record.args)(final_args)
            elif isinstance(record.args, dict):
                for key, arg in record.args.items():
                    if not isinstance(arg, basestring):
                        continue

                    record.args[key] = mask_apikeys(arg)
        except:
            pass
        return 1


class PublicIPFilter(logging.Filter):
    """
    Log filter for public IP addresses
    """

    def __init__(self):
        super(PublicIPFilter, self).__init__()

    def filter(self, record):
        def mask_ipv4(s):
            ipv4 = re.findall(r'[0-9]+(?:\.[0-9]+){3}(?!\d*-[a-z0-9]{6})', s)
            for ip in ipv4:
                s = s.replace(ip, ip.partition('.')[0] + '.***.***.***')
            return s

        try:
            # Currently only checking for ipv4 addresses
            ipv4 = re.findall(r'[0-9]+(?:\.[0-9]+){3}(?!\d*-[a-z0-9]{6})', record.msg)
            for ip in ipv4:
                record.msg = record.msg.replace(ip, ip.partition('.')[0] + '.***.***.***')

            if isinstance(record.args, (types.ListType, types.TupleType)):
                final_args = []
                for arg in record.args:
                    if not isinstance(arg, basestring):
                        final_args.append(arg)
                        continue

                    final_args.append(mask_ipv4(arg))

                record.args = type(record.args)(final_args)
            elif isinstance(record.args, dict):
                for key, arg in record.args.items():
                    if not isinstance(arg, basestring):
                        continue

                    record.args[key] = mask_ipv4(arg)
        except:
            pass

        return 1


def empty_log():
    fh.doRollover()
