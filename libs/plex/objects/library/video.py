from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.extra.director import Director
from plex.objects.library.extra.writer import Writer
from plex.objects.library.media import Media
from plex.objects.mixins.session import SessionMixin


class Video(Directory, SessionMixin):
    director = Property(resolver=lambda: Director.from_node)
    media = Property(resolver=lambda: Media.from_node)
    writers = Property(resolver=lambda: Writer.from_node)

    view_count = Property('viewCount', type=int)
    view_offset = Property('viewOffset', type=int)

    chapter_source = Property('chapterSource')
    duration = Property(type=int)

    @property
    def seen(self):
        return self.view_count and self.view_count >= 1
