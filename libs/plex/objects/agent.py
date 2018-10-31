from plex.objects.core.base import Descriptor, Property


class MediaType(Descriptor):
    name = Property
    media_type = Property("mediaType", type=int)

    @classmethod
    def from_node(cls, client, node):
        items = []

        for t in cls.helpers.findall(node, 'MediaType'):
            _, obj = MediaType.construct(client, t, child=True)

            items.append(obj)

        return [], items


class Agent(Descriptor):
    name = Property
    enabled = Property(type=int)
    identifier = Property
    primary = Property(type=int)
    has_prefs = Property("hasPrefs", type=int)
    has_attribution = Property("hasAttribution", type=int)

    media_types = Property(resolver=lambda: MediaType.from_node)

