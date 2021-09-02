# -*- coding: utf-8 -*-

"""
tmdbsimple.movies
~~~~~~~~~~~~~~~~~
This module implements the Movies, Collections, Companies, Keywords, and
Reviews functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Movies(TMDB):
    """
    Movies functionality.

    See: https://developers.themoviedb.org/3/movies
    """
    BASE_PATH = 'movie'
    URLS = {
        'info': '/{id}',
        'account_states': '/{id}/account_states',
        'alternative_titles': '/{id}/alternative_titles',
        'changes': '/{id}/changes',
        'credits': '/{id}/credits',
        'external_ids': '/{id}/external_ids',
        'images': '/{id}/images',
        'keywords': '/{id}/keywords',
        'release_dates': '/{id}/release_dates',
        'videos': '/{id}/videos',
        'translations': '/{id}/translations',
        'recommendations': '/{id}/recommendations',
        'similar_movies': '/{id}/similar_movies',
        'reviews': '/{id}/reviews',
        'lists': '/{id}/lists',
        'latest': '/latest',
        'now_playing': '/now_playing',
        'popular': '/popular',
        'top_rated': '/top_rated',
        'upcoming': '/upcoming',
        'rating': '/{id}/rating',       # backward compatability
        'releases': '/{id}/releases',   # backward compatability
    }

    def __init__(self, id=0):
        super(Movies, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the primary information about a movie.

        Supports append_to_response. Read more about this at
        https://developers.themoviedb.org/3/getting-started/append-to-response.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def account_states(self, **kwargs):
        """
        Grab the following account states for a session:
            - Movie rating
            - If it belongs to your watchlist
            - If it belongs to your favourite list

        Args:
            session_id: see Authentication.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('account_states')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def alternative_titles(self, **kwargs):
        """
        Get all of the alternative titles for a movie.

        Args:
            country: (optional) ISO 3166-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('alternative_titles')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def changes(self, **kwargs):
        """
        Get the changes for a movie. By default only the last 24 hours are returned.

        You can query up to 14 days in a single query by using the start_date
        and end_date query parameters.

        Args:
            start_date: (optional) Expected format is 'YYYY-MM-DD'.
            end_date: (optional) Expected format is 'YYYY-MM-DD'.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('changes')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def credits(self, **kwargs):
        """
        Get the cast and crew for a movie.

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def external_ids(self, **kwargs):
        """
        Get the external ids for a movie. We currently support the following
        external sources.

        Media Databases - IMDb
        Social IDs - Facebok, Instagram, Twitter

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('external_ids')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images that belong to a movie.

        Querying images with a language parameter will filter the results. If
        you want to include a fallback language (especially useful for
        backdrops) you can use the include_image_language parameter. This
        should be a comma seperated value like so:
        include_image_language=en,null.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.
            include_image_language: (optional) Comma separated, a valid
                                    ISO 69-1.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def keywords(self):
        """
        Get the keywords that have been added to a movie.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('keywords')

        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response

    def release_dates(self, **kwargs):
        """
        Get the release date along with the certification for a movie.

        Release dates support different types:

            1. Premiere
            2. Theatrical (limited)
            3. Theatrical
            4. Digital
            5. Physical
            6. TV

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('release_dates')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def videos(self, **kwargs):
        """
        Get the videos that have been added to a movie.

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('videos')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def translations(self, **kwargs):
        """
        Get a list of translations that have been created for a movie.

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('translations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def recommendations(self, **kwargs):
        """
        Get a list of recommended movies for a movie.

        Args:
            language: (optional) ISO 639-1 code.
            page: (optional) Minimum value of 1.  Expected value is an integer.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('recommendations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def similar_movies(self, **kwargs):
        """
        Get a list of similar movies. This is not the same as the
        "Recommendation" system you see on the website.

        These items are assembled by looking at keywords and genres.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('similar_movies')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def reviews(self, **kwargs):
        """
        Get the user reviews for a movie.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('reviews')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def lists(self, **kwargs):
        """
        Get a list of lists that this movie belongs to.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('lists')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rating(self, **kwargs):
        """
        Rate a movie.

        A valid session or guest session ID is required. You can read more
        about how this works at
        https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id.

        Args:
            session_id: see Authentication.
            guest_session_id: see Authentication.
            value: Rating value.

        Returns:
            A dict representation of the JSON returned from the API.
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
        Get the most newly created movie. This is a live response and will
        continuously change.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_path('latest')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def now_playing(self, **kwargs):
        """
        Get a list of movies in theatres. This is a release type query that
        looks for all movies that have a release type of 2 or 3 within the
        specified date range.

        You can optionally specify a region prameter which will narrow the
        search to only look for theatrical release dates within the specified
        country.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_path('now_playing')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def popular(self, **kwargs):
        """
        Get a list of the current popular movies on TMDb. This list updates
        daily.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_path('popular')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def top_rated(self, **kwargs):
        """
        Get the top rated movies on TMDb.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_path('top_rated')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def upcoming(self, **kwargs):
        """
        Get a list of upcoming movies in theatres. This is a release type query
        that looks for all movies that have a release type of 2 or 3 within the
        specified date range.

        You can optionally specify a region prameter which will narrow the
        search to only look for theatrical release dates within the specified
        country.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_path('upcoming')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    # backward compatability
    def releases(self, **kwargs):
        """
        Get the release date and certification information by country for a
        specific movie id.

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('releases')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Collections(TMDB):
    """
    Collections functionality.

    See: https://developers.themoviedb.org/3/collections
    """
    BASE_PATH = 'collection'
    URLS = {
        'info': '/{id}',
        'images': '/{id}/images',
        'translations': '/{id}/translations',
    }

    def __init__(self, id):
        super(Collections, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get collection details by id.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images for a collection by id.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.
            include_image_language: (optional) Comma separated, a valid
            ISO 69-1.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def translations(self, **kwargs):
        """
        Get a list of the translations for a collection by id.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('translations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Companies(TMDB):
    """
    Companies functionality.

    See: https://developers.themoviedb.org/3/companies
    """
    BASE_PATH = 'company'
    URLS = {
        'info': '/{id}',
        'alternative_names': '/{id}/alternative_names',
        'images': '/{id}/images',
        'movies': '/{id}/movies',    # backward compatability
    }

    def __init__(self, id=0):
        super(Companies, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get a companies details by id.

        Args:
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def alternative_names(self, **kwargs):
        """
        Get the alternative names of a company.

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
        Get a company's logos by id.

        There are two image formats that are supported for companies, PNG's and
        SVG's. You can see which type the original file is by looking at the
        file_type field. We prefer SVG's as they are resolution independent and
        as such, the width and height are only there to reflect the original
        asset that was uploaded.  An SVG can be scaled properly beyond those
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

    # backward compatability
    def movies(self, **kwargs):
        """
        Get the list of movies associated with a particular company.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any movie method.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('movies')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Keywords(TMDB):
    """
    Keywords functionality.

    See: https://developers.themoviedb.org/3/keywords
    """
    BASE_PATH = 'keyword'
    URLS = {
        'info': '/{id}',
        'movies': '/{id}/movies',
    }

    def __init__(self, id):
        super(Keywords, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the details of a keyword.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def movies(self, **kwargs):
        """
        Get the movies that belong to a keyword.

        We highly recommend using movie discover instead of this method as it
        is much more flexible.

        Args:
            page: (optional) Minimum value of 1.  Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('movies')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Reviews(TMDB):
    """
    Reviews functionality.

    See: https://developers.themoviedb.org/3/reviews
    """
    BASE_PATH = 'review'
    URLS = {
        'info': '/{id}',
    }

    def __init__(self, id):
        super(Reviews, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the review details by id.

        Returns:
            A dict representation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response
