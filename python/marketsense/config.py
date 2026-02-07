from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "y"}:
        return True
    if value in {"0", "false", "no", "n"}:
        return False
    return default


def _env_list(key: str) -> list:
    value = os.getenv(key, "")
    if not value:
        return []
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def load_env(env_file: Optional[str]) -> None:
    if env_file:
        load_dotenv(env_file, override=False)


@dataclass
class Settings:
    firebase_service_account: str
    firebase_storage_bucket: str
    max_concurrent: int
    min_delay: float
    max_delay: float
    cooldown_min: float
    cooldown_max: float
    retries: int
    retry_backoff_base: float
    retry_backoff_max: float
    headless: bool
    user_agent: str
    page_timeout_ms: int
    raw_html_prefix: str
    local_raw_dir: str
    local_store_only: bool
    max_text_chars: int
    llm_provider: str
    allow_domains: list
    deny_domains: list
    robots_enabled: bool
    robots_user_agent: str
    robots_cache_ttl: int
    robots_fail_open: bool
    domain_delay_base: float
    domain_delay_max: float
    running_stale_seconds: int
    requeue_analyzed_after_hours: int
    requeue_downloaded_after_hours: int
    requeue_error_after_hours: int
    ollama_api_key: Optional[str]
    ollama_api_key_header: str
    ollama_base_url: str
    ollama_model: str
    ollama_api_mode: str
    llm_timeout: int

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Settings":
        load_env(env_file)

        firebase_service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
        firebase_storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")

        ollama_api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("ollama_api_key")

        return cls(
            firebase_service_account=firebase_service_account,
            firebase_storage_bucket=firebase_storage_bucket,
            max_concurrent=_env_int("MAX_CONCURRENT", 3),
            min_delay=_env_float("MIN_DELAY", 2.0),
            max_delay=_env_float("MAX_DELAY", 5.0),
            cooldown_min=_env_float("COOLDOWN_MIN", 5.0),
            cooldown_max=_env_float("COOLDOWN_MAX", 10.0),
            retries=_env_int("RETRIES", 3),
            retry_backoff_base=_env_float("RETRY_BACKOFF_BASE", 1.5),
            retry_backoff_max=_env_float("RETRY_BACKOFF_MAX", 30.0),
            headless=_env_bool("HEADLESS", True),
            user_agent=os.getenv("USER_AGENT", DEFAULT_USER_AGENT),
            page_timeout_ms=_env_int("PAGE_TIMEOUT_MS", 30000),
            raw_html_prefix=os.getenv("RAW_HTML_PREFIX", "raw_html/"),
            local_raw_dir=os.getenv("LOCAL_RAW_DIR", ""),
            local_store_only=_env_bool("LOCAL_STORE_ONLY", False),
            max_text_chars=_env_int("MAX_TEXT_CHARS", 12000),
            llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
            ollama_api_key=ollama_api_key,
            ollama_api_key_header=os.getenv("OLLAMA_API_KEY_HEADER", "Authorization"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            ollama_api_mode=os.getenv("OLLAMA_API_MODE", "openai"),
            llm_timeout=_env_int("LLM_TIMEOUT", 60),
            allow_domains=_env_list("ALLOW_DOMAINS"),
            deny_domains=_env_list("DENY_DOMAINS"),
            robots_enabled=_env_bool("ROBOTS_ENABLED", True),
            robots_user_agent=os.getenv("ROBOTS_USER_AGENT", "MarketSenseBot"),
            robots_cache_ttl=_env_int("ROBOTS_CACHE_TTL", 3600),
            robots_fail_open=_env_bool("ROBOTS_FAIL_OPEN", True),
            domain_delay_base=_env_float("DOMAIN_DELAY_BASE", 1.0),
            domain_delay_max=_env_float("DOMAIN_DELAY_MAX", 15.0),
            running_stale_seconds=_env_int("RUNNING_STALE_SECONDS", 900),
            requeue_analyzed_after_hours=_env_int("REQUEUE_ANALYZED_AFTER_HOURS", 0),
            requeue_downloaded_after_hours=_env_int("REQUEUE_DOWNLOADED_AFTER_HOURS", 0),
            requeue_error_after_hours=_env_int("REQUEUE_ERROR_AFTER_HOURS", 24),
        )

    def with_overrides(
        self,
        max_concurrent: Optional[int] = None,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        retries: Optional[int] = None,
        headless: Optional[bool] = None,
        user_agent: Optional[str] = None,
    ) -> "Settings":
        return Settings(
            firebase_service_account=self.firebase_service_account,
            firebase_storage_bucket=self.firebase_storage_bucket,
            max_concurrent=max_concurrent if max_concurrent is not None else self.max_concurrent,
            min_delay=min_delay if min_delay is not None else self.min_delay,
            max_delay=max_delay if max_delay is not None else self.max_delay,
            cooldown_min=self.cooldown_min,
            cooldown_max=self.cooldown_max,
            retries=retries if retries is not None else self.retries,
            retry_backoff_base=self.retry_backoff_base,
            retry_backoff_max=self.retry_backoff_max,
            headless=headless if headless is not None else self.headless,
            user_agent=user_agent if user_agent is not None else self.user_agent,
            page_timeout_ms=self.page_timeout_ms,
            raw_html_prefix=self.raw_html_prefix,
            local_raw_dir=self.local_raw_dir,
            local_store_only=self.local_store_only,
            max_text_chars=self.max_text_chars,
            llm_provider=self.llm_provider,
            ollama_api_key=self.ollama_api_key,
            ollama_api_key_header=self.ollama_api_key_header,
            ollama_base_url=self.ollama_base_url,
            ollama_model=self.ollama_model,
            ollama_api_mode=self.ollama_api_mode,
            llm_timeout=self.llm_timeout,
            allow_domains=self.allow_domains,
            deny_domains=self.deny_domains,
            robots_enabled=self.robots_enabled,
            robots_user_agent=self.robots_user_agent,
            robots_cache_ttl=self.robots_cache_ttl,
            robots_fail_open=self.robots_fail_open,
            domain_delay_base=self.domain_delay_base,
            domain_delay_max=self.domain_delay_max,
            running_stale_seconds=self.running_stale_seconds,
            requeue_analyzed_after_hours=self.requeue_analyzed_after_hours,
            requeue_downloaded_after_hours=self.requeue_downloaded_after_hours,
            requeue_error_after_hours=self.requeue_error_after_hours,
        )
