# coding=utf-8

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'subliminal_patch', 'enzyme', 'guessit', 'subzero', 'libfilebot',
                           'cloudscraper']
PERSONAL_MEDIA_IDENTIFIER = "com.plexapp.agents.none"
PLUGIN_IDENTIFIER_SHORT = "subzero"
PLUGIN_IDENTIFIER = "com.plexapp.agents.%s" % PLUGIN_IDENTIFIER_SHORT
PLUGIN_NAME = "Sub-Zero"
PREFIX = "/video/%s" % PLUGIN_IDENTIFIER_SHORT

TITLE = "%s Subtitles" % PLUGIN_NAME
ART      = 'art-default.jpg'
ICON     = 'icon-default.jpg'
ICON_SUB = 'icon-sub.jpg'

DEFAULT_TIMEOUT = 15


# media types as on https://github.com/Arcanemagus/plex-api/wiki/MediaTypes
MOVIE = 1
SHOW = 2
SEASON = 3
EPISODE = 4
TRAILER = 5
COMIC = 6
PERSON = 7
ARTIST = 8
ALBUM = 9
TRACK = 10
PHOTO_ALBUM = 11
PICTURE = 12
PHOTO = 13
CLIP = 14
PLAYLIST_ITEM = 15

MEDIA_TYPE_TO_STRING = {
    MOVIE: "movie",
    SHOW: "show"
}


mode_map = {
    "a": "auto",
    "m": "manual",
    "b": "auto-better"
}