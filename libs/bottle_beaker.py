#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bottle
import inspect
import beaker
from beaker import middleware


class BeakerPlugin(object):
    name = 'beaker'

    def __init__(self, keyword='beaker'):
        """
        :param keyword: Keyword used to inject beaker in a route
        """
        self.keyword = keyword

    def setup(self, app):
        """ Make sure that other installed plugins don't affect the same
            keyword argument and check if metadata is available."""
        for other in app.plugins:
            if not isinstance(other, BeakerPlugin):
                continue
            if other.keyword == self.keyword:
                raise bottle.PluginError("Found another beaker plugin "
                                         "with conflicting settings ("
                                         "non-unique keyword).")

    def apply(self, callback, context):
        args = inspect.getargspec(context['callback'])[0]

        if self.keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = beaker
            kwargs["{0}_middleware".format(self.keyword)] = middleware
            return callback(*args, **kwargs)

        return wrapper
