# coding=utf-8

from __future__ import absolute_import
from __future__ import print_function
from subzero.language import Language
from .data import data
import six

#for lang, data in data.iteritems():
#    print Language.fromietf(lang).alpha2

for find, rep in six.iteritems(data["dan"]):
    print(find, rep)