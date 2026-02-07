from __future__ import annotations

import asyncio
import time
from typing import Dict
from urllib.parse import urlparse

from .config import Settings


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


class DomainRateLimiter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._locks: Dict[str, asyncio.Lock] = {}
        self._last_request: Dict[str, float] = {}
        self._delay: Dict[str, float] = {}

    async def wait(self, url: str) -> None:
        domain = domain_from_url(url)
        lock = self._locks.setdefault(domain, asyncio.Lock())

        async with lock:
            now = time.time()
            last = self._last_request.get(domain, 0.0)
            delay = self._delay.get(domain, self.settings.domain_delay_base)
            sleep_for = delay - (now - last)
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            self._last_request[domain] = time.time()

    def record_result(self, url: str, blocked: bool) -> None:
        domain = domain_from_url(url)
        current = self._delay.get(domain, self.settings.domain_delay_base)
        if blocked:
            new_delay = min(self.settings.domain_delay_max, current * 1.5)
        else:
            new_delay = max(self.settings.domain_delay_base, current * 0.9)
        self._delay[domain] = new_delay
