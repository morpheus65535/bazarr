from plex.objects.core.base import Descriptor, Property


class Role(Descriptor):
    id = Property(type=int)
    tag = Property

    role = Property
    thumb = Property

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Role'):
            _, obj = Role.construct(client, genre, child=True)

            items.append(obj)

        return [], items
