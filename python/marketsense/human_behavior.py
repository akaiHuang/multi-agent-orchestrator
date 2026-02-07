"""
Human Behavior Simulation Module
模擬人類瀏覽行為，降低被反爬蟲系統偵測的機率
"""
from __future__ import annotations

import asyncio
import random
from typing import List, Optional, Tuple


# 動態 User-Agent 輪換列表（2024-2026 最新版本）
USER_AGENTS = [
    # Chrome (macOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
]

# 常見螢幕解析度
SCREEN_RESOLUTIONS = [
    (1920, 1080),
    (2560, 1440),
    (1440, 900),
    (1680, 1050),
    (1366, 768),
    (2880, 1620),  # Retina
    (3840, 2160),  # 4K
]

# 時區列表
TIMEZONES = [
    "Asia/Taipei",
    "Asia/Hong_Kong",
    "Asia/Tokyo",
    "America/Los_Angeles",
    "America/New_York",
]


def get_random_user_agent() -> str:
    """隨機選擇 User-Agent"""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """隨機選擇視窗大小"""
    width, height = random.choice(SCREEN_RESOLUTIONS)
    # 模擬真實的瀏覽器視窗（不是全螢幕）
    width = width - random.randint(0, 200)
    height = height - random.randint(100, 200)
    return {"width": width, "height": height}


def get_random_timezone() -> str:
    """隨機選擇時區"""
    return random.choice(TIMEZONES)


async def simulate_mouse_movement(page, duration: float = 2.0) -> None:
    """
    模擬人類滑鼠移動軌跡
    使用貝茲曲線產生自然的移動路徑
    """
    viewport = page.viewport_size
    if not viewport:
        return

    width = viewport.get("width", 1200)
    height = viewport.get("height", 800)

    # 產生 3-6 個隨機路徑點
    num_points = random.randint(3, 6)
    points: List[Tuple[int, int]] = []

    for _ in range(num_points):
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        points.append((x, y))

    # 沿路徑移動滑鼠
    for x, y in points:
        # 添加微小的抖動，模擬人手的不穩定
        jitter_x = random.randint(-3, 3)
        jitter_y = random.randint(-3, 3)

        await page.mouse.move(x + jitter_x, y + jitter_y)
        await asyncio.sleep(random.uniform(0.1, 0.4))


async def simulate_scroll(page, scroll_count: int = 3) -> None:
    """
    模擬人類捲動行為
    包含不規則的捲動距離和速度
    """
    for _ in range(scroll_count):
        # 隨機捲動距離 (100-500 像素)
        scroll_amount = random.randint(100, 500)

        # 決定方向 (主要向下，偶爾向上)
        if random.random() < 0.85:
            direction = scroll_amount
        else:
            direction = -scroll_amount // 2

        await page.mouse.wheel(0, direction)
        # 人類會在捲動後停頓閱讀
        await asyncio.sleep(random.uniform(0.5, 2.0))


async def simulate_reading_pause(min_seconds: float = 1.0, max_seconds: float = 5.0) -> None:
    """
    模擬人類閱讀停頓
    """
    pause = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(pause)


async def simulate_random_clicks(page, count: int = 2) -> None:
    """
    模擬隨機點擊（非連結區域）
    """
    viewport = page.viewport_size
    if not viewport:
        return

    width = viewport.get("width", 1200)
    height = viewport.get("height", 800)

    for _ in range(count):
        # 避開邊緣區域
        x = random.randint(100, width - 100)
        y = random.randint(100, height - 100)

        # 模擬移動到點擊位置
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # 隨機決定是否真的點擊（避免觸發不想要的操作）
        if random.random() < 0.3:
            await page.mouse.click(x, y)

        await asyncio.sleep(random.uniform(0.3, 1.0))


async def human_like_navigation(page, url: str, settings=None) -> None:
    """
    執行類人的網頁瀏覽流程
    """
    # 1. 導航前的短暫延遲（模擬思考）
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # 2. 導航到頁面
    await page.goto(url, wait_until="domcontentloaded")

    # 3. 等待頁面基本載入
    await asyncio.sleep(random.uniform(1.0, 2.0))

    # 4. 模擬初始滑鼠移動
    await simulate_mouse_movement(page, duration=1.5)

    # 5. 模擬閱讀停頓
    await simulate_reading_pause(1.0, 3.0)

    # 6. 模擬捲動閱讀
    await simulate_scroll(page, scroll_count=random.randint(2, 4))

    # 7. 再次滑鼠移動
    await simulate_mouse_movement(page, duration=1.0)

    # 8. 最終等待（確保動態內容載入）
    await page.wait_for_load_state("networkidle")


def get_browser_context_options() -> dict:
    """
    取得更真實的瀏覽器 context 設定
    """
    viewport = get_random_viewport()

    return {
        "user_agent": get_random_user_agent(),
        "viewport": viewport,
        "screen": {
            "width": viewport["width"] + random.randint(0, 200),
            "height": viewport["height"] + random.randint(100, 200),
        },
        "locale": random.choice(["zh-TW", "zh-HK", "en-US"]),
        "timezone_id": get_random_timezone(),
        "color_scheme": random.choice(["light", "dark"]),
        "has_touch": random.choice([True, False]),
        "is_mobile": False,
        "java_script_enabled": True,
        "accept_downloads": True,
        "ignore_https_errors": True,
        # WebGL 偽裝
        "extra_http_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
    }


# 進階：WebGL 偽裝腳本
WEBGL_SPOOF_SCRIPT = """
() => {
    // 偽裝 WebGL Vendor 和 Renderer
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';  // UNMASKED_VENDOR_WEBGL
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';  // UNMASKED_RENDERER_WEBGL
        }
        return getParameter.call(this, parameter);
    };

    const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter2.call(this, parameter);
    };

    // 隱藏 webdriver 屬性
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });

    // 偽裝 plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ],
    });

    // 偽裝 languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-TW', 'zh', 'en-US', 'en'],
    });

    // 模擬 Chrome runtime
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {},
    };
}
"""


async def apply_stealth_scripts(page) -> None:
    """
    應用進階反偵測腳本
    """
    await page.add_init_script(WEBGL_SPOOF_SCRIPT)


class HumanBehaviorSimulator:
    """
    人類行為模擬器類別
    統一管理所有擬人行為
    """

    def __init__(self, page, settings=None):
        self.page = page
        self.settings = settings

    async def warm_up(self) -> None:
        """預熱：應用反偵測腳本"""
        await apply_stealth_scripts(self.page)

    async def browse_naturally(self, url: str) -> None:
        """自然瀏覽一個頁面"""
        await human_like_navigation(self.page, url, self.settings)

    async def random_activity(self, duration: float = 5.0) -> None:
        """
        執行一段隨機的人類活動
        """
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < duration:
            action = random.choice(["move", "scroll", "pause"])
            if action == "move":
                await simulate_mouse_movement(self.page, 1.0)
            elif action == "scroll":
                await simulate_scroll(self.page, 1)
            else:
                await simulate_reading_pause(0.5, 2.0)
