"""Keep a service available across transport loss, without a session deadline."""
import asyncio


class Reconnect(Exception):
    """A transport session ended; retain local resources and try a new session."""


async def serve(session, log, *, pause=asyncio.sleep):
    delay = 1
    while True:
        started = asyncio.get_running_loop().time()
        try:
            await session()
        except Reconnect:
            if asyncio.get_running_loop().time() - started >= 30:
                delay = 1
            log(f'Tunnel offline; reconnecting in {delay}s. The application remains available.')
            await pause(delay)
            delay = min(delay * 2, 30)
        else:
            return
