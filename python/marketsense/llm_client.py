from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from .config import Settings
from .utils import extract_json, normalize_analysis


class LLMClient:
    def __init__(self, settings: Settings, dry_run: bool = False) -> None:
        self.settings = settings
        self.dry_run = dry_run

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if self.dry_run or self.settings.llm_provider.lower() == "mock":
            return {"mock": True}

        if not self.settings.ollama_api_key:
            return {"error": "Missing OLLAMA_API_KEY"}

        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        headers = {"Content-Type": "application/json"}
        key_header = self.settings.ollama_api_key_header
        if key_header.lower() == "authorization":
            headers["Authorization"] = f"Bearer {self.settings.ollama_api_key}"
        else:
            headers[key_header] = self.settings.ollama_api_key

        base_url = self.settings.ollama_base_url.rstrip("/")
        mode = self.settings.ollama_api_mode.lower()

        if mode == "ollama":
            url = f"{base_url}/api/chat"
        else:
            url = f"{base_url}/v1/chat/completions"

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.settings.llm_timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return {"error": f"LLM request failed: {exc}"}

        if mode == "ollama":
            content = data.get("message", {}).get("content", "")
        else:
            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""

        try:
            raw = extract_json(content)
        except Exception:
            raw = {"error": "Failed to parse LLM JSON", "raw": content}

        return raw

    def analyze(self, text: str, title: str = "", url: str = "") -> Dict[str, Any]:
        if not text:
            return {"error": "No content extracted"}

        if self.dry_run or self.settings.llm_provider.lower() == "mock":
            return {
                "sentiment_score": 7.5,
                "sentiment_summary": "測試模式：略過 LLM 呼叫。",
                "key_discussions": ["測試", "示例", "mock"],
                "buying_intent": "中",
            }

        prompt = (
            "你是市場輿情分析師。請分析以下內容並以 JSON 回傳：\n"
            "- sentiment_score (1-10)\n"
            "- sentiment_summary (摘要)\n"
            "- key_discussions (3個討論點)\n"
            "- buying_intent (高/中/低)\n\n"
            f"標題: {title}\nURL: {url}\n內容:\n{text}"
        )

        raw = self._call_llm("你是專業的市場輿情分析師，輸出必須是 JSON。", prompt)
        if "error" in raw:
            return raw
        if raw.get("mock") is True:
            return {
                "sentiment_score": 7.5,
                "sentiment_summary": "測試模式：略過 LLM 呼叫。",
                "key_discussions": ["測試", "示例", "mock"],
                "buying_intent": "中",
            }

        return normalize_analysis(raw)

    def review_quality(
        self,
        analysis: Dict[str, Any],
        title: str = "",
        url: str = "",
        brand: str = "",
        product: str = "",
        objective: str = "",
    ) -> Dict[str, Any]:
        if self.dry_run or self.settings.llm_provider.lower() == "mock":
            return {
                "quality_score": 85,
                "quality_pass": True,
                "issues": [],
                "notes": "測試模式：略過 LLM 回測。",
                "optimized_insights": {
                    "key_messages": ["優化亮點 1", "優化亮點 2"],
                    "ad_angles": ["角度 A", "角度 B"],
                    "audience_fit": ["目標族群 1"],
                    "objections": ["疑慮 1"],
                    "recommended_copy": ["文案範例 1"],
                },
            }

        prompt = (
            "你是行銷資料質量審查與優化專家。請評估下列分析結果，"
            "判斷是否可作為行銷文案與廣告策略依據，並輸出 JSON：\n"
            "- quality_score (0-100)\n"
            "- quality_pass (true/false)\n"
            "- issues (列表)\n"
            "- notes (簡短說明)\n"
            "- optimized_insights: {key_messages, ad_angles, audience_fit, objections, recommended_copy}\n\n"
            f"品牌: {brand}\n產品: {product}\n目的: {objective}\n"
            f"標題: {title}\nURL: {url}\n分析結果: {analysis}"
        )

        raw = self._call_llm("你是嚴謹的資料品質審查者，輸出必須是 JSON。", prompt)
        if "error" in raw:
            return raw
        if raw.get("mock") is True:
            return {
                "quality_score": 85,
                "quality_pass": True,
                "issues": [],
                "notes": "測試模式：略過 LLM 回測。",
                "optimized_insights": {
                    "key_messages": ["優化亮點 1", "優化亮點 2"],
                    "ad_angles": ["角度 A", "角度 B"],
                    "audience_fit": ["目標族群 1"],
                    "objections": ["疑慮 1"],
                    "recommended_copy": ["文案範例 1"],
                },
            }

        return raw
