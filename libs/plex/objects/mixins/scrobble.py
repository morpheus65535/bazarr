from plex import Plex
from plex.objects.core.base import DescriptorMixin


class ScrobbleMixin(DescriptorMixin):
    def scrobble(self):
        return Plex['library'].scrobble(self.rating_key)
