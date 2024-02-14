# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .avistaz_network import AvistazNetworkProviderBase


class AvistazProvider(AvistazNetworkProviderBase):
    """AvistaZ.to Provider."""
    server_url = 'https://avistaz.to/'
    provider_name = 'avistaz'
