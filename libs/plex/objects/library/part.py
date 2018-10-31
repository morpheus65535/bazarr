from plex.objects.core.base import Descriptor, Property
from plex.objects.library.stream import Stream


class Part(Descriptor):
    streams = Property(resolver=lambda: Stream.from_node)

    id = Property(type=int)
    key = Property

    file = Property
    container = Property

    duration = Property(type=int)
    size = Property(type=int)

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Part'):
            _, obj = Part.construct(client, genre, child=True)

            items.append(obj)

        return [], items
