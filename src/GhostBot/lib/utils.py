import asyncio
import inspect
import threading
import time
from collections.abc import Callable
from functools import partial
from typing import Coroutine, Protocol, TypeVar, ParamSpec


class TRetryCoroutine(Protocol):
    def __call__(self, *, retry_count) -> Coroutine[None, None, bool]: ...
class TRetry(Protocol):
    def __call__(self, *, retry_count) -> bool: ...
RetryCoroutine = Callable[[], bool] | TRetryCoroutine | Callable[[], Coroutine[None, None, bool]]
RetryFunc = TRetry | Callable[[], bool]

def retry(func: RetryFunc, retries: int = 1, delay: float = 1) -> bool:
    for i in range(0, retries):
        try:
            if 'retry_count' in inspect.signature(func).parameters:
                func = partial(func, retry_count=i+1)
        except ValueError:
            pass
        result = func()
        if result:
            return result
        time.sleep(delay)
    return False


async def asyncretry(func: RetryCoroutine, retries: int = 1, delay: float = 1) -> bool:
    for i in range(0, retries):
        try:
            if 'retry_count' in inspect.signature(func).parameters:
                func = partial(func, retry_count=i+1)
        except ValueError:
            pass
        result = func()
        if asyncio.iscoroutine(result):
            result = await result
        if result:
            return result
        await asyncio.sleep(delay)
    return False


def recursive_subclasses(_clazz):
    if not inspect.isabstract(_clazz):
        yield _clazz
    for _sub in _clazz.__subclasses__():
        yield from recursive_subclasses(_sub)


def subclasses_by_name(_clazz):
    return {a.__name__: a for a in recursive_subclasses(_clazz)}

_P = ParamSpec("_P")
_R = TypeVar("_R")


def with_timeout(_func: Callable[_P, _R], timeout: float = 1) -> _R:

    _return: list[_R] = []
    thread = threading.Thread(target=lambda: _return.append(_func()), name=f'{_func.__name__}:with_timeout')
    thread.start()
    thread.join(timeout=timeout)
    if not _return:
        raise TimeoutError('%s timed out', _func.__name__)
    return _return.pop()

if __name__ == "__main__":

    async def async_thing():
        gen = (a for a in (None, False, True))

        async def foo(retry_count):
            return next(gen)

        if await asyncretry(foo, retries=3, delay=1):
            print('yes')
        print(1)
        gen = (a for a in (False, False, True))
        if retry(partial(next, gen), retries=3, delay=1):
            print('yes')
        print(2)
        gen = (a for a in (False, False, False))
        if await asyncretry(partial(next, gen), retries=3, delay=1):
            print('yes')
        print(3)
    asyncio.run(async_thing())
