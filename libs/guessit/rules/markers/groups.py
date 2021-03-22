#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Groups markers (...), [...] and {...}
"""
from rebulk import Rebulk

from ...options import ConfigurationException

def groups(config):
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()
    rebulk.defaults(name="group", marker=True)

    starting = config['starting']
    ending = config['ending']

    if len(starting) != len(ending):
        raise ConfigurationException("Starting and ending groups must have the same length")

    def mark_groups(input_string):
        """
        Functional pattern to mark groups (...), [...] and {...}.

        :param input_string:
        :return:
        """
        openings = ([], ) * len(starting)
        i = 0

        ret = []
        for char in input_string:
            start_type = starting.find(char)
            if start_type > -1:
                openings[start_type].append(i)

            i += 1

            end_type = ending.find(char)
            if end_type > -1:
                try:
                    start_index = openings[end_type].pop()
                    ret.append((start_index, i))
                except IndexError:
                    pass
        return ret

    rebulk.functional(mark_groups)
    return rebulk
