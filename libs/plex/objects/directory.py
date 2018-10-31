from plex.objects.core.base import Descriptor, Property


class Directory(Descriptor):
    key = Property
    type = Property

    title = Property

    size = Property

    art = Property
    thumb = Property

    allow_sync = Property('allowSync', bool)
    updated_at = Property('updatedAt', int)
