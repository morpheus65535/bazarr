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
                          'use_tag_search': settings.opensubtitles.getboolean('use_tag_search'),
                          'only_foreign': False, # fixme
                          'also_foreign': False, # fixme
                          'is_vip': settings.opensubtitles.getboolean('vip'),
                          'use_ssl': settings.opensubtitles.getboolean('ssl'),
                          'timeout': int(settings.opensubtitles.timeout) or 15,
                          'skip_wrong_fps': settings.opensubtitles.getboolean('skip_wrong_fps'),
                       },
        'podnapisi': {
            'only_foreign': False, # fixme
            'also_foreign': False, # fixme
        },
        'subscene': {
            'only_foreign': False, # fixme
        },
        'legendastv': {'username': settings.legendastv.username,
                       'password': settings.legendastv.password,
                    },
        'assrt': {'token': settings.assrt.token, }
    }
    
    
    return providers_auth
