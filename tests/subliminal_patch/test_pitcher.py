import pytest

import subliminal_patch.pitcher as pitcher_module
from subliminal_patch.pitcher import Pitcher, SolveCooldown


class _FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class _StubPitcher(Pitcher):
    def __init__(self, name: str, results: list) -> None:
        self.name = name
        self.website_name = "test-site"
        self.solve_time = None
        self._results = list(results)
        self.calls = 0

    def _throw(self):
        self.calls += 1
        return self._results.pop(0) if self._results else None


@pytest.fixture
def clock(monkeypatch):
    fake = _FakeClock()
    monkeypatch.setattr(pitcher_module, "_solve_cooldowns", {})
    monkeypatch.setattr(pitcher_module, "SolveCooldown",
                        lambda cooldown_seconds: SolveCooldown(cooldown_seconds, clock=fake))
    return fake


def test_cooldown_after_failure():
    clock = _FakeClock()
    cooldown = SolveCooldown(cooldown_seconds=100, clock=clock)
    assert cooldown.is_available() is True
    cooldown.report_failure()
    assert cooldown.is_available() is False
    clock.now += 100
    assert cooldown.is_available() is True
    cooldown.report_failure()
    cooldown.report_success()
    assert cooldown.is_available() is True


def test_failed_solve_blocks_later_solves_of_same_pitcher(clock):
    first = _StubPitcher("StubA", [None])
    assert first.throw() is None
    assert first.calls == 1

    # A new instance of the same pitcher shares the cooldown.
    second = _StubPitcher("StubA", ["answer"])
    assert second.throw() is None
    assert second.calls == 0


def test_cooldown_is_per_pitcher_name(clock):
    failing = _StubPitcher("StubA", [None])
    failing.throw()

    other = _StubPitcher("StubB", ["answer"])
    assert other.throw() == "answer"
    assert other.calls == 1


def test_successful_solve_is_returned_and_cooldown_expires(clock):
    stub = _StubPitcher("StubC", [None, "answer"])
    stub.throw()
    assert stub.calls == 1
    clock.now += pitcher_module.PITCHER_COOLDOWN_SECONDS
    assert stub.throw() == "answer"
    assert stub.calls == 2


def test_exception_in_solver_starts_cooldown_and_propagates(clock):
    class _Raising(_StubPitcher):
        def _throw(self):
            self.calls += 1
            raise RuntimeError("service down")

    stub = _Raising("StubD", [])
    with pytest.raises(RuntimeError):
        stub.throw()
    assert _StubPitcher("StubD", ["x"]).throw() is None
