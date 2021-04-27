import asyncio
import sys
import types


def run(coro):
    if sys.version_info >= (3, 7):
        return asyncio.run(coro)

    # Emulate asyncio.run() on older versions

    # asyncio.run() requires a coroutine, so require it here as well
    if not isinstance(coro, types.CoroutineType):
        raise TypeError("run() requires a coroutine object")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def strip_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string
