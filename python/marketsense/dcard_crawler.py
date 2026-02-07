"""
Dcard Authenticated Crawler
使用已儲存的認證狀態進行 Dcard 爬取
避免登入檢測和反爬蟲阻擋
"""
from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, BrowserContext, Page

from .human_behavior import (
    HumanBehaviorSimulator,
    get_browser_context_options,
    simulate_mouse_movement,
    simulate_reading_pause,
    simulate_scroll,
)


class DcardCrawler:
    """
    Dcard 專用爬蟲
    使用已認證的 session 狀態
    """

    AUTH_STATE_PATH = Path(__file__).parent.parent.parent / "dcard-auth.json"

    def __init__(
        self,
        headless: bool = True,
        auth_state_path: Optional[str] = None,
    ):
        self.headless = headless
        self.auth_state_path = Path(auth_state_path) if auth_state_path else self.AUTH_STATE_PATH
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> None:
        """啟動瀏覽器並載入認證狀態"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)

        # 準備 context 設定
        context_options = get_browser_context_options()

        # 載入已儲存的認證狀態
        if self.auth_state_path.exists():
            context_options["storage_state"] = str(self.auth_state_path)
            print(f"✅ 已載入認證狀態: {self.auth_state_path}")
        else:
            print(f"⚠️ 找不到認證狀態檔案: {self.auth_state_path}")
            print("   請先執行登入並儲存狀態")

        self._context = await self._browser.new_context(**context_options)

    async def close(self) -> None:
        """關閉瀏覽器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def save_auth_state(self, path: Optional[str] = None) -> None:
        """儲存當前認證狀態"""
        save_path = Path(path) if path else self.auth_state_path
        if self._context:
            state = await self._context.storage_state()
            save_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            print(f"✅ 已儲存認證狀態: {save_path}")

    async def fetch_forum_posts(
        self,
        forum: str = "talk",
        count: int = 20,
        sort: str = "popular",
    ) -> List[dict]:
        """
        抓取看板文章列表

        Args:
            forum: 看板名稱 (talk, mood, relationship, etc.)
            count: 要抓取的文章數量
            sort: 排序方式 (popular, new)

        Returns:
            文章列表
        """
        if not self._context:
            raise RuntimeError("Crawler not started. Call start() first.")

        page = await self._context.new_page()
        human_sim = HumanBehaviorSimulator(page)
        await human_sim.warm_up()

        posts = []
        try:
            url = f"https://www.dcard.tw/f/{forum}"
            if sort == "new":
                url += "?tab=latest"

            # 模擬人類導航
            await simulate_mouse_movement(page, 0.5)
            await page.goto(url, wait_until="domcontentloaded")
            await simulate_reading_pause(1.0, 2.0)

            # 捲動載入更多文章
            loaded_count = 0
            scroll_attempts = 0
            max_scrolls = count // 5 + 3

            while loaded_count < count and scroll_attempts < max_scrolls:
                await simulate_scroll(page, 2)
                await simulate_reading_pause(0.8, 1.5)

                # 透過 API 獲取文章資料
                articles = await page.query_selector_all('article')
                loaded_count = len(articles)
                scroll_attempts += 1

            # 提取文章資訊
            articles = await page.query_selector_all('article')
            for i, article in enumerate(articles[:count]):
                try:
                    # 取得標題
                    title_el = await article.query_selector('h2')
                    title = await title_el.inner_text() if title_el else ""

                    # 取得連結
                    link_el = await article.query_selector('a[href*="/p/"]')
                    link = await link_el.get_attribute('href') if link_el else ""

                    # 取得看板
                    board_el = await article.query_selector('a[href^="/f/"]')
                    board = await board_el.inner_text() if board_el else forum

                    # 取得摘要
                    summary_el = await article.query_selector('p')
                    summary = await summary_el.inner_text() if summary_el else ""

                    posts.append({
                        "index": i + 1,
                        "title": title.strip(),
                        "link": f"https://www.dcard.tw{link}" if link and not link.startswith('http') else link,
                        "board": board.strip(),
                        "summary": summary.strip()[:200],
                    })
                except Exception as e:
                    print(f"  ⚠️ 文章 {i+1} 解析失敗: {e}")

            print(f"✅ 成功抓取 {len(posts)} 篇文章")

        except Exception as e:
            print(f"❌ 抓取失敗: {e}")
        finally:
            await page.close()

        return posts

    async def fetch_post_content(self, post_url: str) -> dict:
        """
        抓取單篇文章內容

        Args:
            post_url: 文章網址

        Returns:
            文章詳細內容
        """
        if not self._context:
            raise RuntimeError("Crawler not started. Call start() first.")

        page = await self._context.new_page()
        human_sim = HumanBehaviorSimulator(page)
        await human_sim.warm_up()

        result = {
            "url": post_url,
            "title": "",
            "content": "",
            "author": "",
            "board": "",
            "reactions": {},
            "comments_count": 0,
        }

        try:
            # 模擬人類導航
            await simulate_mouse_movement(page, 0.5)
            await page.goto(post_url, wait_until="domcontentloaded")
            await simulate_reading_pause(1.5, 3.0)

            # 模擬閱讀行為
            await simulate_scroll(page, random.randint(2, 4))
            await simulate_mouse_movement(page, 1.0)

            # 等待內容載入
            await page.wait_for_load_state("networkidle")

            # 提取標題
            title_el = await page.query_selector('h1')
            if title_el:
                result["title"] = await title_el.inner_text()

            # 提取內容
            content_el = await page.query_selector('article')
            if content_el:
                result["content"] = await content_el.inner_text()

            # 提取作者資訊
            author_el = await page.query_selector('a[href^="/@"]')
            if author_el:
                result["author"] = await author_el.inner_text()

            print(f"✅ 成功抓取文章: {result['title'][:50]}...")

        except Exception as e:
            print(f"❌ 抓取文章失敗: {e}")
            result["error"] = str(e)
        finally:
            await page.close()

        return result

    async def search_posts(
        self,
        keyword: str,
        forum: Optional[str] = None,
        count: int = 20,
    ) -> List[dict]:
        """
        搜尋 Dcard 文章

        Args:
            keyword: 搜尋關鍵字
            forum: 限定看板 (可選)
            count: 要抓取的文章數量

        Returns:
            搜尋結果列表
        """
        if not self._context:
            raise RuntimeError("Crawler not started. Call start() first.")

        page = await self._context.new_page()
        human_sim = HumanBehaviorSimulator(page)
        await human_sim.warm_up()

        results = []
        try:
            # 構建搜尋 URL
            search_url = f"https://www.dcard.tw/search?query={keyword}"
            if forum:
                search_url += f"&forum={forum}"

            # 模擬人類導航
            await simulate_mouse_movement(page, 0.5)
            await page.goto(search_url, wait_until="domcontentloaded")
            await simulate_reading_pause(1.5, 2.5)

            # 捲動載入更多結果
            for _ in range(count // 10 + 2):
                await simulate_scroll(page, 2)
                await simulate_reading_pause(0.8, 1.5)

            # 提取搜尋結果
            articles = await page.query_selector_all('article')
            for i, article in enumerate(articles[:count]):
                try:
                    title_el = await article.query_selector('h2')
                    title = await title_el.inner_text() if title_el else ""

                    link_el = await article.query_selector('a[href*="/p/"]')
                    link = await link_el.get_attribute('href') if link_el else ""

                    summary_el = await article.query_selector('p')
                    summary = await summary_el.inner_text() if summary_el else ""

                    results.append({
                        "index": i + 1,
                        "title": title.strip(),
                        "link": f"https://www.dcard.tw{link}" if link and not link.startswith('http') else link,
                        "summary": summary.strip()[:200],
                    })
                except Exception as e:
                    print(f"  ⚠️ 結果 {i+1} 解析失敗: {e}")

            print(f"✅ 搜尋 '{keyword}' 找到 {len(results)} 篇文章")

        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
        finally:
            await page.close()

        return results


async def main():
    """測試 Dcard 爬蟲"""
    async with DcardCrawler(headless=False) as crawler:
        # 測試抓取熱門文章
        print("\n📰 抓取熱門文章...")
        posts = await crawler.fetch_forum_posts("talk", count=10)
        for post in posts:
            print(f"  [{post['index']}] {post['title'][:40]}...")

        # 測試搜尋
        print("\n🔍 搜尋測試...")
        results = await crawler.search_posts("工作", count=5)
        for r in results:
            print(f"  [{r['index']}] {r['title'][:40]}...")


if __name__ == "__main__":
    asyncio.run(main())
