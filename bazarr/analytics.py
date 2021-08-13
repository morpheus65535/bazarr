# coding=utf-8

import pickle
import random
import platform
import os
import logging
import codecs

from pyga.requests import Event, Page, Tracker, Session, Visitor, Config
from pyga.entities import CustomVariable

from get_args import args
from config import settings
from utils import get_sonarr_info, get_radarr_info

sonarr_version = get_sonarr_info.version()
radarr_version = get_radarr_info.version()


def track_event(category=None, action=None, label=None):
    if not settings.analytics.getboolean('enabled'):
        return

    anonymousConfig = Config()
    anonymousConfig.anonimize_ip_address = True

    tracker = Tracker('UA-138214134-3', 'none', conf=anonymousConfig)

    try:
        if os.path.isfile(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics.dat'))):
            with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics.dat')), 'r') as handle:
                visitor_text = handle.read()
            visitor = pickle.loads(codecs.decode(visitor_text.encode(), "base64"))
            if visitor.user_agent is None:
                visitor.user_agent = os.environ.get("SZ_USER_AGENT")
            if visitor.unique_id > int(0x7fffffff):
                visitor.unique_id = random.randint(0, 0x7fffffff)
        else:
            visitor = Visitor()
            visitor.unique_id = random.randint(0, 0x7fffffff)
    except:
        visitor = Visitor()
        visitor.unique_id = random.randint(0, 0x7fffffff)

    session = Session()
    event = Event(category=category, action=action, label=label, value=1)

    tracker.add_custom_variable(CustomVariable(index=1, name='BazarrVersion',
                                               value=os.environ["BAZARR_VERSION"].lstrip('v'), scope=1))
    tracker.add_custom_variable(CustomVariable(index=2, name='PythonVersion', value=platform.python_version(), scope=1))
    if settings.general.getboolean('use_sonarr'):
        tracker.add_custom_variable(CustomVariable(index=3, name='SonarrVersion', value=sonarr_version, scope=1))
    else:
        tracker.add_custom_variable(CustomVariable(index=3, name='SonarrVersion', value='unused', scope=1))
    if settings.general.getboolean('use_radarr'):
        tracker.add_custom_variable(CustomVariable(index=4, name='RadarrVersion', value=radarr_version, scope=1))
    else:
        tracker.add_custom_variable(CustomVariable(index=4, name='RadarrVersion', value='unused', scope=1))
    tracker.add_custom_variable(CustomVariable(index=5, name='OSVersion', value=platform.platform(), scope=1))

    try:
        tracker.track_event(event, session, visitor)
    except:
        logging.debug("BAZARR unable to track event.")
        pass
    else:
        with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics.dat')), 'w+') as handle:
            handle.write(codecs.encode(pickle.dumps(visitor), "base64").decode())
