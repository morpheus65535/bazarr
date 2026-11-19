# `NL2BR` Extension
# ===============

# A Python-Markdown extension to treat newlines as hard breaks; like
# GitHub-flavored Markdown does.

# See https://Python-Markdown.github.io/extensions/nl2br
# for documentation.

# Original code Copyright 2011 [Brian Neal](https://deathofagremmie.com/)

# All changes Copyright 2011-2014 The Python Markdown Project

# License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""
A Python-Markdown extension to treat newlines as hard breaks.
Similar to GitHub-flavored Markdown's behavior.

See the [documentation](https://Python-Markdown.github.io/extensions/nl2br)
for details.
"""

from __future__ import annotations

from . import Extension
from ..inlinepatterns import SubstituteTagInlineProcessor

BR_RE = r'\n'


class Nl2BrExtension(Extension):
    """ Newline-to-break extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Register the processor.

        | Class Instance                                                  | Registry                                                      | Name   | Priority |
        | --------------------------------------------------------------- | ------------------------------------------------------------- | ------ | :------: |
        | [`SubstituteTagInlineProcessor`][markdown.inlinepatterns.SubstituteTagInlineProcessor] | [`inlinepatterns`][markdown.inlinepatterns.build_inlinepatterns] | `nl` | `5` |

        """
        # flake8: noqa: E501 38-40
        br_tag = SubstituteTagInlineProcessor(BR_RE, 'br')
        md.inlinePatterns.register(br_tag, 'nl', 5)


def makeExtension(**kwargs):  # pragma: no cover
    return Nl2BrExtension(**kwargs)
