"""
🌏 Charamel: Truly Universal Encoding Detection in Python 🌎
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Licensed under Apache 2.0
"""
import itertools
import math
from typing import Dict, List, Optional, Sequence, Set, Tuple

from charamel.encoding import Encoding
from charamel.resources import load_biases, load_features, load_weights


def _get_features(content: bytes) -> Set[int]:
    """
    Extract unique byte uni-grams and bi-grams

    Args:
        content: Encoded text

    Returns:
        Set of integers that represent byte n-grams
    """
    pairs = zip(content, itertools.islice(content, 1, None))
    return set(content).union(x * 256 + y for x, y in pairs)


def _apply_sigmoid(value: float) -> float:
    """
    Apply sigmoid function to given value
    """
    return 1 / (1 + math.exp(-value))


class Detector:
    """
    Universal encoding detector
    """

    def __init__(
        self,
        encodings: Sequence[Encoding] = tuple(Encoding),
        min_confidence: float = 0.0,
    ):
        """
        Create universal encoding detector for given encodings

        Args:
            encodings: Encodings that will be supported by this Detector instance,
                less encodings lead to faster runtime
            min_confidence: Minimum confidence threshold for encodings

        Example:
            >>> detector = Detector(
            ...     encodings=[Encoding.UTF_8, Encoding.BIG_5],
            ...     min_confidence=0.7,
            ... )
        """
        if not encodings:
            raise ValueError('No encodings specified')

        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError('min_confidence must be in range [0, 1]')

        self._features = load_features()
        self._weights = load_weights(encodings)
        self._biases = load_biases(encodings)
        self._min_confidence = min_confidence

    def _score(self, content: bytes) -> Dict[Encoding, float]:
        """
        Compute how likely each encoding is able to decode the content

        Args:
            content: Encoded text

        Returns:
            Real-valued score for each encoding
        """
        scores = self._biases.copy()
        features = _get_features(content).intersection(self._features)
        indices = [self._features[feature] for feature in features]
        for encoding, weights in self._weights.items():
            scores[encoding] += sum(weights[index] for index in indices)
        return scores

    def detect(self, content: bytes) -> Optional[Encoding]:
        """
        Detect the most probable encoding for given byte content

        Args:
            content: Encoded text

        Returns:
            Encoding or `None` if not confident enough

        Example:
            >>> detector = Detector()
            >>> detector.detect(b'\xc4\xe3\xba\xc3')
            <Encoding.GB_K: 'gbk'>
        """
        scores = self._score(content)
        if scores:
            encoding, score = max(scores.items(), key=lambda x: x[1])
            if _apply_sigmoid(score) >= self._min_confidence:
                return encoding
        return None

    def probe(self, content: bytes, top: int = 3) -> List[Tuple[Encoding, float]]:
        """
        Detect `top` probable encodings with confidences

        Args:
            content: Encoded text
            top: How many of the most likely encodings to return

        Example:
            >>> detector = Detector()
            >>> detector.probe(b'\xc4\xe3\xba\xc3')
            [(<Encoding.GB_K: 'gbk'>, 0.6940633812304486),
             (<Encoding.GB_18030: 'gb18030'>, 0.6886364021582343),
             (<Encoding.GB_2312: 'gb2312'>, 0.6707061223726806)]
        """
        scores = sorted(self._score(content).items(), key=lambda x: x[1], reverse=True)
        confidences = [
            (encoding, _apply_sigmoid(score)) for encoding, score in scores[:top]
        ]
        return [
            (encoding, confidence)
            for encoding, confidence in confidences
            if confidence >= self._min_confidence
        ]
