#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import logging
import sys

from sklearn.pipeline import Pipeline

from .subtitle_parser import GenericSubtitleParser
from .subtitle_transformers import SubtitleShifter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    td = float(sys.argv[3])
    pipe = Pipeline([
        ('parse', GenericSubtitleParser()),
        ('offset', SubtitleShifter(td)),
    ])
    pipe.fit_transform(sys.argv[1])
    pipe.steps[-1][1].write_file(sys.argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
