#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebulk object default builder
"""
from rebulk import Rebulk

from .markers.path import path
from .markers.groups import groups

from .properties.episodes import episodes
from .properties.container import container
from .properties.source import source
from .properties.video_codec import video_codec
from .properties.audio_codec import audio_codec
from .properties.screen_size import screen_size
from .properties.website import website
from .properties.date import date
from .properties.title import title
from .properties.episode_title import episode_title
from .properties.language import language
from .properties.country import country
from .properties.release_group import release_group
from .properties.streaming_service import streaming_service
from .properties.other import other
from .properties.size import size
from .properties.bit_rate import bit_rate
from .properties.edition import edition
from .properties.cds import cds
from .properties.bonus import bonus
from .properties.film import film
from .properties.part import part
from .properties.crc import crc
from .properties.mimetype import mimetype
from .properties.type import type_

from .processors import processors


def rebulk_builder(config):
    """
    Default builder for main Rebulk object used by api.
    :return: Main Rebulk object
    :rtype: Rebulk
    """
    def _config(name):
        return config.get(name, {})

    rebulk = Rebulk()

    common_words = frozenset(_config('common_words'))

    rebulk.rebulk(path(_config('path')))
    rebulk.rebulk(groups(_config('groups')))

    rebulk.rebulk(episodes(_config('episodes')))
    rebulk.rebulk(container(_config('container')))
    rebulk.rebulk(source(_config('source')))
    rebulk.rebulk(video_codec(_config('video_codec')))
    rebulk.rebulk(audio_codec(_config('audio_codec')))
    rebulk.rebulk(screen_size(_config('screen_size')))
    rebulk.rebulk(website(_config('website')))
    rebulk.rebulk(date(_config('date')))
    rebulk.rebulk(title(_config('title')))
    rebulk.rebulk(episode_title(_config('episode_title')))
    rebulk.rebulk(language(_config('language'), common_words))
    rebulk.rebulk(country(_config('country'), common_words))
    rebulk.rebulk(release_group(_config('release_group')))
    rebulk.rebulk(streaming_service(_config('streaming_service')))
    rebulk.rebulk(other(_config('other')))
    rebulk.rebulk(size(_config('size')))
    rebulk.rebulk(bit_rate(_config('bit_rate')))
    rebulk.rebulk(edition(_config('edition')))
    rebulk.rebulk(cds(_config('cds')))
    rebulk.rebulk(bonus(_config('bonus')))
    rebulk.rebulk(film(_config('film')))
    rebulk.rebulk(part(_config('part')))
    rebulk.rebulk(crc(_config('crc')))

    rebulk.rebulk(processors(_config('processors')))

    rebulk.rebulk(mimetype(_config('mimetype')))
    rebulk.rebulk(type_(_config('type')))

    def customize_properties(properties):
        """
        Customize default rebulk properties
        """
        count = properties['count']
        del properties['count']

        properties['season_count'] = count
        properties['episode_count'] = count

        return properties

    rebulk.customize_properties = customize_properties

    return rebulk
