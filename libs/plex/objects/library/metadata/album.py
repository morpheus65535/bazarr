from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import ChildrenContainer
from plex.objects.library.extra.genre import Genre
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.metadata.artist import Artist
from plex.objects.mixins.rate import RateMixin


class Album(Directory, Metadata, RateMixin):
    artist = Property(resolver=lambda: Album.construct_artist)
    genres = Property(resolver=lambda: Genre.from_node)

    index = Property(type=int)

    year = Property(type=int)
    originally_available_at = Property('originallyAvailableAt')

    track_count = Property('leafCount', int)
    viewed_track_count = Property('viewedLeafCount', int)

    def children(self):
        return self.client['library/metadata'].children(self.rating_key)

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',

            'title':        'parentTitle',
            'thumb':        'parentThumb'
        }

        return Artist.construct(client, node, attribute_map, child=True)


class AlbumChildrenContainer(ChildrenContainer):
    artist = Property(resolver=lambda: AlbumChildrenContainer.construct_artist)
    album = Property(resolver=lambda: AlbumChildrenContainer.construct_album)

    key = Property

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'title': 'grandparentTitle'
        }

        return Artist.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_album(client, node):
        attribute_map = {
            'index': 'parentIndex',

            'title': 'parentTitle',
            'year' : 'parentYear'
        }

        return Album.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(ChildrenContainer, self).__iter__():
            item.artist = self.artist
            item.album = self.album

            yield item
