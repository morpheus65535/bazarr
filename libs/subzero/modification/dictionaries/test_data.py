# coding=utf-8

from subzero.language import Language
from data import data

#for lang, data in data.iteritems():
#    print Language.fromietf(lang).alpha2

for find, rep in data["dan"].iteritems():
    print find, rep