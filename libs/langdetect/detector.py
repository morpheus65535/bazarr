import random
import re

import six
from six.moves import zip, xrange

from .lang_detect_exception import ErrorCode, LangDetectException
from .language import Language
from .utils.ngram import NGram
from .utils.unicode_block import unicode_block


class Detector(object):
    '''
    Detector class is to detect language from specified text.
    Its instance is able to be constructed via the factory class DetectorFactory.

    After appending a target text to the Detector instance with .append(string),
    the detector provides the language detection results for target text via .detect() or .get_probabilities().

    .detect() method returns a single language name which has the highest probability.
    .get_probabilities() methods returns a list of multiple languages and their probabilities.

    The detector has some parameters for language detection.
    See set_alpha(double), .set_max_text_length(int) .set_prior_map(dict).

    Example:

        from langdetect.detector_factory import DetectorFactory
        factory = DetectorFactory()
        factory.load_profile('/path/to/profile/directory')

        def detect(text):
            detector = factory.create()
            detector.append(text)
            return detector.detect()

        def detect_langs(text):
            detector = factory.create()
            detector.append(text)
            return detector.get_probabilities()
    '''

    ALPHA_DEFAULT = 0.5
    ALPHA_WIDTH = 0.05

    ITERATION_LIMIT = 1000
    PROB_THRESHOLD = 0.1
    CONV_THRESHOLD = 0.99999
    BASE_FREQ = 10000
    UNKNOWN_LANG = 'unknown'

    URL_RE = re.compile(r'https?://[-_.?&~;+=/#0-9A-Za-z]{1,2076}')
    MAIL_RE = re.compile(r'[-_.0-9A-Za-z]{1,64}@[-_0-9A-Za-z]{1,255}[-_.0-9A-Za-z]{1,255}')

    def __init__(self, factory):
        self.word_lang_prob_map = factory.word_lang_prob_map
        self.langlist = factory.langlist
        self.seed = factory.seed
        self.random = random.Random()
        self.text = ''
        self.langprob = None

        self.alpha = self.ALPHA_DEFAULT
        self.n_trial = 7
        self.max_text_length = 10000
        self.prior_map = None
        self.verbose = False

    def set_verbose(self):
        self.verbose = True

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_prior_map(self, prior_map):
        '''Set prior information about language probabilities.'''
        self.prior_map = [0.0] * len(self.langlist)
        sump = 0.0
        for i in xrange(len(self.prior_map)):
            lang = self.langlist[i]
            if lang in prior_map:
                p = prior_map[lang]
                if p < 0:
                    raise LangDetectException(ErrorCode.InitParamError, 'Prior probability must be non-negative.')
                self.prior_map[i] = p
                sump += p
        if sump <= 0.0:
            raise LangDetectException(ErrorCode.InitParamError, 'More one of prior probability must be non-zero.')
        for i in xrange(len(self.prior_map)):
            self.prior_map[i] /= sump

    def set_max_text_length(self, max_text_length):
        '''Specify max size of target text to use for language detection.
        The default value is 10000(10KB).
        '''
        self.max_text_length = max_text_length

    def append(self, text):
        '''Append the target text for language detection.
        If the total size of target text exceeds the limit size specified by
        Detector.set_max_text_length(int), the rest is cut down.
        '''
        text = self.URL_RE.sub(' ', text)
        text = self.MAIL_RE.sub(' ', text)
        text = NGram.normalize_vi(text)
        pre = 0
        for i in xrange(min(len(text), self.max_text_length)):
            ch = text[i]
            if ch != ' ' or pre != ' ':
                self.text += ch
            pre = ch

    def cleaning_text(self):
        '''Cleaning text to detect
        (eliminate URL, e-mail address and Latin sentence if it is not written in Latin alphabet).
        '''
        latin_count, non_latin_count = 0, 0
        for ch in self.text:
            if 'A' <= ch <= 'z':
                latin_count += 1
            elif ch >= six.u('\u0300') and unicode_block(ch) != 'Latin Extended Additional':
                non_latin_count += 1

        if latin_count * 2 < non_latin_count:
            text_without_latin = ''
            for ch in self.text:
                if ch < 'A' or 'z' < ch:
                    text_without_latin += ch
            self.text = text_without_latin

    def detect(self):
        '''Detect language of the target text and return the language name
        which has the highest probability.
        '''
        probabilities = self.get_probabilities()
        if probabilities:
            return probabilities[0].lang
        return self.UNKNOWN_LANG

    def get_probabilities(self):
        if self.langprob is None:
            self._detect_block()
        return self._sort_probability(self.langprob)

    def _detect_block(self):
        self.cleaning_text()
        ngrams = self._extract_ngrams()
        if not ngrams:
            raise LangDetectException(ErrorCode.CantDetectError, 'No features in text.')

        self.langprob = [0.0] * len(self.langlist)

        self.random.seed(self.seed)
        for t in xrange(self.n_trial):
            prob = self._init_probability()
            alpha = self.alpha + self.random.gauss(0.0, 1.0) * self.ALPHA_WIDTH

            i = 0
            while True:
                self._update_lang_prob(prob, self.random.choice(ngrams), alpha)
                if i % 5 == 0:
                    if self._normalize_prob(prob) > self.CONV_THRESHOLD or i >= self.ITERATION_LIMIT:
                        break
                    if self.verbose:
                        six.print_('>', self._sort_probability(prob))
                i += 1
            for j in xrange(len(self.langprob)):
                self.langprob[j] += prob[j] / self.n_trial
            if self.verbose:
                six.print_('==>', self._sort_probability(prob))

    def _init_probability(self):
        '''Initialize the map of language probabilities.
        If there is the specified prior map, use it as initial map.
        '''
        if self.prior_map is not None:
            return list(self.prior_map)
        else:
            return [1.0 / len(self.langlist)] * len(self.langlist)

    def _extract_ngrams(self):
        '''Extract n-grams from target text.'''
        RANGE = list(xrange(1, NGram.N_GRAM + 1))

        result = []
        ngram = NGram()
        for ch in self.text:
            ngram.add_char(ch)
            if ngram.capitalword:
                continue
            for n in RANGE:
                # optimized w = ngram.get(n)
                if len(ngram.grams) < n:
                    break
                w = ngram.grams[-n:]
                if w and w != ' ' and w in self.word_lang_prob_map:
                    result.append(w)
        return result

    def _update_lang_prob(self, prob, word, alpha):
        '''Update language probabilities with N-gram string(N=1,2,3).'''
        if word is None or word not in self.word_lang_prob_map:
            return False

        lang_prob_map = self.word_lang_prob_map[word]
        if self.verbose:
            six.print_('%s(%s): %s' % (word, self._unicode_encode(word), self._word_prob_to_string(lang_prob_map)))

        weight = alpha / self.BASE_FREQ
        for i in xrange(len(prob)):
            prob[i] *= weight + lang_prob_map[i]
        return True

    def _word_prob_to_string(self, prob):
        result = ''
        for j in xrange(len(prob)):
            p = prob[j]
            if p >= 0.00001:
                result += ' %s:%.5f' % (self.langlist[j], p)
        return result

    def _normalize_prob(self, prob):
        '''Normalize probabilities and check convergence by the maximun probability.
        '''
        maxp, sump = 0.0, sum(prob)
        for i in xrange(len(prob)):
            p = prob[i] / sump
            if maxp < p:
                maxp = p
            prob[i] = p
        return maxp

    def _sort_probability(self, prob):
        result = [Language(lang, p) for (lang, p) in zip(self.langlist, prob) if p > self.PROB_THRESHOLD]
        result.sort(reverse=True)
        return result

    def _unicode_encode(self, word):
        buf = ''
        for ch in word:
            if ch >= six.u('\u0080'):
                st = hex(0x10000 + ord(ch))[2:]
                while len(st) < 4:
                    st = '0' + st
                buf += r'\u' + st[1:5]
            else:
                buf += ch
        return buf
