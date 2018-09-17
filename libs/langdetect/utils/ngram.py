import re

import six

from . import messages
from .unicode_block import (
    unicode_block,
    UNICODE_BASIC_LATIN,
    UNICODE_LATIN_1_SUPPLEMENT,
    UNICODE_LATIN_EXTENDED_B,
    UNICODE_GENERAL_PUNCTUATION,
    UNICODE_ARABIC,
    UNICODE_LATIN_EXTENDED_ADDITIONAL,
    UNICODE_HIRAGANA,
    UNICODE_KATAKANA,
    UNICODE_BOPOMOFO,
    UNICODE_BOPOMOFO_EXTENDED,
    UNICODE_CJK_UNIFIED_IDEOGRAPHS,
    UNICODE_HANGUL_SYLLABLES,
)


class NGram(object):
    LATIN1_EXCLUDED = messages.get_string('NGram.LATIN1_EXCLUDE')
    N_GRAM = 3

    def __init__(self):
        self.grams = ' '
        self.capitalword = False

    def add_char(self, ch):
        '''Append a character into ngram buffer.'''
        ch = self.normalize(ch)
        last_char = self.grams[-1]
        if last_char == ' ':
            self.grams = ' '
            self.capitalword = False
            if ch == ' ':
                return
        elif len(self.grams) >= self.N_GRAM:
            self.grams = self.grams[1:]
        self.grams += ch

        if ch.isupper():
            if last_char.isupper():
                self.capitalword = True
        else:
            self.capitalword = False

    def get(self, n):
        '''Get n-gram.'''
        if self.capitalword:
            return
        if n < 1 or n > self.N_GRAM or len(self.grams) < n:
            return
        if n == 1:
            ch = self.grams[-1]
            if ch == ' ':
                return
            return ch
        else:
            return self.grams[-n:]

    @classmethod
    def normalize(cls, ch):
        block = unicode_block(ch)
        if block == UNICODE_BASIC_LATIN:
            if ch < 'A' or ('Z' < ch < 'a') or 'z' < ch:
                ch = ' '
        elif block == UNICODE_LATIN_1_SUPPLEMENT:
            if cls.LATIN1_EXCLUDED.find(ch) >= 0:
                ch = ' '
        elif block == UNICODE_LATIN_EXTENDED_B:
            # normalization for Romanian
            if ch == six.u('\u0219'):  # Small S with comma below => with cedilla
                ch = six.u('\u015f')
            if ch == six.u('\u021b'):  # Small T with comma below => with cedilla
                ch = six.u('\u0163')
        elif block == UNICODE_GENERAL_PUNCTUATION:
            ch = ' '
        elif block == UNICODE_ARABIC:
            if ch == six.u('\u06cc'):
                ch = six.u('\u064a')  # Farsi yeh => Arabic yeh
        elif block == UNICODE_LATIN_EXTENDED_ADDITIONAL:
            if ch >= six.u('\u1ea0'):
                ch = six.u('\u1ec3')
        elif block == UNICODE_HIRAGANA:
            ch = six.u('\u3042')
        elif block == UNICODE_KATAKANA:
            ch = six.u('\u30a2')
        elif block in (UNICODE_BOPOMOFO, UNICODE_BOPOMOFO_EXTENDED):
            ch = six.u('\u3105')
        elif block == UNICODE_CJK_UNIFIED_IDEOGRAPHS:
            ch = cls.CJK_MAP.get(ch, ch)
        elif block == UNICODE_HANGUL_SYLLABLES:
            ch = six.u('\uac00')
        return ch

    @classmethod
    def normalize_vi(cls, text):
        '''Normalizer for Vietnamese.
        Normalize Alphabet + Diacritical Mark(U+03xx) into U+1Exx.
        '''
        def repl(m):
            alphabet = cls.TO_NORMALIZE_VI_CHARS.find(m.group(1))
            dmark = cls.DMARK_CLASS.find(m.group(2))  # Diacritical Mark
            return cls.NORMALIZED_VI_CHARS[dmark][alphabet]
        return cls.ALPHABET_WITH_DMARK.sub(repl, text)

    NORMALIZED_VI_CHARS = [
        messages.get_string('NORMALIZED_VI_CHARS_0300'),
        messages.get_string('NORMALIZED_VI_CHARS_0301'),
        messages.get_string('NORMALIZED_VI_CHARS_0303'),
        messages.get_string('NORMALIZED_VI_CHARS_0309'),
        messages.get_string('NORMALIZED_VI_CHARS_0323')]
    TO_NORMALIZE_VI_CHARS = messages.get_string('TO_NORMALIZE_VI_CHARS')
    DMARK_CLASS = messages.get_string('DMARK_CLASS')
    ALPHABET_WITH_DMARK = re.compile(
        '([' + TO_NORMALIZE_VI_CHARS + '])([' + DMARK_CLASS + '])',
        re.UNICODE)

    # CJK Kanji Normalization Mapping
    CJK_CLASS = [
        messages.get_string('NGram.KANJI_1_0'),
        messages.get_string('NGram.KANJI_1_2'),
        messages.get_string('NGram.KANJI_1_4'),
        messages.get_string('NGram.KANJI_1_8'),
        messages.get_string('NGram.KANJI_1_11'),
        messages.get_string('NGram.KANJI_1_12'),
        messages.get_string('NGram.KANJI_1_13'),
        messages.get_string('NGram.KANJI_1_14'),
        messages.get_string('NGram.KANJI_1_16'),
        messages.get_string('NGram.KANJI_1_18'),
        messages.get_string('NGram.KANJI_1_22'),
        messages.get_string('NGram.KANJI_1_27'),
        messages.get_string('NGram.KANJI_1_29'),
        messages.get_string('NGram.KANJI_1_31'),
        messages.get_string('NGram.KANJI_1_35'),
        messages.get_string('NGram.KANJI_2_0'),
        messages.get_string('NGram.KANJI_2_1'),
        messages.get_string('NGram.KANJI_2_4'),
        messages.get_string('NGram.KANJI_2_9'),
        messages.get_string('NGram.KANJI_2_10'),
        messages.get_string('NGram.KANJI_2_11'),
        messages.get_string('NGram.KANJI_2_12'),
        messages.get_string('NGram.KANJI_2_13'),
        messages.get_string('NGram.KANJI_2_15'),
        messages.get_string('NGram.KANJI_2_16'),
        messages.get_string('NGram.KANJI_2_18'),
        messages.get_string('NGram.KANJI_2_21'),
        messages.get_string('NGram.KANJI_2_22'),
        messages.get_string('NGram.KANJI_2_23'),
        messages.get_string('NGram.KANJI_2_28'),
        messages.get_string('NGram.KANJI_2_29'),
        messages.get_string('NGram.KANJI_2_30'),
        messages.get_string('NGram.KANJI_2_31'),
        messages.get_string('NGram.KANJI_2_32'),
        messages.get_string('NGram.KANJI_2_35'),
        messages.get_string('NGram.KANJI_2_36'),
        messages.get_string('NGram.KANJI_2_37'),
        messages.get_string('NGram.KANJI_2_38'),
        messages.get_string('NGram.KANJI_3_1'),
        messages.get_string('NGram.KANJI_3_2'),
        messages.get_string('NGram.KANJI_3_3'),
        messages.get_string('NGram.KANJI_3_4'),
        messages.get_string('NGram.KANJI_3_5'),
        messages.get_string('NGram.KANJI_3_8'),
        messages.get_string('NGram.KANJI_3_9'),
        messages.get_string('NGram.KANJI_3_11'),
        messages.get_string('NGram.KANJI_3_12'),
        messages.get_string('NGram.KANJI_3_13'),
        messages.get_string('NGram.KANJI_3_15'),
        messages.get_string('NGram.KANJI_3_16'),
        messages.get_string('NGram.KANJI_3_18'),
        messages.get_string('NGram.KANJI_3_19'),
        messages.get_string('NGram.KANJI_3_22'),
        messages.get_string('NGram.KANJI_3_23'),
        messages.get_string('NGram.KANJI_3_27'),
        messages.get_string('NGram.KANJI_3_29'),
        messages.get_string('NGram.KANJI_3_30'),
        messages.get_string('NGram.KANJI_3_31'),
        messages.get_string('NGram.KANJI_3_32'),
        messages.get_string('NGram.KANJI_3_35'),
        messages.get_string('NGram.KANJI_3_36'),
        messages.get_string('NGram.KANJI_3_37'),
        messages.get_string('NGram.KANJI_3_38'),
        messages.get_string('NGram.KANJI_4_0'),
        messages.get_string('NGram.KANJI_4_9'),
        messages.get_string('NGram.KANJI_4_10'),
        messages.get_string('NGram.KANJI_4_16'),
        messages.get_string('NGram.KANJI_4_17'),
        messages.get_string('NGram.KANJI_4_18'),
        messages.get_string('NGram.KANJI_4_22'),
        messages.get_string('NGram.KANJI_4_24'),
        messages.get_string('NGram.KANJI_4_28'),
        messages.get_string('NGram.KANJI_4_34'),
        messages.get_string('NGram.KANJI_4_39'),
        messages.get_string('NGram.KANJI_5_10'),
        messages.get_string('NGram.KANJI_5_11'),
        messages.get_string('NGram.KANJI_5_12'),
        messages.get_string('NGram.KANJI_5_13'),
        messages.get_string('NGram.KANJI_5_14'),
        messages.get_string('NGram.KANJI_5_18'),
        messages.get_string('NGram.KANJI_5_26'),
        messages.get_string('NGram.KANJI_5_29'),
        messages.get_string('NGram.KANJI_5_34'),
        messages.get_string('NGram.KANJI_5_39'),
        messages.get_string('NGram.KANJI_6_0'),
        messages.get_string('NGram.KANJI_6_3'),
        messages.get_string('NGram.KANJI_6_9'),
        messages.get_string('NGram.KANJI_6_10'),
        messages.get_string('NGram.KANJI_6_11'),
        messages.get_string('NGram.KANJI_6_12'),
        messages.get_string('NGram.KANJI_6_16'),
        messages.get_string('NGram.KANJI_6_18'),
        messages.get_string('NGram.KANJI_6_20'),
        messages.get_string('NGram.KANJI_6_21'),
        messages.get_string('NGram.KANJI_6_22'),
        messages.get_string('NGram.KANJI_6_23'),
        messages.get_string('NGram.KANJI_6_25'),
        messages.get_string('NGram.KANJI_6_28'),
        messages.get_string('NGram.KANJI_6_29'),
        messages.get_string('NGram.KANJI_6_30'),
        messages.get_string('NGram.KANJI_6_32'),
        messages.get_string('NGram.KANJI_6_34'),
        messages.get_string('NGram.KANJI_6_35'),
        messages.get_string('NGram.KANJI_6_37'),
        messages.get_string('NGram.KANJI_6_39'),
        messages.get_string('NGram.KANJI_7_0'),
        messages.get_string('NGram.KANJI_7_3'),
        messages.get_string('NGram.KANJI_7_6'),
        messages.get_string('NGram.KANJI_7_7'),
        messages.get_string('NGram.KANJI_7_9'),
        messages.get_string('NGram.KANJI_7_11'),
        messages.get_string('NGram.KANJI_7_12'),
        messages.get_string('NGram.KANJI_7_13'),
        messages.get_string('NGram.KANJI_7_16'),
        messages.get_string('NGram.KANJI_7_18'),
        messages.get_string('NGram.KANJI_7_19'),
        messages.get_string('NGram.KANJI_7_20'),
        messages.get_string('NGram.KANJI_7_21'),
        messages.get_string('NGram.KANJI_7_23'),
        messages.get_string('NGram.KANJI_7_25'),
        messages.get_string('NGram.KANJI_7_28'),
        messages.get_string('NGram.KANJI_7_29'),
        messages.get_string('NGram.KANJI_7_32'),
        messages.get_string('NGram.KANJI_7_33'),
        messages.get_string('NGram.KANJI_7_35'),
        messages.get_string('NGram.KANJI_7_37')]

    CJK_MAP = {}

    @classmethod
    def _init_cjk_map(cls):
        for cjk_list in cls.CJK_CLASS:
            representative = cjk_list[0]
            for ch in cjk_list:
                cls.CJK_MAP[ch] = representative

NGram._init_cjk_map()
