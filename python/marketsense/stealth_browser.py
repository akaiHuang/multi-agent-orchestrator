"""
Stealth Browser Configuration
進階反偵測瀏覽器配置 - 解決 WebGL SwiftShader 問題
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional, Dict, Any, List

# 獲取真實的 GPU 資訊
REAL_GPU_INFO = {
    "macos_apple_silicon": {
        "vendor": "Apple",
        "renderer": "Apple M1 Pro",
        "vendor_id": "0x106b",
    },
    "macos_intel": {
        "vendor": "Intel Inc.",
        "renderer": "Intel Iris Plus Graphics",
        "vendor_id": "0x8086",
    },
    "windows_nvidia": {
        "vendor": "NVIDIA Corporation",
        "renderer": "NVIDIA GeForce RTX 3080",
        "vendor_id": "0x10de",
    },
    "windows_amd": {
        "vendor": "AMD",
        "renderer": "AMD Radeon RX 6800 XT",
        "vendor_id": "0x1002",
    },
}


def get_chromium_args_for_real_gpu() -> List[str]:
    """
    獲取用於啟用真實 GPU 的 Chromium 啟動參數
    解決 SwiftShader 問題
    """
    return [
        # 啟用 GPU 加速（關鍵！）
        "--enable-gpu",
        "--enable-webgl",
        "--enable-accelerated-2d-canvas",
        
        # 禁用軟體渲染（避免 SwiftShader）
        "--disable-software-rasterizer",
        
        # 啟用硬體加速
        "--ignore-gpu-blocklist",
        "--enable-gpu-rasterization",
        
        # 使用 EGL 而非 SwiftShader
        "--use-gl=egl",
        "--use-angle=default",
        
        # WebGL 相關
        "--enable-unsafe-webgpu",
        "--enable-features=Vulkan",
        
        # 反偵測基礎參數
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        
        # 隱藏自動化標記
        "--disable-automation",
        
        # 性能優化
        "--no-first-run",
        "--no-default-browser-check",
        
        # 安全相關
        "--disable-web-security",
        "--allow-running-insecure-content",
    ]


def get_enhanced_stealth_script(gpu_profile: str = "macos_apple_silicon") -> str:
    """
    獲取增強版反偵測腳本
    包含更完整的 WebGL 偽裝
    """
    gpu = REAL_GPU_INFO.get(gpu_profile, REAL_GPU_INFO["macos_apple_silicon"])
    
    return f"""
() => {{
    // ===== WebGL 深度偽裝 =====
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {{
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) return '{gpu["vendor"]}';
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) return '{gpu["renderer"]}';
        // VERSION
        if (param === 7938) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
        // SHADING_LANGUAGE_VERSION
        if (param === 35724) return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
        return originalGetParameter.call(this, param);
    }};

    // WebGL2 偽裝
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(param) {{
            if (param === 37445) return '{gpu["vendor"]}';
            if (param === 37446) return '{gpu["renderer"]}';
            if (param === 7938) return 'WebGL 2.0 (OpenGL ES 3.0 Chromium)';
            if (param === 35724) return 'WebGL GLSL ES 3.00 (OpenGL ES GLSL ES 3.0 Chromium)';
            return originalGetParameter2.call(this, param);
        }};
    }}

    // ===== Canvas 指紋噪音 =====
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {{
        if (type === 'image/png' || type === 'image/jpeg') {{
            const context = this.getContext('2d');
            if (context) {{
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    // 添加微小噪音 (不影響視覺效果)
                    imageData.data[i] = imageData.data[i] ^ (Math.random() > 0.99 ? 1 : 0);
                }}
                context.putImageData(imageData, 0, 0);
            }}
        }}
        return originalToDataURL.apply(this, arguments);
    }};

    // ===== Navigator 偽裝 =====
    // 移除 webdriver 屬性
    delete navigator.__proto__.webdriver;
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});

    // 偽裝 plugins (更真實)
    Object.defineProperty(navigator, 'plugins', {{
        get: () => {{
            const plugins = [
                {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }},
                {{ name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chromium PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
            ];
            plugins.item = (index) => plugins[index];
            plugins.namedItem = (name) => plugins.find(p => p.name === name);
            plugins.refresh = () => {{}};
            return plugins;
        }},
        configurable: true
    }});

    // 偽裝 mimeTypes
    Object.defineProperty(navigator, 'mimeTypes', {{
        get: () => {{
            const mimeTypes = [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
                {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
            ];
            mimeTypes.item = (index) => mimeTypes[index];
            mimeTypes.namedItem = (type) => mimeTypes.find(m => m.type === type);
            return mimeTypes;
        }},
        configurable: true
    }});

    // ===== Chrome Runtime 偽裝 =====
    window.chrome = {{
        runtime: {{
            connect: () => ({{}}),
            sendMessage: () => {{}},
            onMessage: {{ addListener: () => {{}} }},
            onConnect: {{ addListener: () => {{}} }},
        }},
        loadTimes: () => ({{
            requestTime: Date.now() / 1000 - Math.random() * 10,
            startLoadTime: Date.now() / 1000 - Math.random() * 5,
            commitLoadTime: Date.now() / 1000 - Math.random() * 3,
            finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 2,
            finishLoadTime: Date.now() / 1000 - Math.random(),
            firstPaintTime: Date.now() / 1000 - Math.random() * 4,
            firstPaintAfterLoadTime: 0,
            navigationType: 'Other',
        }}),
        csi: () => ({{
            onloadT: Date.now(),
            pageT: Date.now() - Math.random() * 1000,
            startE: Date.now() - Math.random() * 2000,
            tran: 15,
        }}),
        app: {{
            isInstalled: false,
            InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
            RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
        }},
    }};

    // ===== Permissions API 偽裝 =====
    const originalQuery = navigator.permissions.query;
    navigator.permissions.query = (parameters) => {{
        if (parameters.name === 'notifications') {{
            return Promise.resolve({{ state: Notification.permission, onchange: null }});
        }}
        return originalQuery.call(navigator.permissions, parameters);
    }};

    // ===== 隱藏 Headless 特徵 =====
    // 偽裝 connection.rtt (移除 Headless 特徵)
    if (navigator.connection) {{
        Object.defineProperty(navigator.connection, 'rtt', {{
            get: () => {{ return 50 + Math.floor(Math.random() * 100); }},
            configurable: true
        }});
    }}

    // 添加 MediaSession API (真實瀏覽器會有)
    if (!navigator.mediaSession) {{
        navigator.mediaSession = {{
            metadata: null,
            playbackState: 'none',
            setActionHandler: () => {{}},
            setPositionState: () => {{}},
        }};
    }}

    // ===== 防止 iframe 偵測 =====
    try {{
        if (window.self !== window.top) {{
            Object.defineProperty(window, 'self', {{
                get: () => window.top,
                configurable: true
            }});
        }}
    }} catch (e) {{}}

    // ===== 時間一致性 =====
    const originalDateNow = Date.now;
    const timeOffset = Math.random() * 100 - 50;
    Date.now = () => originalDateNow() + timeOffset;

    console.log('🛡️ Stealth scripts applied successfully');
}}
"""


def get_browser_launch_options(
    headless: bool = False,  # 建議使用 headed 模式
    gpu_profile: str = "macos_apple_silicon"
) -> Dict[str, Any]:
    """
    獲取完整的瀏覽器啟動選項
    """
    args = get_chromium_args_for_real_gpu()
    
    if headless:
        # 使用新版 headless 模式 (更難偵測)
        args.append("--headless=new")
    
    return {
        "headless": headless,
        "args": args,
        "ignore_default_args": [
            "--enable-automation",
            "--enable-blink-features=IdleDetection",
        ],
        # 慢速模式 (更人性化)
        "slow_mo": 50,
    }


async def create_stealth_context(browser, storage_state: Optional[str] = None) -> Any:
    """
    創建具有完整反偵測的瀏覽器上下文
    """
    from .human_behavior import get_browser_context_options
    
    context_options = get_browser_context_options()
    
    if storage_state and os.path.exists(storage_state):
        context_options["storage_state"] = storage_state
    
    context = await browser.new_context(**context_options)
    
    # 注入反偵測腳本
    await context.add_init_script(get_enhanced_stealth_script())
    
    return context


# ===== 使用範例 =====
"""
from playwright.async_api import async_playwright
from stealth_browser import get_browser_launch_options, create_stealth_context, get_enhanced_stealth_script

async def main():
    async with async_playwright() as p:
        # 使用 headed 模式 + GPU 加速 = 最難偵測
        browser = await p.chromium.launch(**get_browser_launch_options(headless=False))
        
        # 創建反偵測上下文
        context = await create_stealth_context(browser)
        
        # 在頁面上額外注入腳本
        page = await context.new_page()
        await page.add_init_script(get_enhanced_stealth_script())
        
        # 開始瀏覽
        await page.goto('https://bot.sannysoft.com/')
"""
