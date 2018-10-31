from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class StatusInterface(Interface):
    path = 'status'

    def sessions(self):
        response = self.http.get('sessions')

        return self.parse(response, idict({
            'MediaContainer': ('SessionContainer', idict({
                'Track': 'Track',

                'Video': {
                    'episode':  'Episode',
                    'clip':     'Clip',
                    'movie':    'Movie'
                }
            }))
        }))
