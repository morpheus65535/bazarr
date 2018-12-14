# coding=utf-8
import os
import configparser

from get_argv import config_dir


class _ConfigSection(object):
    """Hold settings for a section of the configuration file."""

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            raise AttributeError('No "%s" setting in section.' % attr)

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return str(tuple(self.__dict__.keys()))


def read(config_file):
    """Read settings from file and return a dot notation object."""
    config = configparser.ConfigParser()
    config.read(unicode(config_file))

    dotini = _ConfigSection()

    for section in config.sections():

        s = _ConfigSection()
        for key, value in config.items(section):
            if value == "True":
                value = True
            elif value == "False":
                value = False
            setattr(s, key, value)

        setattr(dotini, section, s)

    return dotini


settings = read(os.path.join(os.path.join(config_dir, 'config', 'config.ini')))

# sonarr url
if settings.sonarr.ssl:
    protocol_sonarr = "https"
else:
    protocol_sonarr = "http"

if settings.sonarr.base_url == '':
    settings.sonarr.base_url = "/"
if not settings.sonarr.base_url.startswith("/"):
    settings.sonarr.base_url = "/" + settings.sonarr.base_url
if settings.sonarr.base_url.endswith("/"):
    settings.sonarr.base_url = settings.sonarr.base_url[:-1]

url_sonarr = protocol_sonarr + "://" + settings.sonarr.ip + ":" + settings.sonarr.port + settings.sonarr.base_url
url_sonarr_short = protocol_sonarr + "://" + settings.sonarr.ip + ":" + settings.sonarr.port

# radarr url
if settings.radarr.ssl:
    protocol_radarr = "https"
else:
    protocol_radarr = "http"

if settings.radarr.base_url == '':
    settings.radarr.base_url = "/"
if not settings.radarr.base_url.startswith("/"):
    settings.radarr.base_url = "/" + settings.radarr.base_url
if settings.radarr.base_url.endswith("/"):
    settings.radarr.base_url = settings.radarr.base_url[:-1]

url_radarr = protocol_radarr + "://" + settings.radarr.ip + ":" + settings.radarr.port + settings.radarr.base_url
url_radarr_short = protocol_radarr + "://" + settings.radarr.ip + ":" + settings.radarr.port
