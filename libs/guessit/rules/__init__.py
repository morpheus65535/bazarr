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
from .properties.format import format_
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
from .properties.edition import edition
from .properties.cds import cds
from .properties.bonus import bonus
from .properties.film import film
from .properties.part import part
from .properties.crc import crc
from .properties.mimetype import mimetype
from .properties.type import type_

from .processors import processors


def rebulk_builder():
    """
    Default builder for main Rebulk object used by api.
    :return: Main Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()

    rebulk.rebulk(path())
    rebulk.rebulk(groups())

    rebulk.rebulk(episodes())
    rebulk.rebulk(container())
    rebulk.rebulk(format_())
    rebulk.rebulk(video_codec())
    rebulk.rebulk(audio_codec())
    rebulk.rebulk(screen_size())
    rebulk.rebulk(website())
    rebulk.rebulk(date())
    rebulk.rebulk(title())
    rebulk.rebulk(episode_title())
    rebulk.rebulk(language())
    rebulk.rebulk(country())
    rebulk.rebulk(release_group())
    rebulk.rebulk(streaming_service())
    rebulk.rebulk(other())
    rebulk.rebulk(size())
    rebulk.rebulk(edition())
    rebulk.rebulk(cds())
    rebulk.rebulk(bonus())
    rebulk.rebulk(film())
    rebulk.rebulk(part())
    rebulk.rebulk(crc())

    rebulk.rebulk(processors())

    rebulk.rebulk(mimetype())
    rebulk.rebulk(type_())

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
