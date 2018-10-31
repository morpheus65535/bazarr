from plex.objects.core.base import Property
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.video import Video


class Clip(Video, Metadata):
    extra_type = Property('extraType', type=int)

    index = Property(type=int)
