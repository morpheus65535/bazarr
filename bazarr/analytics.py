# coding=utf-8

import cPickle as pickle
import base64
import random
import platform
import os

from pyga.requests import Event, Page, Tracker, Session, Visitor, Config
from pyga.entities import CustomVariable

from get_args import args
from config import settings
from utils import get_sonarr_version, get_radarr_version

sonarr_version = get_sonarr_version()
radarr_version = get_radarr_version()


def track_event(category=None, action=None, label=None):
    if not settings.analytics.getboolean('enabled'):
        return

    anonymousConfig = Config()
    anonymousConfig.anonimize_ip_address = True

    tracker = Tracker('UA-138214134-3', 'none', conf=anonymousConfig)

    try:
        if settings.analytics.visitor:
            visitor = pickle.loads(base64.b64decode(settings.analytics.visitor))
        if visitor.unique_id > int(0x7fffffff):
            visitor.unique_id = random.randint(0, 0x7fffffff)
    except:
        visitor = Visitor()
        visitor.unique_id = long(random.randint(0, 0x7fffffff))

    session = Session()
    event = Event(category=category, action=action, label=label, value=1)
    path = u"/" + u"/".join([category, action, label])
    page = Page(path.lower())

    tracker.add_custom_variable(CustomVariable(index=1, name='BazarrVersion', value=os.environ["BAZARR_VERSION"], scope=1))
    tracker.add_custom_variable(CustomVariable(index=2, name='PythonVersion', value=platform.python_version(), scope=1))
    if settings.general.getboolean('use_sonarr'):
        tracker.add_custom_variable(CustomVariable(index=3, name='SonarrVersion', value=sonarr_version, scope=1))
    if settings.general.getboolean('use_radarr'):
        tracker.add_custom_variable(CustomVariable(index=4, name='RadarrVersion', value=radarr_version, scope=1))
    tracker.add_custom_variable(CustomVariable(index=5, name='OSVersion', value=platform.platform(), scope=1))

    try:
        tracker.track_event(event, session, visitor)
        tracker.track_pageview(page, session, visitor)
    except:
        pass
    else:
        settings.analytics.visitor = base64.b64encode(pickle.dumps(visitor))
        with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
            settings.write(handle)
