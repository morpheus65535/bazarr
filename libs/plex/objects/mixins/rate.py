from plex import Plex
from plex.objects.core.base import Property, DescriptorMixin


class RateMixin(DescriptorMixin):
    rating = Property(type=float)
    user_rating = Property('userRating', type=float)

    def rate(self, value):
        return Plex['library'].rate(self.rating_key, value)
