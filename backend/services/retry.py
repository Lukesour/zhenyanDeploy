import asyncio
import inspect
import random
from typing import Any, Awaitable, Callable, Iterable, Tuple
from anyio import to_thread


async def async_retry_full_jitter(
    func: Callable[..., Any],
    *args: Any,
    exceptions: Tuple[type[BaseException], ...],
    max_attempts: int = 3,
    base: float = 2.0,
    max_backoff: float = 5.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    rng: Callable[[], float] = random.random,
    **kwargs: Any,
) -> Any:
    """
    Retry wrapper with Full Jitter for async contexts.

    Full Jitter: delay_k = U(0, min(max_backoff, base**k))

    - Retries only on provided `exceptions` types
    - Supports both sync and async callables; sync ones are executed via thread pool
    - Does not sleep on the final failed attempt
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 0
    while True:
        try:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            # run sync in thread to avoid blocking event loop
            return await to_thread.run_sync(lambda: func(*args, **kwargs))
        except exceptions as exc:  # type: ignore[misc]
            attempt += 1
            if attempt >= max_attempts:
                raise
            backoff = min(max_backoff, base ** attempt)
            delay = rng() * backoff
            # ensure non-negative delay even if rng misbehaves
            delay = 0.0 if delay < 0 else delay
            await sleep(delay)
        except Exception:
            # non-retryable exception: propagate immediately
            raise

















