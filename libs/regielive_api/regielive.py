# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ts=4 et sw=4 sts=4

# This utility should return a list of RegieLiveAPIData objects when queried
# by using a mix of json api search and page scraping in order to fetch data
# from Regielive website.
#
# This may break at anytime since regex is very sensitive to website structure changes
# for this in the future I might make the regex to load directly from github

# imports
import re
import enum
import logging
import requests
import numpy as np

from time import sleep
from hashlib import sha1
from subliminal.cache import region
from urllib import parse as urlparse
from subliminal.video import Episode

logger = logging.getLogger(__name__)

# class


class RegieLiveAPIData():
    'data returned class'
    title = ''
    rating = None
    download_url = ''

    def __init__(self, title, url, rating):
        self.title = title
        self.download_url = url
        self.rating = rating

    def __repr__(self):
        return "<RegieLiveAPIData: title = " + str(self.title) + "; download url = " + str(self.download_url) + "; rating = " + str(self.rating.rating) + "/" + str(self.rating.count) + ">"


class RegieLiveAPIRating():  # probably an extraneous class
    'rating for the subtitle'
    rating = 0
    count = 0

    def __init__(self, rating, count):
        if rating:
            self.rating = rating

        if not count:
            self.count = 0
        if count and type(count) == str and count.isnumeric():
            self.count = count
        elif count == 'vot':
            self.count = 1
        else:
            self.count = 0


# constants
CACHE_PREFIX = 'RL_API'

DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    'Origin': 'https://subtitrari.regielive.ro',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://subtitrari.regielive.ro',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}

REQUEST_TIMEOUT = 15

BASE_URL = "https://subtitrari.regielive.ro"
LITE_JSON_PATH = "/ajax/subtitrari/searchsuggest.php"
PAGE_SEARCH_PATH = "/cauta.html"
SEASON_URL = "sezonul-%i/"

SUB_PAGE_EPISODE_PATTERN = r'(?ism)<h3>Episodul %s</h3>(.+?)</ul>'
SUB_PAGE_MOVIE_MATCH = re.compile(
    r'(?ism)<div class="subtitrari">.*?<ul class="mt-6">(.+?)</ul>')

SUB_FILE_INFO_MATCH = re.compile(
    r'(?ism)id="sub_\d+">([^<]+)</span>.*?Nota ([0-9.]+)\s+(?:dintr-un\s+?(\w+)|din\s+?([0-9]+)\s*?)[^>].*?<a href="([^"]+)".+?</li>')
SEARCH_PAGE_MATCH = re.compile(
    r'(?ism)class="detalii\s[^>]{1}.+?<a href="([^"]+)"[^>]+?>([^<]+)</a>\s*<span.+?>\((\d{4})\)</span>')

# helpers


def title_match(s, t, ratio_calc=False):
    """ title_match:
        Tries to calculate the levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        This function is mainly copied from the Levenshtein package
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows, cols), dtype=int)

    for i in range(1, rows):
        for k in range(1, cols):
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
                                     # Cost of insertions
                                     distance[row][col-1] + 1,
                                     distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc:
        ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return ratio
    else:
        # This is the minimum number of edits needed to convert string a to string b
        return distance[row][col]

# models


@enum.unique
class SearchTypes(enum.Enum):
    'Search type based on video object received'
    Movie = 1
    Episode = 2


class RegieLiveSearchAPI():
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
        if isinstance(self.video, Episode):
            self.search_type = SearchTypes.Episode
            self.title = self.video.series
        else:
            self.title = self.video.title

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        logger.debug('Initialized new RegieLiveSearchAPI with search type %s of object %s',
                     self.search_type, str(self.video))

    def get_req_cookies(self):
        'Get cookies used for request'
        if self.session:
            return self.session.cookies

        return None

    def search_video(self):
        'Main function that should be called to get sub data back'
        if self.video is None:
            return None

        results = self.search_lite_api()

        if not results:
            sleep(2.0) #stagger request in order to no flood the server
            results = self.search_page()

        if not results or results['data'] is None:
            return None  # not logging since we can't get here without logging the reason elsewhere

        logger.debug(results)
        found_subs = self.parse_page(results)
        logger.debug(found_subs)

        return found_subs

    def parse_page(self, results):
        'fetch and parse episode/movie page'
        if len(results['data']) > 1:
            logger.warning("More than one page result for subtitle %s with data %s",
                           self.title,
                           str(results['data']))

        sub_list = None
        if self.search_type is SearchTypes.Movie:
            sub_list = self.parse_movie_pages(results['data'])
        else:
            sub_list = self.parse_episode_pages(results['data'])

        return sub_list

    def parse_movie_pages(self, sub_page_data):
        'Fetch and parse movie page data'
        sub_list = []
        for result in sub_page_data:
            extracted_subs = self.extract_movie_sub_block(
                self.get_page(result['url'], None))
            sub_data = self.parse_sub_block(extracted_subs)
            if sub_data:
                sub_list.extend(sub_data)
            else:
                logger.debug(
                    'Empty results from url %s with resulted block %s', result['url'], str(sub_data))

        return sub_list

    def parse_episode_pages(self, sub_page_data):
        'Fetch and parse episode pages'
        season = SEASON_URL % self.video.season
        url = ''
        sub_list = []
        for result in sub_page_data:
            url = urlparse.urljoin(result['url'], season)
            extracted_subs = self.extract_episode_sub_block(
                self.get_page(url, None))
            sub_data = self.parse_sub_block(extracted_subs)
            if sub_data:
                sub_list.extend(sub_data)
            else:
                logger.debug(
                    'Empty results from url %s with resulted block %s', url, str(sub_data))

        return sub_list

    def search_page(self):
        """
        Scrape search the page for the title
        This does not take into consideration pagination
        since the titles should be pretty unique and this api
        is not a search engine.
        I will make the pagination too if this, later, turns out to be a problem
        Return a similar object to the lite api in order to be consistent
        """
        cache_key = sha1(CACHE_PREFIX + self.title.encode("utf-8"), usedforsecurity=False).digest()
        cached_response = region.get(cache_key)
        if cached_response:
            logger.info("Found cached reply for search request %s", self.title)
            return cached_response

        response = self.get_api_page(PAGE_SEARCH_PATH, {'s': self.title})
        data = {'error': True, 'data': []}

        if response:
            m_iter = SEARCH_PAGE_MATCH.finditer(response)
            if m_iter:
                for m in m_iter:
                    data['data'].append({
                        'id': RegieLiveSearchAPI.get_id_from_url(m.group(1)),
                        'text': m.group(2),
                        'url': m.group(1),
                        'an': m.group(3)
                    })

        # could be more efficient doing this in the previous iteration
        data['data'] = self.parse_json_results(data['data'])

        if data['data'] and len(data['data']) > 0:
            data['error'] = False
            region.set(cache_key, data)

        return data

    def search_lite_api(self):
        'Access the lite json api for info'
        response = self.get_api_page(LITE_JSON_PATH, {'s': self.title}, True)

        if response is None:
            logger.warning(
                "Regielive lite API failed to provide a proper reply")
            return None

        if response['error'] or not response['data']:
            logger.warning("Regielive API responded with no results!")
            logger.info(response)
            return None

        response['data'] = self.parse_json_results(response['data'])

        return response

    def parse_json_results(self, data_arr):
        'Parses the results of our lite api request'
        if not data_arr:
            return None

        result = list(filter(self.json_result_filter, data_arr))

        if not result:
            return None

        return result

    def json_result_filter(self, element):
        'Filter function for json results'
        if not element:
            return False

        match_ratio = title_match(element['text'], self.title, True)
        if element['an'] == self.video.year and match_ratio > 0.9:
            return True

        logger.info("No match for title %s year %i and returned title %s year %i match ration %f",
                    self.title,
                    self.video.year,
                    element['text'],
                    element['an'],
                    match_ratio)
        return False

    def get_api_page(self, url, url_params, return_json=False):
        'request a page from RL API'
        return self.get_page(urlparse.urljoin(BASE_URL, url), url_params, return_json)

    def get_page(self, url, url_params, return_json=False):
        'Request a page'
        try:
            req = self.session.get(url, params=url_params,
                                   timeout=REQUEST_TIMEOUT,
                                   allow_redirects=True)
            req.raise_for_status()

            if return_json:
                return req.json()

            return req.text
        except requests.exceptions.HTTPError as err:
            logger.exception(
                "Failed to request url %s\n Error %s", url, str(err))

        return None

    def extract_movie_sub_block(self, page_html):
        'extract subtitles block from movie page'
        m = SUB_PAGE_MOVIE_MATCH.search(page_html)
        if m:
            return m.group(1)

        logger.info("Could not find subtitle block for Movie %s", self.title)
        return ''

    def extract_episode_sub_block(self, page_html):
        'extract subtitle from series page'
        episode_zone_regex = SUB_PAGE_EPISODE_PATTERN % self.video.episode
        m = None
        try:
            m = re.search(episode_zone_regex, page_html)
        except Exception as err:
            logger.debug(str(page_html))
            logger.exception(err)

        if m:
            return m.group(1)

        logger.info("Could not find episode %i for season %i of series %s",
                    self.video.episode,
                    self.video.season,
                    self.title)
        return ''

    def parse_sub_block(self, subs_block):
        'Parse sub block into subtitle objects'
        if subs_block is None:
            return None

        m_iter = SUB_FILE_INFO_MATCH.finditer(subs_block)
        sub_list = []
        if m_iter:
            for match in m_iter:
                sub_list.append(RegieLiveAPIData(match.group(1), match.group(
                    5), RegieLiveAPIRating(match.group(2), match.group(4))))
        else:
            logger.debug('No subtitles matched for sub block %s of title %s', str(
                subs_block), self.title)

        return sub_list

    @classmethod
    def get_id_from_url(cls, url):
        'get the movie rl id from page url'
        m = re.search(r'(?ms)(\d+)/', url)
        if m:
            return m.group(1)

        return 0
