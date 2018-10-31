from plex.interfaces.core.base import Interface

TIMELINE_STATES = [
    'buffering',
    'paused',
    'playing',
    'stopped'
]


class TimelineInterface(Interface):
    path = ':/timeline'

    def update(self, rating_key, state, time, duration, key=None, play_queue_item_id=None):
        if not rating_key:
            raise ValueError('Invalid "rating_key" parameter')

        if time is None or duration is None:
            raise ValueError('"time" and "duration" parameters are required')

        if state not in TIMELINE_STATES:
            raise ValueError('Unknown "state"')

        response = self.http.get(query=[
            ('ratingKey', rating_key),
            ('state', state),

            ('time', time),
            ('duration', duration),

            # Optional parameters
            ('key', key),
            ('playQueueItemID', play_queue_item_id)
        ])

        return response and response.status_code == 200
