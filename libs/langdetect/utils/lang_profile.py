from collections import defaultdict
import re

import six
from six.moves import xrange

from .ngram import NGram


class LangProfile(object):
    MINIMUM_FREQ = 2
    LESS_FREQ_RATIO = 100000

    ROMAN_CHAR_RE = re.compile(r'^[A-Za-z]$')
    ROMAN_SUBSTR_RE = re.compile(r'.*[A-Za-z].*')

    def __init__(self, name=None, freq=None, n_words=None):
        self.freq = defaultdict(int)
        if freq is not None:
            self.freq.update(freq)

        if n_words is None:
            n_words = [0] * NGram.N_GRAM

        self.name = name
        self.n_words = n_words

    def add(self, gram):
        '''Add n-gram to profile.'''
        if self.name is None or gram is None:  # Illegal
            return
        length = len(gram)
        if length < 1 or length > NGram.N_GRAM:  # Illegal
            return
        self.n_words[length - 1] += 1
        self.freq[gram] += 1

    def omit_less_freq(self):
        '''Eliminate below less frequency n-grams and noise Latin alphabets.'''
        if self.name is None:  # Illegal
            return
        threshold = max(self.n_words[0] // self.LESS_FREQ_RATIO, self.MINIMUM_FREQ)

        roman = 0
        for key, count in list(six.iteritems(self.freq)):
            if count <= threshold:
                self.n_words[len(key)-1] -= count
                del self.freq[key]
            elif self.ROMAN_CHAR_RE.match(key):
                roman += count

        # roman check
        if roman < self.n_words[0] // 3:
            for key, count in list(six.iteritems(self.freq)):
                if self.ROMAN_SUBSTR_RE.match(key):
                    self.n_words[len(key)-1] -= count
                    del self.freq[key]

    def update(self, text):
        '''Update the language profile with (fragmented) text.
        Extract n-grams from text and add their frequency into the profile.
        '''
        if text is None:
            return
        text = NGram.normalize_vi(text)
        gram = NGram()
        for ch in text:
            gram.add_char(ch)
            for n in xrange(1, NGram.N_GRAM+1):
                self.add(gram.get(n))
