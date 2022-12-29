# imports
import re
import enum
import requests
import logging
import numpy as np
from urllib import parse as urlparse

from subliminal.video import Movie

logger = logging.getLogger(__name__)

#constants
DEFAULT_HEADERS = {
            "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            'Origin': 'https://subtitrari.regielive.ro',
            'Accept-Language' : 'en-US,en;q=0.5',
            'Referer': 'https://subtitrari.regielive.ro',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
            }

REQUEST_TIMEOUT = 15

BASE_URL = "https://subtitrari.regielive.ro"
LITE_JSON_PATH = "/ajax/subtitrari/searchsuggest.php"
PAGE_SEARCH_PATH = "/cauta.html"
SEASON_URL = "/sezonul-%i/"

SUB_PAGE_EPISODE_PATTERN = r'(?ism)<h3>Episodul {episode}</h3>(.+?)</ul>'

SUB_PAGE_ZONE_MATCH = re.compile(r'(?ism)<div class="subtitrari">.*?<ul class="mt-6">(.+?)</ul>')
SUB_FILE_INFO_MATCH = re.compile(r'(?ism)id="sub_\d+">([^<]+)</span>.*?Nota ([0-9.]+)\s+(?:dintr-un (\w+)|din\s+([0-9]+)\s+)[^"]+">.*?<a href="([^\"]+)".+?</li>')
SEARCH_PAGE_MATCH = re.compile(r'(?ism)class="detalii\s[^>]{1}.+?<a href="([^"]+)"[^>]+?>([^<]+)</a>\s*<span.+?>\((\d{4})\)</span>')

#helpers
def title_match(s, t, ratio_calc = False):
    """ title_match:
        Tries to calculate the levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        This function is mainly copied from the Levenshtein package
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows,cols),dtype = int)

    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions    
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0
            else:
                # the cost of a substitution is 2 for distance the cost of a substitution is 1.
                if ratio_calc:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc:
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
    else:
        # This is the minimum number of edits needed to convert string a to string b
        return distance[row][col]

# models
@enum.unique
class SearchTypes(enum.Enum):
    Movie = 1
    Episode = 2


class RegieLiveAPI():
    'Main class that interfaces with regielive sub provider'
    video = None
    title = None
    session = None
    search_type = SearchTypes.Movie

    def __init__(self, video):
        'Constructor that needs a [Movie, Episode] object'
        self.video = video
        self.initialize()


    def initialize(self):
        'Instance initialization goes here'
        if isinstance(self.video, Movie):
            self.search_type = SearchTypes.Episode
            self.title = self.video.title
        else:
            self.title = self.video.series
        
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
    def search_video(self):
        'Main function that should be called to get sub data back'
        if self.video is None:
            return None

        if self.search_type == SearchTypes.Movie:
            return self.search_movie()
           
        return self.search_episode()

    def search_movie(self):
        'search a movie'
        results = self.search_lite_api()

        if not results:
            results = self.search_page()


    def search_episode(self):
        'search an episode'
        results = self.search_lite_api()

        if not results:
            results  = self.search_page()

        return results

    def search_page(self):
        """
        Scrape search the page for the title
        This does not take into consideration pagination
        since the titles should be pretty unique and this api
        is not a search engine.
        I will make the pagination too if this, later, turns out to be a problem
        Return a similar object to the lite api in order to be consistent
        """
        response = self.get_page(PAGE_SEARCH_PATH, {'s' : self.title })
        data = {'error' : True, 'data' : []}

        if response:
            m_iter = SEARCH_PAGE_MATCH.finditer(response)
            if m_iter:
                for m in m_iter:
                    data['data'].append({
                        'id' : RegieLiveAPI.get_id_from_url(m.group(1)),
                        'text' : m.group(2),
                        'url' : m.group(1),
                        'an': m.group(3)
                    })

        return data

    def search_lite_api(self):
        'Access the lite json api for info'
        response = self.get_page(LITE_JSON_PATH, {'s' : self.title }, True)

        if response is None:
            logger.warning("Regielive lite API failed to provide a proper reply")
            return None

        if response['error'] or not response['data']:
            logger.warning("Regielive API responded with no results!")
            logger.info(response)
            return None

        return self.parse_lite_results(response['data'])

    def parse_lite_results(self, data_arr):
        'Parses the results of our lite api request'
        result = map(self.filter_lite_results, data_arr)

        if not result:
            return None

        return result

    def filter_lite_results(self, input_data):
        'list generator for lite api results'
        for element in input_data:
            match_ratio = title_match(element['text'], self.title, True)
            if element['an'] == self.video.year and match_ratio > 0.9:
                yield element
            else:
                logger.info("No match for title %s year %i and \
                    returned title %s year %i match ration %f", self.title, self.video.year, element['text'], element['year'], match_ratio)

    def get_page(self, url, url_params, return_json = False):
        'Request a page'
        try:
            req = self.session.get(urlparse.urljoin(BASE_URL , url), params=url_params,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True)
            req.raise_for_status()

            if return_json:
                return req.json()

            return req.text
        except requests.exceptions.HTTPError as err:
            logger.exception("Failed to request url %s\n Error %s", url, err.strerror())

        return None

    @classmethod
    def get_id_from_url(cls, url):
        'get the movie rl id from page url'
        m = re.search(r'(?ms)(\d+)/', url)
        if m:
            return m.group(1)

        return 0
