from plex.objects.core.base import Descriptor, Property


class User(Descriptor):
    id = Property(type=int)

    title = Property
    thumb = Property
