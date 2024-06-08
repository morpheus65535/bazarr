from __future__ import annotations

# built-in
import json
from collections import defaultdict
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Sequence


LIBRARIES_PATH = Path(__file__).parent / 'libraries.json'


class LibrariesManager:
    libs: defaultdict[str, list[LibraryBase]]

    def __init__(self) -> None:
        self.libs = defaultdict(list)

    def register(self, alg: str, lib: LibraryBase) -> None:
        """Register new lib
        """
        self.libs[alg].append(lib)

    def optimize(self) -> None:
        """Sort algorithm implementations by speed.
        """
        # load benchmarks results
        with LIBRARIES_PATH.open('r', encoding='utf8') as f:
            libs_data: dict = json.load(f)
        # optimize
        for alg, libs_names in libs_data.items():
            libs = self.get_libs(alg)
            if not libs:
                continue
            # drop slow libs
            self.libs[alg] = [lib for lib in libs if [lib.module_name, lib.func_name] in libs_names]
            # sort libs by speed
            self.libs[alg].sort(key=lambda lib: libs_names.index([lib.module_name, lib.func_name]))

    def get_algorithms(self) -> list[str]:
        """Get list of available algorithms.
        """
        return list(self.libs.keys())

    def get_libs(self, alg: str) -> list[LibraryBase]:
        """Get libs list for algorithm
        """
        if alg not in self.libs:
            return []
        return self.libs[alg]

    def clone(self) -> LibrariesManager:
        """Clone library manager prototype
        """
        obj = self.__class__()
        obj.libs = deepcopy(self.libs)
        return obj


class LibraryBase:
    func: Callable | None | Any = NotImplemented

    def __init__(
        self,
        module_name: str,
        func_name: str,
        *,
        presets: dict[str, Any] | None = None,
        attr: str | None = None,
        conditions: dict[str, bool] | None = None,
    ) -> None:
        self.module_name = module_name
        self.func_name = func_name
        self.presets = presets
        self.conditions = conditions
        self.attr = attr

    def check_conditions(self, obj: object, *sequences: Sequence) -> bool:
        # external libs can compare only 2 strings
        if len(sequences) != 2:
            return False
        if not self.conditions:
            return True
        for name, value in self.conditions.items():
            if getattr(obj, name) != value:
                return False

        return True

    def prepare(self, *sequences: Sequence) -> tuple:
        return sequences

    @property
    def setup(self) -> str:
        result = f'from {self.module_name} import {self.func_name} as func'
        result += '\nfunc = func'
        if self.presets is not None:
            result += f'(**{repr(self.presets)})'
        if self.attr is not None:
            result += f'.{self.attr}'
        return result

    def get_function(self) -> Callable | None:
        if self.func is NotImplemented:
            # import module
            try:
                module = import_module(self.module_name)
            except ImportError:
                self.func = None
                return None

            # get object from module
            obj = getattr(module, self.func_name)
            # init class
            if self.presets is not None:
                obj = obj(**self.presets)
            # get needed attribute
            if self.attr is not None:
                obj = getattr(obj, self.attr)
            self.func = obj

        return self.func

    def __str__(self) -> str:
        return f'{self.module_name}.{self.func_name}'


class TextLibrary(LibraryBase):
    def check_conditions(self, obj: object, *sequences: Sequence) -> bool:
        if not super().check_conditions(obj, *sequences):
            return False

        # compare only by letters
        if getattr(obj, 'qval', 0) != 1:
            return False

        # every sequence must be string
        for seq in sequences:
            if type(seq) is not str:
                return False
        return True

    def prepare(self, *sequences: Sequence) -> tuple:
        # convert list of letters to string
        if isinstance(sequences[0], (tuple, list)):
            sequences = tuple(map(lambda x: ''.join(x), sequences))
        return sequences


class SameLengthLibrary(LibraryBase):
    def check_conditions(self, obj: object, *sequences: Sequence) -> bool:
        if not super().check_conditions(obj, *sequences):
            return False
        # compare only same length iterators
        if min(map(len, sequences)) != max(map(len, sequences)):
            return False
        return True


class SameLengthTextLibrary(SameLengthLibrary, TextLibrary):
    pass


prototype = LibrariesManager()
reg = prototype.register

alg = 'DamerauLevenshtein'
reg(alg, LibraryBase('pyxdameraulevenshtein', 'damerau_levenshtein_distance', conditions=dict(restricted=True)))
reg(alg, TextLibrary('jellyfish', 'damerau_levenshtein_distance', conditions=dict(restricted=False)))
reg(alg, LibraryBase('rapidfuzz.distance.DamerauLevenshtein', 'distance', conditions=dict(restricted=False)))
reg(alg, LibraryBase('rapidfuzz.distance.OSA', 'distance', conditions=dict(restricted=True)))

alg = 'Hamming'
reg(alg, SameLengthLibrary('distance', 'hamming'))
reg(alg, SameLengthTextLibrary('Levenshtein', 'hamming'))
reg(alg, TextLibrary('jellyfish', 'hamming_distance'))
reg(alg, SameLengthLibrary('rapidfuzz.distance.Hamming', 'distance'))

alg = 'Jaro'
reg(alg, TextLibrary('jellyfish', 'jaro_similarity'))
reg(alg, LibraryBase('rapidfuzz.distance.Jaro', 'similarity'))
# reg(alg, TextLibrary('Levenshtein', 'jaro'))
# reg(alg, TextLibrary('py_stringmatching.similarity_measure.jaro', 'jaro'))

alg = 'JaroWinkler'
# reg(alg, LibraryBase('py_stringmatching.similarity_measure.jaro_winkler', 'jaro_winkler'))
reg(alg, TextLibrary('jellyfish', 'jaro_winkler_similarity', conditions=dict(winklerize=True)))
reg(alg, LibraryBase('rapidfuzz.distance.JaroWinkler', 'similarity', conditions=dict(winklerize=True)))
# https://github.com/life4/textdistance/issues/39
# reg(alg, TextLibrary('Levenshtein', 'jaro_winkler', conditions=dict(winklerize=True)))

alg = 'Levenshtein'
reg(alg, LibraryBase('distance', 'levenshtein'))
reg(alg, LibraryBase('pylev', 'levenshtein'))
reg(alg, TextLibrary('jellyfish', 'levenshtein_distance'))
reg(alg, TextLibrary('Levenshtein', 'distance'))
reg(alg, LibraryBase('rapidfuzz.distance.Levenshtein', 'distance'))
# reg(alg, TextLibrary('py_stringmatching.similarity_measure.levenshtein', 'levenshtein'))
