from plex.objects.core.base import Descriptor, Property


class Genre(Descriptor):
    id = Property(type=int)
    tag = Property

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Genre'):
            _, obj = Genre.construct(client, genre, child=True)

            items.append(obj)

        return [], items
