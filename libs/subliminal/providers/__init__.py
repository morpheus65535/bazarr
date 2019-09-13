# -*- coding: utf-8 -*-
import logging

from bs4 import BeautifulSoup, FeatureNotFound
from six.moves.xmlrpc_client import SafeTransport

from ..video import Episode, Movie

logger = logging.getLogger(__name__)


class TimeoutSafeTransport(SafeTransport):
    """Timeout support for ``xmlrpc.client.SafeTransport``."""
    def __init__(self, timeout, *args, **kwargs):
        SafeTransport.__init__(self, *args, **kwargs)
        self.timeout = timeout

    def make_connection(self, host):
        c = SafeTransport.make_connection(self, host)
        c.timeout = self.timeout

        return c


class ParserBeautifulSoup(BeautifulSoup):
    """A ``bs4.BeautifulSoup`` that picks the first parser available in `parsers`.

    :param markup: markup for the ``bs4.BeautifulSoup``.
    :param list parsers: parser names, in order of preference.

    """
    def __init__(self, markup, parsers, **kwargs):
        # reject features
        if set(parsers).intersection({'fast', 'permissive', 'strict', 'xml', 'html', 'html5'}):
            raise ValueError('Features not allowed, only parser names')

        # reject some kwargs
        if 'features' in kwargs:
            raise ValueError('Cannot use features kwarg')
        if 'builder' in kwargs:
            raise ValueError('Cannot use builder kwarg')

        # pick the first parser available
        for parser in parsers:
            try:
                super(ParserBeautifulSoup, self).__init__(markup, parser, **kwargs)
                return
            except FeatureNotFound:
                pass

        raise FeatureNotFound


class Provider(object):
    """Base class for providers.

    If any configuration is possible for the provider, like credentials, it must take place during instantiation.

    :raise: :class:`~subliminal.exceptions.ConfigurationError` if there is a configuration error

    """
    #: Supported set of :class:`~babelfish.language.Language`
    languages = set()

    #: Supported video types
    video_types = (Episode, Movie)

    #: Required hash, if any
    required_hash = None

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.terminate()

    def initialize(self):
        """Initialize the provider.

        Must be called when starting to work with the provider. This is the place for network initialization
        or login operations.

        .. note::
            This is called automatically when entering the `with` statement

        """
        raise NotImplementedError

    def terminate(self):
        """Terminate the provider.

        Must be called when done with the provider. This is the place for network shutdown or logout operations.

        .. note::
            This is called automatically when exiting the `with` statement

        """
        raise NotImplementedError

    @classmethod
    def check(cls, video):
        """Check if the `video` can be processed.

        The `video` is considered invalid if not an instance of :attr:`video_types` or if the :attr:`required_hash` is
        not present in :attr:`~subliminal.video.Video.hashes` attribute of the `video`.

        :param video: the video to check.
        :type video: :class:`~subliminal.video.Video`
        :return: `True` if the `video` is valid, `False` otherwise.
        :rtype: bool

        """
        if not isinstance(video, cls.video_types):
            return False
        if cls.required_hash is not None and cls.required_hash not in video.hashes:
            return False

        return True

    def query(self, *args, **kwargs):
        """Query the provider for subtitles.

        Arguments should match as much as possible the actual parameters for querying the provider

        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`
        :raise: :class:`~subliminal.exceptions.ProviderError`

        """
        raise NotImplementedError

    def list_subtitles(self, video, languages):
        """List subtitles for the `video` with the given `languages`.

        This will call the :meth:`query` method internally. The parameters passed to the :meth:`query` method may
        vary depending on the amount of information available in the `video`.

        :param video: video to list subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to search for.
        :type languages: set of :class:`~babelfish.language.Language`
        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`
        :raise: :class:`~subliminal.exceptions.ProviderError`

        """
        raise NotImplementedError

    def download_subtitle(self, subtitle):
        """Download `subtitle`'s :attr:`~subliminal.subtitle.Subtitle.content`.

        :param subtitle: subtitle to download.
        :type subtitle: :class:`~subliminal.subtitle.Subtitle`
        :raise: :class:`~subliminal.exceptions.ProviderError`

        """
        raise NotImplementedError

    def __repr__(self):
        return '<%s [%r]>' % (self.__class__.__name__, self.video_types)
