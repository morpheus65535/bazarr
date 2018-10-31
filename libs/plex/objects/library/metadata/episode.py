from plex.objects.core.base import Property
from plex.objects.library.metadata.season import Season
from plex.objects.library.metadata.show import Show
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.video import Video
from plex.objects.mixins.rate import RateMixin
from plex.objects.mixins.scrobble import ScrobbleMixin


class Episode(Video, Metadata, RateMixin, ScrobbleMixin):
    show = Property(resolver=lambda: Episode.construct_show)
    season = Property(resolver=lambda: Episode.construct_season)

    index = Property(type=int)

    studio = Property
    audience_rating = Property('audienceRating', float)
    content_rating = Property('contentRating')

    year = Property(type=int)
    originally_available_at = Property('originallyAvailableAt')

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'key':          'grandparentKey',
            'ratingKey':    'grandparentRatingKey',

            'title':        'grandparentTitle',

            'art':          'grandparentArt',
            'theme':        'grandparentTheme',
            'thumb':        'grandparentThumb'
        }

        return Show.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_season(client, node):
        attribute_map = {
            'index':        'parentIndex',
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',

            'thumb':        'parentThumb'
        }

        return Season.construct(client, node, attribute_map, child=True)
