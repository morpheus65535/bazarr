# coding=utf-8
import os
import subliminal
import base64
import zlib
from subliminal import __short_version__
from subliminal.refiners.omdb import OMDBClient, refine as refine_orig, Episode, Movie
from subliminal_patch.http import TimeoutSession


class SZOMDBClient(OMDBClient):
    def __init__(self, version=1, session=None, headers=None, timeout=10):
        if not session:
            session = TimeoutSession(timeout=timeout)
        super(SZOMDBClient, self).__init__(version=version, session=session, headers=headers, timeout=timeout)

    def get_params(self, params):
        self.session.params['apikey'] = \
            zlib.decompress(base64.b16decode(os.environ['U1pfT01EQl9LRVk']))\
            .decode('cm90MTM=\n'.decode("base64")) \
            .decode('YmFzZTY0\n'.decode("base64")).split("x")[0]
        return dict(self.session.params, **params)

    def get(self, id=None, title=None, type=None, year=None, plot='short', tomatoes=False):
        # build the params
        params = {}
        if id:
            params['i'] = id
        if title:
            params['t'] = title
        if not params:
            raise ValueError('At least id or title is required')
        params['type'] = type
        params['y'] = year
        params['plot'] = plot
        params['tomatoes'] = tomatoes

        # perform the request
        r = self.session.get(self.base_url, params=self.get_params(params))
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j['Response'] == 'False':
            return None

        return j

    def search(self, title, type=None, year=None, page=1):
        # build the params
        params = {'s': title, 'type': type, 'y': year, 'page': page}

        # perform the request
        r = self.session.get(self.base_url, params=self.get_params(params))
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j['Response'] == 'False':
            return None

        return j


def refine(video, **kwargs):
    refine_orig(video, **kwargs)
    if isinstance(video, Episode) and video.series_imdb_id:
        video.series_imdb_id = video.series_imdb_id.strip()
    elif isinstance(video, Movie) and video.imdb_id:
        video.imdb_id = video.imdb_id.strip()


omdb_client = SZOMDBClient(headers={'User-Agent': 'Subliminal/%s' % __short_version__})
subliminal.refiners.omdb.omdb_client = omdb_client
