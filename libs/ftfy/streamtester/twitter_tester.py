"""
Implements a StreamTester that runs over Twitter data. See the class
docstring.

This module is written for Python 3 only. The __future__ imports you see here
are just to let Python 2 scan the file without crashing with a SyntaxError.
"""
from __future__ import print_function, unicode_literals
import os
from collections import defaultdict
from ftfy.streamtester import StreamTester


class TwitterTester(StreamTester):
    """
    This class uses the StreamTester code (defined in `__init__.py`) to
    evaluate ftfy's real-world performance, by feeding it live data from
    Twitter.

    This is a semi-manual evaluation. It requires a human to look at the
    results and determine if they are good. The three possible cases we
    can see here are:

        - Success: the process takes in mojibake and outputs correct text.
        - False positive: the process takes in correct text, and outputs
          mojibake. Every false positive should be considered a bug, and
          reported on GitHub if it isn't already.
        - Confusion: the process takes in mojibake and outputs different
          mojibake. Not a great outcome, but not as dire as a false
          positive.

    This tester cannot reveal false negatives. So far, that can only be
    done by the unit tests.
    """
    OUTPUT_DIR = './twitterlogs'

    def __init__(self):
        self.lines_by_lang = defaultdict(list)
        super().__init__()

    def save_files(self):
        """
        When processing data from live Twitter, save it to log files so that
        it can be replayed later.
        """
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
        for lang, lines in self.lines_by_lang.items():
            filename = 'tweets.{}.txt'.format(lang)
            fullname = os.path.join(self.OUTPUT_DIR, filename)
            langfile = open(fullname, 'a', encoding='utf-8')
            for line in lines:
                print(line.replace('\n', ' '), file=langfile)
            langfile.close()
        self.lines_by_lang = defaultdict(list)

    def run_sample(self):
        """
        Listen to live data from Twitter, and pass on the fully-formed tweets
        to `check_ftfy`. This requires the `twitter` Python package as a
        dependency.
        """
        from twitter import TwitterStream
        from ftfy.streamtester.oauth import get_auth
        twitter_stream = TwitterStream(auth=get_auth())
        iterator = twitter_stream.statuses.sample()
        for tweet in iterator:
            if 'text' in tweet:
                self.check_ftfy(tweet['text'])
                if 'user' in tweet:
                    lang = tweet['user'].get('lang', 'NONE')
                    self.lines_by_lang[lang].append(tweet['text'])
                if self.count % 10000 == 100:
                    self.save_files()


def main():
    """
    When run from the command line, this script connects to the Twitter stream
    and runs the TwitterTester on it forever. Or at least until the stream
    drops.
    """
    tester = TwitterTester()
    tester.run_sample()


if __name__ == '__main__':
    main()
