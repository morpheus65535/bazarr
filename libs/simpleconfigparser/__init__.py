# -*- coding: utf-8 -*-
"""
The MIT License

Copyright (c) 2013 Helgi Þorbjörnsson <helgi@php.net>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# Bazarr patch to use custom ConfigParser2:
from ConfigParser2 import ConfigParser as configparser, NoOptionError, NoSectionError
#try:
#    from configparser2 import ConfigParser as configparser, NoOptionError, NoSectionError
#except ImportError:
#    from ConfigParser import SafeConfigParser as configparser, NoOptionError, NoSectionError


class simpleconfigparser(configparser):
    class Section(dict):
        """
        Contain the section specific items that can be accessed via object properties
        """
        parser = None
        section = None

        def __init__(self, section, parser):
            self.section = section
            self.parser = parser

        def __getitem__(self, name, raw=False, vars=None):
            """Fetch a value via the dict handler"""
            if name not in simpleconfigparser.Section.__dict__:
                return self.parser.get(self.section, name, raw, vars)

        def __setitem__(self, name, value):
            """Set a value via the dict handler"""
            if name in simpleconfigparser.Section.__dict__:
                return dict.__setitem__(self, name, value)

            return self.parser.set(self.section, name, value)

        def __getattr__(self, name, raw=False, vars=None):
            """Fetch a value via the object handler"""
            if name not in simpleconfigparser.Section.__dict__:
                return self.parser.get(self.section, name, raw, vars)

        def __setattr__(self, name, value):
            """Set a value via the object handler"""
            if name in simpleconfigparser.Section.__dict__:
                return object.__setattr__(self, name, value)

            return self.parser.set(self.section, name, value)

        def getboolean(self, name):
            if not self.section:
                return None

            return self.parser.getboolean(self.section, name)

        def items(self):
            if not self.section:
                return None

            items = []
            for key, value in self.parser.items(self.section):
                # strip quotes
                items.append((key, value.strip('"\'')))

            return items

    def __init__(self, defaults=None, *args, **kwargs):
        configparser.__init__(self, defaults=None, *args, **kwargs)
        # Improved defaults handling
        if isinstance(defaults, dict):
            for section, values in defaults.items():
                # Break out original format defaults was passed in
                if not isinstance(values, dict):
                    break

                if section not in self.sections():
                    self.add_section(section)

                for name, value in values.items():
                    self.set(section, name, str(value))

    def __getitem__(self, name):
        """Access a section via a dict handler"""
        if name not in simpleconfigparser.__dict__:
            if name not in self.sections():
                self.add_section(name)

            return simpleconfigparser.Section(name, self)

        return None

    def __getattr__(self, name, raw=False, vars=None):
        """Access a section via a object handler"""
        if name not in simpleconfigparser.__dict__:
            if name not in self.sections():
                self.add_section(name)

            return simpleconfigparser.Section(name, self)

        return None

    def set(self, section, option, value=None):
        try:
            return configparser.set(self, section, option, value)
        except NoSectionError:
            return None

    def get(self, section, option, raw=False, vars=None):
        try:
            # Strip out quotes from the edges
            return configparser.get(self, section, option, raw=raw, vars=vars).strip('"\'')
        except NoOptionError:
            return None
