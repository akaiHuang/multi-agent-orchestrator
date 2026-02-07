from __future__ import annotations

import asyncio
import gzip
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async as _stealth_async
except Exception:  # pragma: no cover - support different playwright-stealth versions
    try:
        from playwright_stealth.stealth import Stealth

        async def _stealth_async(page):  # type: ignore
            await Stealth().apply_stealth_async(page)

    except Exception:
        _stealth_async = None
from firebase_admin import firestore

from .config import Settings
from .firebase_client import get_db_and_bucket
from .human_behavior import (
    HumanBehaviorSimulator,
    get_browser_context_options,
    get_random_user_agent,
    simulate_mouse_movement,
    simulate_reading_pause,
    simulate_scroll,
)
from .stealth_browser import (
    get_browser_launch_options,
    get_enhanced_stealth_script,
)
from .rate_limit import DomainRateLimiter
from .robots import RobotsCache, is_domain_allowed
from .utils import detect_block_signals, normalize_url, url_hash


@dataclass
class CrawlTarget:
    url: str
    ref: Optional[object] = None
    brand: str = ""
    product: str = ""
    objective: str = ""


async def fetch_and_store(
    semaphore: asyncio.Semaphore,
    context,
    target: CrawlTarget,
    settings: Settings,
    db,
    bucket,
    robots_cache: RobotsCache,
    rate_limiter: DomainRateLimiter,
) -> Dict[str, Optional[object]]:
    async with semaphore:
        normalized = normalize_url(target.url)
        hash_id = url_hash(normalized)

        if not is_domain_allowed(target.url, settings.allow_domains, settings.deny_domains):
            payload = {
                "url": target.url,
                "normalized_url": normalized,
                "url_hash": hash_id,
                "status": "skipped",
                "skip_reason": "domain_not_allowed",
                "skipped_at": firestore.SERVER_TIMESTAMP,
                "locked_at": None,
                "locked_until": None,
            }
            if target.ref is not None:
                target.ref.update(payload)
            else:
                db.collection("crawling_tasks").add(payload)
            return {"success": False, "blocked_suspected": False, "response_status": None, "error": "domain_not_allowed"}

        if not robots_cache.allowed(target.url):
            payload = {
                "url": target.url,
                "normalized_url": normalized,
                "url_hash": hash_id,
                "status": "skipped",
                "skip_reason": "robots_disallow",
                "skipped_at": firestore.SERVER_TIMESTAMP,
                "locked_at": None,
                "locked_until": None,
            }
            if target.ref is not None:
                target.ref.update(payload)
            else:
                db.collection("crawling_tasks").add(payload)
            return {"success": False, "blocked_suspected": False, "response_status": None, "error": "robots_disallow"}

        last_error = ""
        for attempt in range(1, settings.retries + 1):
            page = await context.new_page()
            if _stealth_async:
                await _stealth_async(page)

            # 初始化人類行為模擬器
            human_sim = HumanBehaviorSimulator(page, settings)
            await human_sim.warm_up()

            response_status: Optional[int] = None
            try:
                await rate_limiter.wait(target.url)
                await asyncio.sleep(random.uniform(settings.min_delay, settings.max_delay))

                # 模擬人類導航前的行為
                await simulate_mouse_movement(page, duration=0.5)

                start_time = time.time()
                response = await page.goto(target.url, wait_until="domcontentloaded", timeout=settings.page_timeout_ms)
                if response is not None:
                    response_status = response.status

                # 模擬人類瀏覽行為
                await simulate_reading_pause(0.5, 1.5)
                await simulate_scroll(page, scroll_count=random.randint(1, 3))
                await simulate_mouse_movement(page, duration=0.8)

                # 等待完整載入
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(random.uniform(settings.min_delay / 2, settings.max_delay / 2))

                content = await page.content()
                title = await page.title()
                latency_ms = int((time.time() - start_time) * 1000)

                compressed = gzip.compress(content.encode("utf-8"))
                filename = f"{settings.raw_html_prefix}{int(time.time())}_{random.randint(1000,9999)}.html.gz"

                local_path = ""
                if settings.local_raw_dir:
                    os.makedirs(settings.local_raw_dir, exist_ok=True)
                    local_name = f"{hash_id}_{int(time.time())}.html.gz"
                    local_path = os.path.join(settings.local_raw_dir, local_name)
                    with open(local_path, "wb") as handle:
                        handle.write(compressed)

                if not settings.local_store_only:
                    blob = bucket.blob(filename)
                    blob.content_encoding = "gzip"
                    blob.content_type = "text/html"
                    blob.upload_from_string(compressed)

                block_signals = detect_block_signals(content, response_status)

                payload = {
                    "url": target.url,
                    "normalized_url": normalized,
                    "url_hash": hash_id,
                    "title": title,
                    "storage_path": filename if not settings.local_store_only else "",
                    "local_path": local_path,
                    "status": "downloaded",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "downloaded_at": firestore.SERVER_TIMESTAMP,
                    "response_status": response_status,
                    "block_signals": block_signals,
                    "blocked_suspected": len(block_signals) > 0,
                    "fetch_attempts": attempt,
                    "last_error": "",
                    "locked_at": None,
                    "locked_until": None,
                    "fetch_latency_ms": latency_ms,
                }
                if target.brand:
                    payload["brand"] = target.brand
                if target.product:
                    payload["product"] = target.product
                if target.objective:
                    payload["objective"] = target.objective

                if target.ref is not None:
                    target.ref.update(payload)
                else:
                    db.collection("crawling_tasks").add(payload)
                await page.close()
                rate_limiter.record_result(target.url, blocked=len(block_signals) > 0)
                return {
                    "success": True,
                    "blocked_suspected": len(block_signals) > 0,
                    "response_status": response_status,
                    "error": None,
                }
            except Exception as exc:
                last_error = str(exc)
                await page.close()
                rate_limiter.record_result(target.url, blocked=True)
                backoff = min(
                    settings.retry_backoff_max,
                    settings.retry_backoff_base * (2 ** (attempt - 1)),
                )
                sleep_time = backoff + random.uniform(0, 1)
                sleep_time = max(settings.cooldown_min, min(settings.cooldown_max, sleep_time))
                await asyncio.sleep(sleep_time)

        error_payload = {
            "url": target.url,
            "normalized_url": normalized,
            "url_hash": hash_id,
            "status": "error",
            "error_log": last_error,
            "last_error": last_error,
            "created_at": firestore.SERVER_TIMESTAMP,
            "failed_at": firestore.SERVER_TIMESTAMP,
            "locked_at": None,
            "locked_until": None,
        }
        if target.brand:
            error_payload["brand"] = target.brand
        if target.product:
            error_payload["product"] = target.product
        if target.objective:
            error_payload["objective"] = target.objective
        if target.ref is not None:
            target.ref.update(error_payload)
        else:
            db.collection("crawling_tasks").add(error_payload)
        return {
            "success": False,
            "blocked_suspected": False,
            "response_status": None,
            "error": last_error,
        }


async def run_crawl(targets: Iterable[CrawlTarget], settings: Settings) -> List[Dict[str, Optional[object]]]:
    db, bucket = get_db_and_bucket(settings)

    if settings.local_store_only and not settings.local_raw_dir:
        raise ValueError("LOCAL_RAW_DIR is required when LOCAL_STORE_ONLY=true")
    if not settings.firebase_storage_bucket and not settings.local_raw_dir:
        raise ValueError("FIREBASE_STORAGE_BUCKET or LOCAL_RAW_DIR is required")

    semaphore = asyncio.Semaphore(settings.max_concurrent)
    robots_cache = RobotsCache(settings)
    rate_limiter = DomainRateLimiter(settings)

    async with async_playwright() as p:
        # 1️⃣ 使用 Headed 模式 + 2️⃣ 真實 GPU 啟動參數
        launch_options = get_browser_launch_options(headless=settings.headless)
        browser = await p.chromium.launch(**launch_options)
        
        # 使用更真實的瀏覽器設定
        context_options = get_browser_context_options()
        # 允許使用者自訂 user_agent 覆蓋
        if settings.user_agent and settings.user_agent != "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36":
            context_options["user_agent"] = settings.user_agent
        context = await browser.new_context(**context_options)
        
        # 注入增強版反偵測腳本（WebGL 偽裝等）
        await context.add_init_script(get_enhanced_stealth_script())

        tasks = [
            fetch_and_store(semaphore, context, target, settings, db, bucket, robots_cache, rate_limiter)
            for target in targets
        ]
        results = await asyncio.gather(*tasks)

        await browser.close()
        return results
