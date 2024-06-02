from __future__ import absolute_import

from subliminal_patch.providers.avistaz_network import AvistazNetworkProviderBase


class CinemazProvider(AvistazNetworkProviderBase):
    """CinemaZ.to Provider."""
    server_url = 'https://cinemaz.to/'
    provider_name = 'cinemaz'
