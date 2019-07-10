# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ts=4 et sw=4 sts=4

# This file is part of Subscene-API.
#
# Subscene-API is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Subscene-API is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Python wrapper for Subscene subtitle database.

since Subscene doesn't provide an official API, I wrote
this script that does the job by parsing the website"s pages.
"""

# imports
import re

import enum
import sys
import requests
import time
import logging

is_PY2 = sys.version_info[0] < 3
if is_PY2:
    from contextlib2 import suppress
    from urllib2 import Request, urlopen
else:
    from contextlib import suppress
    from urllib2.request import Request, urlopen

from dogpile.cache.api import NO_VALUE
from subliminal.cache import region
from bs4 import BeautifulSoup, NavigableString


logger = logging.getLogger(__name__)

# constants
HEADERS = {
}
SITE_DOMAIN = "https://subscene.com"

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWeb"\
                     "Kit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"


ENDPOINT_RE = re.compile(ur'(?uis)<form.+?action="/subtitles/(.+)">.*?<input type="text"')


class NewEndpoint(Exception):
    pass


# utils
def soup_for(url, data=None, session=None, user_agent=DEFAULT_USER_AGENT):
    url = re.sub("\s", "+", url)
    if not session:
        r = Request(url, data=None, headers=dict(HEADERS, **{"User-Agent": user_agent}))
        html = urlopen(r).read().decode("utf-8")
    else:
        ret = session.post(url, data=data)
        ret.raise_for_status()
        html = ret.text
    return BeautifulSoup(html, "html.parser")


class AttrDict(object):
    def __init__(self, *attrs):
        self._attrs = attrs

        for attr in attrs:
            setattr(self, attr, "")

    def to_dict(self):
        return {k: getattr(self, k) for k in self._attrs}


# models
@enum.unique
class SearchTypes(enum.Enum):
    Exact = 1
    TvSerie = 2
    Popular = 3
    Close = 4


SectionsParts = {
    SearchTypes.Exact: "Exact",
    SearchTypes.TvSerie: "TV-Series",
    SearchTypes.Popular: "Popular",
    SearchTypes.Close: "Close"
}


class Subtitle(object):
    def __init__(self, title, url, language, owner_username, owner_url,
                 description, hearing_impaired):
        self.title = title
        self.url = url
        self.language = language
        self.owner_username = owner_username
        self.owner_url = owner_url
        self.description = description
        self.hearing_impaired = hearing_impaired

        self._zipped_url = None

    def __str__(self):
        return self.title

    @classmethod
    def from_rows(cls, rows):
        subtitles = []

        for row in rows:
            if row.td.a is not None and row.td.get("class", ["lazy"])[0] != "empty":
                subtitles.append(cls.from_row(row))

        return subtitles

    @classmethod
    def from_row(cls, row):
        attrs = AttrDict("title", "url", "language", "owner_username",
                         "owner_url", "description", "hearing_impaired")

        with suppress(Exception):
            attrs.title = row.find("td", "a1").a.find_all("span")[1].text \
                .strip()

        with suppress(Exception):
            attrs.url = SITE_DOMAIN + row.find("td", "a1").a.get("href")

        with suppress(Exception):
            attrs.language = row.find("td", "a1").a.find_all("span")[0].text \
                .strip()

        with suppress(Exception):
            attrs.owner_username = row.find("td", "a5").a.text.strip()

        with suppress(Exception):
            attrs.owner_page = SITE_DOMAIN + row.find("td", "a5").a \
                .get("href").strip()

        with suppress(Exception):
            attrs.description = row.find("td", "a6").div.text.strip()

        with suppress(Exception):
            attrs.hearing_impaired = bool(row.find("td", "a41"))

        return cls(**attrs.to_dict())

    @classmethod
    def get_zipped_url(cls, url, session=None):
        soup = soup_for(url, session=session)
        return SITE_DOMAIN + soup.find("div", "download").a.get("href")

    @property
    def zipped_url(self):
        if self._zipped_url:
            return self._zipped_url

        self._zipped_url = Subtitle.get_zipped_url(self.url)
        return self._zipped_url


class Film(object):
    def __init__(self, title, year=None, imdb=None, cover=None,
                 subtitles=None):
        self.title = title
        self.year = year
        self.imdb = imdb
        self.cover = cover
        self.subtitles = subtitles

    def __str__(self):
        return self.title

    @classmethod
    def from_url(cls, url, session=None):
        soup = soup_for(url, session=session)

        content = soup.find("div", "subtitles")
        header = content.find("div", "box clearfix")
        cover = None

        try:
            cover = header.find("div", "poster").img.get("src")
        except AttributeError:
            pass

        title = header.find("div", "header").h2.text[:-12].strip()

        imdb = header.find("div", "header").h2.find("a", "imdb").get("href")

        year = header.find("div", "header").ul.li.text
        year = int(re.findall(r"[0-9]+", year)[0])

        rows = content.find("table").tbody.find_all("tr")
        subtitles = Subtitle.from_rows(rows)

        return cls(title, year, imdb, cover, subtitles)


# functions
def section_exists(soup, section):
    tag_part = SectionsParts[section]

    try:
        headers = soup.find("div", "search-result").find_all("h2")
    except AttributeError:
        return False

    for header in headers:
        if tag_part in header.text:
            return True

    return False


def get_first_film(soup, section, year=None, session=None):
    tag_part = SectionsParts[section]
    tag = None

    headers = soup.find("div", "search-result").find_all("h2")
    for header in headers:
        if tag_part in header.text:
            tag = header
            break

    if not tag:
        return

    url = None

    if not year:
        url = SITE_DOMAIN + tag.findNext("ul").find("li").div.a.get("href")
    else:
        for t in tag.findNext("ul").findAll("li"):
            if isinstance(t, NavigableString) or not t.div:
                continue

            if str(year) in t.div.a.string:
                url = SITE_DOMAIN + t.div.a.get("href")
                break
        if not url:
            # fallback to non-year results
            logger.info("Falling back to non-year results as year wasn't found (%s)", year)
            url = SITE_DOMAIN + tag.findNext("ul").find("li").div.a.get("href")

    return Film.from_url(url, session=session)


def find_endpoint(session, content=None):
    endpoint = region.get("subscene_endpoint2")
    if endpoint is NO_VALUE:
        if not content:
            content = session.get(SITE_DOMAIN).text

        m = ENDPOINT_RE.search(content)
        if m:
            endpoint = m.group(1).strip()
            logger.debug("Switching main endpoint to %s", endpoint)
            region.set("subscene_endpoint2", endpoint)
    return endpoint


def search(term, release=True, session=None, year=None, limit_to=SearchTypes.Exact, throttle=0):
    # note to subscene: if you actually start to randomize the endpoint, we'll have to query your server even more

    if release:
        endpoint = "release"
    else:
        endpoint = find_endpoint(session)
        time.sleep(throttle)

    if not endpoint:
        logger.error("Couldn't find endpoint, exiting")
        return

    soup = soup_for("%s/subtitles/%s" % (SITE_DOMAIN, endpoint), data={"query": term},
                    session=session)

    if soup:
        if "Subtitle search by" in str(soup):
            rows = soup.find("table").tbody.find_all("tr")
            subtitles = Subtitle.from_rows(rows)
            return Film(term, subtitles=subtitles)

        for junk, search_type in SearchTypes.__members__.items():
            if section_exists(soup, search_type):
                return get_first_film(soup, search_type, year=year, session=session)

            if limit_to == search_type:
                return
