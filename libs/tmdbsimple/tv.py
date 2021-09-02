# -*- coding: utf-8 -*-

"""
tmdbsimple.tv
~~~~~~~~~~~~~
This module implements the TV, TV Seasons, TV Episodes, and Networks
functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class TV(TMDB):
    """
    TV functionality.

    See: https://developers.themoviedb.org/3/tv
    """
    BASE_PATH = 'tv'
    URLS = {
        'info': '/{id}',
        'account_states': '/{id}/account_states',
        'alternative_titles': '/{id}/alternative_titles',
        'content_ratings': '/{id}/content_ratings',
        'credits': '/{id}/credits',
        'episode_groups': '/{id}/episode_groups',
        'external_ids': '/{id}/external_ids',
        'images': '/{id}/images',
        'keywords': '/{id}/keywords',
        'recommendations': '/{id}/recommendations',
        'reviews': '/{id}/reviews',
        'screened_theatrically': '/{id}/screened_theatrically',
        'similar': '/{id}/similar',
        'translations': '/{id}/translations',
        'videos': '/{id}/videos',
        'rating': '/{id}/rating',
        'latest': '/latest',
        'airing_today': '/airing_today',
        'on_the_air': '/on_the_air',
        'popular': '/popular',
        'top_rated': '/top_rated',
    }

    def __init__(self, id=0):
        super(TV, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the primary TV show details by id.

        Supports append_to_response. Read more about this at
        https://developers.themoviedb.org/3/getting-started/append-to-response.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any TV series
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def account_states(self, **kwargs):
        """
        Grab the following account states for a session:
            - TV show rating
            - If it belongs to your watchlist
            - If it belongs to your favourite list

        Args:
            language: (optional) ISO 3166-1 code.
            append_to_response: (optional) Comma separated, any tv method.
        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('account_states')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def alternative_titles(self, **kwargs):
        """
        Returns all of the alternative titles for a TV show.

        Args:
            language: (optional) ISO 3166-1 code.
            append_to_response: (optional) Comma separated, any tv method.
        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('alternative_titles')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def content_ratings(self, **kwargs):
        """
        Get the list of content ratings (certifications) that have been added
        to a TV show.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any collection
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('content_ratings')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def credits(self, **kwargs):
        """
        Get the credits (cast and crew) that have been added to a TV show.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any collection
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def episode_groups(self, **kwargs):
        """
        Get all of the episode groups that have been created for a TV show.
        With a group ID you can call the get TV episode group details  method.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('episode_groups')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def external_ids(self, **kwargs):
        """
        Get the external ids for a TV show. We currently support the following
        external sources.

        Media Databases: IMDb ID, TVDB ID, Freebase MID*, Freebase ID*, TVRage
        ID*
        Social IDs: Facebook, Instagram, Twitter

        *Defunct or no longer available as a service.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('external_ids')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images that belong to a TV show.

        Querying images with a language parameter will filter the results. If
        you want to include a fallback language (especially useful for
        backdrops) you can use the include_image_language parameter. This
        should be a comma seperated value like so:
        include_image_language=en,null.

        Args:
            language: (optional) ISO 639 code.
            include_image_language: (optional) Comma separated, a valid
                                    ISO 69-1.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def keywords(self, **kwargs):
        """
        Get the keywords that have been added to a TV show.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('keywords')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def recommendations(self, **kwargs):
        """
        Get the list of TV show recommendations for this item.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('recommendations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def reviews(self, **kwargs):
        """
        Get the reviews for a TV show.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('reviews')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def screened_theatrically(self, **kwargs):
        """
        Get a list of seasons or episodes that have been screened in a film
        festival or theatre.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('screened_theatrically')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def similar(self, **kwargs):
        """
        Get a list of similar TV shows. These items are assembled by looking at
        keywords and genres.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any TV method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('similar')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def translations(self, **kwargs):
        """
        Get a list of the translations that exist for a TV show.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('translations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def videos(self, **kwargs):
        """
        Get the videos that have been added to a TV show.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('videos')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rating(self, **kwargs):
        """
        Rate a TV show.

        A valid session or guest session ID is required. You can read more
        about how this works at
        https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id.

        Args:
            session_id: see Authentication.
            guest_session_id: see Authentication.
            value: Rating value.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('rating')

        payload = {
            'value': kwargs.pop('value', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def latest(self, **kwargs):
        """
        Get the most newly created TV show. This is a live response and will
        continuously change.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('latest')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def airing_today(self, **kwargs):
        """
        Get a list of TV shows that are airing today. This query is purely day
        based as we do not currently support airing times.

        You can specify a timezone to offset the day calculation. Without a
        specified timezone, this query defaults to EST (Eastern Time
        UTC-05:00).

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639 code.
            timezone: (optional) Valid value from the list of timezones.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('airing_today')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def on_the_air(self, **kwargs):
        """
        Get a list of shows that are currently on the air.

        This query looks for any TV show that has an episode with an air date
        in the next 7 days.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('on_the_air')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def popular(self, **kwargs):
        """
        Get a list of the current popular TV shows on TMDb. This list updates
        daily.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('popular')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def top_rated(self, **kwargs):
        """
        Get a list of the top rated TV shows on TMDb.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('top_rated')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class TV_Seasons(TMDB):
    """
    TV Seasons functionality.

    See: https://developers.themoviedb.org/3/tv-seasons
    """
    BASE_PATH = 'tv/{tv_id}/season/{season_number}'
    URLS = {
        'info': '',
        'account_states': '/account_states',
        'credits': '/credits',
        'external_ids': '/external_ids',
        'images': '/images',
        'videos': '/videos',
    }

    def __init__(self, tv_id, season_number):
        super(TV_Seasons, self).__init__()
        self.tv_id = tv_id
        self.season_number = season_number

    def info(self, **kwargs):
        """
        Get the TV season details by id.

        Supports append_to_response. Read more about this at
        https://developers.themoviedb.org/3/getting-started/append-to-response.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any TV series
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def account_states(self, **kwargs):
        """
        Returns all of the user ratings for the season's episodes.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any TV series
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('account_states')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def credits(self, **kwargs):
        """
        Get the credits for TV season.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def external_ids(self, **kwargs):
        """
        Get the external ids for a TV season. We currently support the
        following external sources.

        Media Databases: TVDB ID, Freebase MID*, Freebase ID*, TVRage ID*

        *Defunct or no longer available as a service.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('external_ids')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images that belong to a TV season.

        Querying images with a language parameter will filter the results. If
        you want to include a fallback language (especially useful for
        backdrops) you can use the include_image_language parameter. This
        should be a comma seperated value like so:
        include_image_language=en,null.

        Args:
            language: (optional) ISO 639 code.
            include_image_language: (optional) Comma separated, a valid
                                    ISO 69-1.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def videos(self, **kwargs):
        """
        Get the videos that have been added to a TV season.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_path('videos')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class TV_Episodes(TMDB):
    """
    TV Episodes functionality.

    See: https://developers.themoviedb.org/3/tv-episodes
    """
    BASE_PATH = 'tv/{tv_id}/season/{season_number}/episode/{episode_number}'
    URLS = {
        'info': '',
        'account_states': '/account_states',
        'credits': '/credits',
        'external_ids': '/external_ids',
        'images': '/images',
        'translations': '/translations',
        'rating': '/rating',
        'videos': '/videos',
    }

    def __init__(self, tv_id, season_number, episode_number):
        super(TV_Episodes, self).__init__()
        self.tv_id = tv_id
        self.season_number = season_number
        self.episode_number = episode_number

    def info(self, **kwargs):
        """
        Get the TV episode details by id.

        Supports append_to_response. Read more about this at
        https://developers.themoviedb.org/3/getting-started/append-to-response.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any TV series
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def account_states(self, **kwargs):
        """
        Get your rating for an episode.

        Args:
            language: (optional) ISO 639 code.
            append_to_response: (optional) Comma separated, any TV series
                                method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('account_states')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def credits(self, **kwargs):
        """
        Get the credits (cast, crew and guest stars) for a TV episode.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def external_ids(self, **kwargs):
        """
        Get the external ids for a TV episode. We currently support the
        following external sources.

        External Sources: IMDb ID, TVDB ID, Freebase MID*, Freebase ID*, TVRage
        ID*

        *Defunct or no longer available as a service.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path(
            'external_ids')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images that belong to a TV episode.

        Querying images with a language parameter will filter the results. If
        you want to include a fallback language (especially useful for
        backdrops) you can use the include_image_language parameter. This
        should be a comma seperated value like so:
        include_image_language=en,null.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def translations(self, **kwargs):
        """
        Get the translation data for an episode.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('translations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rating(self, **kwargs):
        """
        Rate a TV episode.

        A valid session or guest session ID is required. You can read more
        about how this works at
        https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id.

        Args:
            session_id: see Authentication.
            guest_session_id: see Authentication.
            value: Rating value.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('rating')

        payload = {
            'value': kwargs.pop('value', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def videos(self, **kwargs):
        """
        Get the videos that have been added to a TV episode.

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_tv_id_season_number_episode_number_path('videos')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class TV_Episode_Groups(TMDB):
    """
    TV Episode Groups functionality.

    See: https://developers.themoviedb.org/3/tv-episode-groups
    """
    BASE_PATH = 'tv/episode_group'
    URLS = {
        'info': '/{id}',
    }

    def __init__(self, id):
        super(TV_Episode_Groups, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the details of a TV episode group. Groups support 7 different types
        which are enumerated as the following:
            1. Original air date
            2. Absolute
            3. DVD
            4. Digital
            5. Story arc
            6. Production
            7. TV

        Args:
            language: (optional) ISO 639 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class TV_Changes(TMDB):
    """
    Changes functionality for TV Series, Season and Episode.

    See: https://developers.themoviedb.org/3/tv/get-tv-changes
         https://developers.themoviedb.org/3/tv-seasons/get-tv-season-changes
         https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-changes
    """
    BASE_PATH = 'tv'
    URLS = {
        'series': '/{id}/changes',             # id => tv_id
        'season': '/season/{id}/changes',      # id => season_id
        'episode': '/episode/{id}/changes',    # id => episode_id
    }

    def __init__(self, id=0):
        super(TV_Changes, self).__init__()
        self.id = id

    def series(self, **kwargs):
        """
        Get the changes for a TV show. By default only the last 24 hours are returned.

        You can query up to 14 days in a single query by using the start_date
        and end_date query parameters.

        TV show changes are different than movie changes in that there are some
        edits on seasons and episodes that will create a change entry at the
        show level. These can be found under the season and episode keys. These
        keys will contain a series_id and episode_id. You can use the season
        changes and episode changes methods to look these up individually.

        Args:
            start_date: (optional) Expected format is 'YYYY-MM-DD'.
            end_date: (optional) Expected format is 'YYYY-MM-DD'.
            page: (optional) Minimum 1, maximum 1000.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('series')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def season(self, **kwargs):
        """
        Get the changes for a TV season. By default only the last 24 hours are returned.

        You can query up to 14 days in a single query by using the start_date
        and end_date query parameters.

        Args:
            start_date: (optional) Expected format is 'YYYY-MM-DD'.
            end_date: (optional) Expected format is 'YYYY-MM-DD'.
            page: (optional) Minimum 1, maximum 1000.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('season')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def episode(self, **kwargs):
        """
        Get the changes for a TV episode. By default only the last 24 hours are returned.

        You can query up to 14 days in a single query by using the start_date
        and end_date query parameters.

        Args:
            start_date: (optional) Expected format is 'YYYY-MM-DD'.
            end_date: (optional) Expected format is 'YYYY-MM-DD'.
            page: (optional) Minimum 1, maximum 1000.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('episode')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Networks(TMDB):
    """
    Networks functionality.

    See: https://developers.themoviedb.org/3/networks
    """
    BASE_PATH = 'network'
    URLS = {
        'info': '/{id}',
        'alternative_names': '/{id}/alternative_names',
        'images': '/{id}/images',
    }

    def __init__(self, id):
        super(Networks, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the details of a network.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def alternative_names(self, **kwargs):
        """
        Get the alternative names of a network.

        Args:

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('alternative_names')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get a TV network logos by id.

        There are two image formats that are supported for networks, PNG's and
        SVG's. You can see which type the original file is by looking at the
        file_type field. We prefer SVG's as they are resolution independent and
        as such, the width and height are only there to reflect the original
        asset that was uploaded. An SVG can be scaled properly beyond those
        dimensions if you call them as a PNG.

        For more information about how SVG's and PNG's can be used, take a read
        through https://developers.themoviedb.org/3/getting-started/images.

        Args:

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response
