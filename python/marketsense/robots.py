from __future__ import annotations

import time
from typing import Callable, Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from .config import Settings


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_domain_allowed(url: str, allow_domains: list, deny_domains: list) -> bool:
    domain = domain_from_url(url)
    if deny_domains and domain in deny_domains:
        return False
    if allow_domains and domain not in allow_domains:
        return False
    return True


class RobotsCache:
    def __init__(
        self,
        settings: Settings,
        fetcher: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.settings = settings
        self._cache: Dict[str, tuple] = {}
        self._fetcher = fetcher or self._default_fetcher

    def allowed(self, url: str) -> bool:
        if not self.settings.robots_enabled:
            return True

        domain = domain_from_url(url)
        robots = self._get_parser(domain)
        if robots is None:
            return self.settings.robots_fail_open

        return robots.can_fetch(self.settings.robots_user_agent, url)

    def _get_parser(self, domain: str) -> Optional[RobotFileParser]:
        now = time.time()
        cached = self._cache.get(domain)
        if cached:
            parser, expires_at = cached
            if expires_at > now:
                return parser

        try:
            content = self._fetcher(domain)
        except Exception:
            return None

        parser = RobotFileParser()
        parser.parse(content.splitlines())
        self._cache[domain] = (parser, now + self.settings.robots_cache_ttl)
        return parser

    @staticmethod
    def _default_fetcher(domain: str) -> str:
        url = f"https://{domain}/robots.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
