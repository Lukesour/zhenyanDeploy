import asyncio
import types
import pytest

from backend.services.retry import async_retry_full_jitter


class Flaky:
    def __init__(self, fail_times: int):
        self.remaining = fail_times

    def __call__(self):
        if self.remaining > 0:
            self.remaining -= 1
            raise RuntimeError("flaky")
        return "ok"


@pytest.mark.asyncio
async def test_retry_eventually_succeeds_without_real_sleep():
    calls = {"sleep": []}

    async def fake_sleep(d: float):
        calls["sleep"].append(d)

    def fake_rng():
        return 0.5  # deterministic

    func = Flaky(2)
    result = await async_retry_full_jitter(
        func,
        exceptions=(RuntimeError,),
        max_attempts=3,
        base=2,
        max_backoff=10,
        sleep=fake_sleep,
        rng=fake_rng,
    )
    assert result == "ok"
    # Should have slept twice (after first and second failures)
    assert len(calls["sleep"]) == 2
    # delays: attempt1 -> base^1 * 0.5 = 1.0, attempt2 -> base^2 * 0.5 = 2.0
    assert calls["sleep"][0] == pytest.approx(1.0, rel=1e-6)
    assert calls["sleep"][1] == pytest.approx(2.0, rel=1e-6)


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_attempts():
    async def fake_sleep(_):
        return None

    def fake_rng():
        return 0.5

    func = Flaky(5)
    with pytest.raises(RuntimeError):
        await async_retry_full_jitter(
            func,
            exceptions=(RuntimeError,),
            max_attempts=3,
            base=2,
            max_backoff=10,
            sleep=fake_sleep,
            rng=fake_rng,
        )


@pytest.mark.asyncio
async def test_non_retryable_exception_is_raised_immediately():
    async def fake_sleep(_):
        return None

    def bad():
        raise ValueError("bad")

    with pytest.raises(ValueError):
        await async_retry_full_jitter(
            bad,
            exceptions=(RuntimeError,),
            max_attempts=3,
            sleep=fake_sleep,
        )

















