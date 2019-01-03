# coding=utf-8
from config import settings


def get_providers():
    providers_list = []
    if settings.general.enabled_providers:
        for provider in settings.general.enabled_providers.lower().split(','):
            providers_list.append(provider)
    else:
        providers_list = None

    return providers_list


def get_providers_auth():
    providers_auth = {
     'addic7ed': {'username': settings.addic7ed.username,
                  'password': settings.addic7ed.password,
                  'use_random_agents': settings.addic7ed.getboolean('random_agents'),
                  },
     'opensubtitles': {'username': settings.opensubtitles.username,
                       'password': settings.opensubtitles.password,
                       'is_vip': settings.opensubtitles.getboolean('vip'),
                       'use_ssl': settings.opensubtitles.getboolean('ssl'),
                       'timeout': int(settings.opensubtitles.timeout) or 15,
                       },
     'legendastv': {'username': settings.legendastv.username,
                    'password': settings.legendastv.password,
                    }
     }
    
    return providers_auth
