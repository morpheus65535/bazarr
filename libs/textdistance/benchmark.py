from __future__ import annotations

# built-in
import json
import math
from collections import defaultdict
from timeit import timeit
from typing import Iterable, Iterator, NamedTuple

# external
from tabulate import tabulate

# app
from .libraries import LIBRARIES_PATH, prototype


# python3 -m textdistance.benchmark


libraries = prototype.clone()


class Lib(NamedTuple):
    algorithm: str
    library: str
    function: str
    time: float
    setup: str

    @property
    def row(self) -> tuple[str, ...]:
        time = '' if math.isinf(self.time) else f'{self.time:0.05f}'
        return (self.algorithm, self.library.split('.')[0], time)


INTERNAL_SETUP = """
from textdistance import {} as cls
func = cls(external=False)
"""

STMT = """
func('text', 'test')
func('qwer', 'asdf')
func('a' * 15, 'b' * 15)
"""

RUNS = 4000


class Benchmark:
    @staticmethod
    def get_installed() -> Iterator[Lib]:
        for alg in libraries.get_algorithms():
            for lib in libraries.get_libs(alg):
                # try load function
                if not lib.get_function():
                    print(f'WARNING: cannot get func for {lib}')
                    continue
                # return library info
                yield Lib(
                    algorithm=alg,
                    library=lib.module_name,
                    function=lib.func_name,
                    time=float('Inf'),
                    setup=lib.setup,
                )

    @staticmethod
    def get_external_benchmark(installed: Iterable[Lib]) -> Iterator[Lib]:
        for lib in installed:
            time = timeit(
                stmt=STMT,
                setup=lib.setup,
                number=RUNS,
            )
            yield lib._replace(time=time)

    @staticmethod
    def get_internal_benchmark() -> Iterator[Lib]:
        for alg in libraries.get_algorithms():
            setup = f'func = __import__("textdistance").{alg}(external=False)'
            yield Lib(
                algorithm=alg,
                library='**textdistance**',
                function=alg,
                time=timeit(
                    stmt=STMT,
                    setup=setup,
                    number=RUNS,
                ),
                setup=setup,
            )

    @staticmethod
    def filter_benchmark(
        external: Iterable[Lib],
        internal: Iterable[Lib],
    ) -> Iterator[Lib]:
        limits = {i.algorithm: i.time for i in internal}
        return filter(lambda x: x.time < limits[x.algorithm], external)

    @staticmethod
    def get_table(libs: list[Lib]) -> str:
        table = tabulate(
            [lib.row for lib in libs],
            headers=['algorithm', 'library', 'time'],
            tablefmt='github',
        )
        table += f'\nTotal: {len(libs)} libs.\n\n'
        return table

    @staticmethod
    def save(libs: Iterable[Lib]) -> None:
        data = defaultdict(list)
        for lib in libs:
            data[lib.algorithm].append([lib.library, lib.function])
        with LIBRARIES_PATH.open('w', encoding='utf8') as f:
            json.dump(obj=data, fp=f, indent=2, sort_keys=True)

    @classmethod
    def run(cls) -> None:
        print('# Installed libraries:\n')
        installed = list(cls.get_installed())
        installed.sort()
        print(cls.get_table(installed))

        print('# Benchmarks (with textdistance):\n')
        benchmark = list(cls.get_external_benchmark(installed))
        benchmark_internal = list(cls.get_internal_benchmark())
        benchmark += benchmark_internal
        benchmark.sort(key=lambda x: (x.algorithm, x.time))
        print(cls.get_table(benchmark))

        benchmark = list(cls.filter_benchmark(benchmark, benchmark_internal))
        cls.save(benchmark)


if __name__ == '__main__':
    Benchmark.run()
