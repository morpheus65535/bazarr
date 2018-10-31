from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import LeavesContainer, ChildrenContainer
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.rate import RateMixin


class Show(Directory, Metadata, RateMixin):
    index = Property(type=int)
    duration = Property(type=int)

    studio = Property
    content_rating = Property('contentRating')

    banner = Property
    theme = Property

    year = Property(type=int)
    originally_available_at = Property('originallyAvailableAt')

    season_count = Property('childCount', int)

    episode_count = Property('leafCount', int)
    viewed_episode_count = Property('viewedLeafCount', int)

    view_count = Property('viewCount', int)

    def all_leaves(self):
        return self.client['library/metadata'].all_leaves(self.rating_key)

    def children(self):
        return self.client['library/metadata'].children(self.rating_key)


class ShowChildrenContainer(ChildrenContainer):
    show = Property(resolver=lambda: ShowLeavesContainer.construct_show)

    key = Property
    summary = Property

    banner = Property
    theme = Property

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'index': 'parentIndex',

            'title': 'parentTitle',
            'year' : 'parentYear'
        }

        return Show.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(ChildrenContainer, self).__iter__():
            item.show = self.show

            yield item


class ShowLeavesContainer(LeavesContainer):
    show = Property(resolver=lambda: ShowLeavesContainer.construct_show)

    key = Property

    banner = Property
    theme = Property

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'index': 'parentIndex',

            'title': 'parentTitle',
            'year' : 'parentYear'
        }

        return Show.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(LeavesContainer, self).__iter__():
            item.show = self.show

            yield item
