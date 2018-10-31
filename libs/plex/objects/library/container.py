from plex.core.helpers import flatten, to_iterable
from plex.objects.core.base import Property
from plex.objects.container import Container
from plex.objects.library.section import Section


class MediaContainer(Container):
    section = Property(resolver=lambda: MediaContainer.construct_section)

    title1 = Property
    title2 = Property

    identifier = Property

    art = Property
    thumb = Property

    view_group = Property('viewGroup')
    view_mode = Property('viewMode', int)

    media_tag_prefix = Property('mediaTagPrefix')
    media_tag_version = Property('mediaTagVersion')

    size = Property('size', int)
    total_size = Property('totalSize', int)

    allow_sync = Property('allowSync', bool)
    mixed_parents = Property('mixedParents', bool)
    no_cache = Property('nocache', bool)
    sort_asc = Property('sortAsc', bool)

    @staticmethod
    def construct_section(client, node):
        attribute_map = {
            'key': 'librarySectionID',
            'uuid': 'librarySectionUUID',
            'title': 'librarySectionTitle'
        }

        return Section.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(MediaContainer, self).__iter__():
            item.section = self.section

            yield item


class ChildrenContainer(MediaContainer):
    pass


class LeavesContainer(MediaContainer):
    pass


class SectionContainer(MediaContainer):
    filter_passes = lambda _, allowed, value: allowed is None or value in allowed

    def filter(self, types=None, keys=None, titles=None):
        types = to_iterable(types)
        keys = to_iterable(keys)

        titles = to_iterable(titles)

        if titles:
            # Flatten titles
            titles = [flatten(x) for x in titles]

        for section in self:
            if not self.filter_passes(types, section.type):
                continue

            if not self.filter_passes(keys, section.key):
                continue

            if not self.filter_passes(titles, flatten(section.title)):
                continue

            yield section
