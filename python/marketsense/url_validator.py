from __future__ import annotations

from typing import Dict, List, Tuple

from .config import Settings
from .robots import RobotsCache, is_domain_allowed


def validate_urls(urls: List[str], settings: Settings) -> Tuple[List[str], List[Dict[str, str]]]:
    robots_cache = RobotsCache(settings)
    allowed: List[str] = []
    rejected: List[Dict[str, str]] = []

    for url in urls:
        if not is_domain_allowed(url, settings.allow_domains, settings.deny_domains):
            rejected.append({"url": url, "reason": "domain_not_allowed"})
            continue
        if settings.robots_enabled and not robots_cache.allowed(url):
            rejected.append({"url": url, "reason": "robots_disallow"})
            continue
        allowed.append(url)

    return allowed, rejected
