from plex.core.helpers import to_iterable
from plex.objects.library.container import MediaContainer


class SessionContainer(MediaContainer):
    filter_passes = lambda _, allowed, value: allowed is None or value in allowed

    def filter(self, keys=None):
        keys = to_iterable(keys)

        for item in self:
            if not self.filter_passes(keys, item.session.key):
                continue

            yield item

    def get(self, key):
        for item in self.filter(key):
            return item

        return None
