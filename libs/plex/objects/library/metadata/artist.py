from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import LeavesContainer, ChildrenContainer
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.rate import RateMixin


class Artist(Directory, Metadata, RateMixin):
    index = Property(type=int)

    def all_leaves(self):
        return self.client['library/metadata'].all_leaves(self.rating_key)

    def children(self):
        return self.client['library/metadata'].children(self.rating_key)


class ArtistChildrenContainer(ChildrenContainer):
    artist = Property(resolver=lambda: ArtistChildrenContainer.construct_artist)

    key = Property
    summary = Property

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'index': 'parentIndex',
            'title': 'parentTitle'
        }

        return Artist.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(ChildrenContainer, self).__iter__():
            item.artist = self.artist

            yield item


class ArtistLeavesContainer(LeavesContainer):
    artist = Property(resolver=lambda: ArtistLeavesContainer.construct_artist)

    key = Property

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'index': 'parentIndex',
            'title': 'parentTitle'
        }

        return Artist.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(LeavesContainer, self).__iter__():
            item.artist = self.artist

            yield item
