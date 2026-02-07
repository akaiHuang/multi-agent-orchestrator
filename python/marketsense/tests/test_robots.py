from marketsense.config import Settings
from marketsense.robots import RobotsCache, is_domain_allowed


def test_domain_allow_deny(monkeypatch):
    monkeypatch.setenv("ALLOW_DOMAINS", "example.com,foo.com")
    monkeypatch.setenv("DENY_DOMAINS", "deny.com")
    settings = Settings.from_env()

    assert is_domain_allowed("https://example.com/path", settings.allow_domains, settings.deny_domains)
    assert not is_domain_allowed("https://deny.com/path", settings.allow_domains, settings.deny_domains)
    assert not is_domain_allowed("https://bar.com/path", settings.allow_domains, settings.deny_domains)


def test_robots_cache_allowed(monkeypatch):
    monkeypatch.setenv("ROBOTS_ENABLED", "true")
    monkeypatch.setenv("ROBOTS_USER_AGENT", "MarketSenseBot")
    settings = Settings.from_env()

    def fetcher(_domain):
        return "User-agent: *\nDisallow: /private\nAllow: /\n"

    cache = RobotsCache(settings, fetcher=fetcher)
    assert cache.allowed("https://example.com/public")
    assert not cache.allowed("https://example.com/private")
