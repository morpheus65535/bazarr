# imports
import re
import enum
import sys
import requests
import logging
from subliminal.video import Movie

is_PY2 = sys.version_info[0] < 3
if is_PY2:
    from contextlib2 import suppress
    from urllib2 import Request, urlopen
else:
    from contextlib import suppress
    from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

#constants
HEADERS = { "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" }
            
BASE_URL = "https://subtitrari.regielive.ro"
LITE_JSON_PATH = "/ajax/subtitrari/searchsuggest.php"
PAGE_SEARCH_PATH = "/cauta.html"
SEASON_URL = "/sezonul-{season}/"

SUB_PAGE_EPISODE_PATTERN = r'(?ism)<h3>Episodul {episode}</h3>(.+?)</ul>'

SUB_PAGE_ZONE_MATCH = re.compile(r'(?ism)<div class="subtitrari">.*?<ul class="mt-6">(.+?)</ul>')
SUB_FILE_INFO_MATCH = re.compile(r'(?ism)id="sub_\d+">([^<]+)</span>.*?Nota ([0-9.]+)\s+(?:dintr-un (\w+)|din\s+([0-9]+)\s+)[^"]+">.*?<a href="([^\"]+)".+?</li>')
SEARCH_PAGE_MATCH = re.compile(r'(?ism)class="detalii\s*">.+?<a href="([^"]+)"\s.+?>([^<]+)<\/a>\s*<span .+?>\((\d+)\)<\/span>')

# models
@enum.unique
class SearchTypes(enum.Enum):
    Movie = 1
    Episode = 2

class RegieLiveAPI(object):
    video = None
    searchType = SearchTypes.Movie

    def __init__(self, video):
        self.video = video;
        self.initialize()


    def initialize(self):
        if isinstance(self.video, Movie):
            self.searchType = SearchTypes.Episode
        
    def search_video(self):
        if video is None:
            return None

        if self.searchType == SearchTypes.Movie:
            return self.search_movie()
            
        return self.search_episode()

    def search_movie():
        pass

    def search_episode():
        pass;