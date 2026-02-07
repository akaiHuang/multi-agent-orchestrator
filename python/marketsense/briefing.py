from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

try:
    from firebase_admin import firestore
except ImportError:  # pragma: no cover
    class _FirestoreFallback:
        SERVER_TIMESTAMP = "SERVER_TIMESTAMP"

    firestore = _FirestoreFallback()

from .config import Settings
from .firebase_client import get_db_and_bucket
from .llm_client import LLMClient


DEFAULT_QUESTIONS = [
    {
        "question": "品牌目前的主要客群是誰？（年齡/職業/生活型態）",
        "purpose": "定義 TA",
        "priority": "high",
    },
    {
        "question": "產品最核心的差異化是什麼？（功能/情感/體驗）",
        "purpose": "明確價值主張",
        "priority": "high",
    },
    {
        "question": "本次行銷的目標為何？（提升知名度/轉換/互動）",
        "purpose": "定義 KPI",
        "priority": "high",
    },
    {
        "question": "競品或替代方案有哪些？",
        "purpose": "競品對比",
        "priority": "medium",
    },
    {
        "question": "是否有任何限制或合規要求？",
        "purpose": "合規",
        "priority": "medium",
    },
]


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass
    import re

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def generate_questions(client: LLMClient, brand: str, product: str, objective: str, round_index: int) -> List[Dict[str, Any]]:
    if client.dry_run or client.settings.llm_provider.lower() == "mock":
        return DEFAULT_QUESTIONS

    prompt = (
        "請根據以下品牌/產品資訊，產出一組行銷分析所需的提問清單（JSON）。\n"
        "JSON 格式：{questions:[{question,purpose,priority}]}\n\n"
        f"品牌: {brand}\n產品: {product}\n目標: {objective}\n回合: {round_index}\n"
    )
    raw = client._call_llm("你是行銷策略助理，輸出必須是 JSON。", prompt)
    if "error" in raw or not raw:
        return DEFAULT_QUESTIONS
    return raw.get("questions", DEFAULT_QUESTIONS)


def answer_questions_auto(client: LLMClient, brand: str, product: str, objective: str, questions: List[Dict[str, Any]]) -> Dict[str, str]:
    if client.dry_run or client.settings.llm_provider.lower() == "mock":
        return {q.get("question", "Q"): "（自動假設）待補充" for q in questions}

    prompt = (
        "請以品牌行銷分析師的角度，為下列問題提供合理假設回答。"
        "請以 JSON 回傳：{answers:{question:answer}}\n\n"
        f"品牌: {brand}\n產品: {product}\n目標: {objective}\n"
        f"問題: {[q.get('question') for q in questions]}"
    )
    raw = client._call_llm("你是行銷分析師，輸出必須是 JSON。", prompt)
    if "error" in raw or not raw:
        return {q.get("question", "Q"): "（自動假設）待補充" for q in questions}
    return raw.get("answers", {})


def evaluate_sufficiency(client: LLMClient, answers: Dict[str, str]) -> Dict[str, Any]:
    if client.dry_run or client.settings.llm_provider.lower() == "mock":
        return {"sufficient": True, "missing_info": [], "follow_up_questions": []}

    prompt = (
        "請判斷下列回答是否足以產出行銷分析報告。"
        "輸出 JSON：{sufficient:boolean, missing_info:[...], follow_up_questions:[...]}\n\n"
        f"回答: {answers}"
    )
    raw = client._call_llm("你是行銷資料審查者，輸出必須是 JSON。", prompt)
    if "error" in raw or not raw:
        return {"sufficient": True, "missing_info": [], "follow_up_questions": []}
    return raw


def generate_report(
    client: LLMClient,
    brand: str,
    product: str,
    objective: str,
    answers: Dict[str, str],
) -> Dict[str, Any]:
    if client.dry_run or client.settings.llm_provider.lower() == "mock":
        return {
            "brand_core_message": "（示例）給你一個什麼都不做的理由",
            "ta_situation": ["壓力大", "需要放鬆"],
            "hot_topics": ["慢生活", "療癒"],
            "creative_concepts": {
                "A": ["看不見的價值"],
                "B": ["心靈充電"],
                "C": ["生活體驗與策展"],
            },
            "data_collection_strategy": {
                "platforms": ["社群", "電商", "論壇"],
                "keywords": ["香氛皂", "療癒"],
            },
        }

    prompt = (
        "請根據以下資訊產出完整行銷分析報告，輸出 JSON。\n"
        "JSON 結構: {brand_core_message, ta_situation[], hot_topics[], creative_concepts:{A[],B[],C[]}, data_collection_strategy:{platforms[], keywords[], queries[]}}\n\n"
        f"品牌: {brand}\n產品: {product}\n目標: {objective}\n"
        f"回答: {answers}\n"
    )
    raw = client._call_llm("你是行銷策略師，輸出必須是 JSON。", prompt)
    if "error" in raw or not raw:
        return {"error": raw.get("error", "Failed to generate report"), "raw": raw}
    return raw


def save_brief_to_firestore(settings: Settings, payload: Dict[str, Any]) -> None:
    db, _ = get_db_and_bucket(settings)
    db.collection("marketing_briefs").add(payload)


def run_briefing(
    settings: Settings,
    brand: str,
    product: str,
    objective: str,
    mode: str = "interactive",
    max_rounds: int = 2,
    dry_run: bool = False,
    save_firestore: bool = True,
) -> Dict[str, Any]:
    client = LLMClient(settings, dry_run=dry_run)

    answers: Dict[str, str] = {}
    for round_idx in range(1, max_rounds + 1):
        questions = generate_questions(client, brand, product, objective, round_idx)
        if mode == "auto":
            auto_answers = answer_questions_auto(client, brand, product, objective, questions)
            answers.update(auto_answers)
        else:
            for q in questions:
                q_text = q.get("question", "")
                if not q_text:
                    continue
                user_answer = input(f"{q_text}\n> ").strip()
                if user_answer:
                    answers[q_text] = user_answer

        review = evaluate_sufficiency(client, answers)
        if review.get("sufficient") is True:
            break
        follow_ups = review.get("follow_up_questions", [])
        if follow_ups:
            for q_text in follow_ups:
                if mode == "auto":
                    answers[q_text] = "（自動補充）"
                else:
                    user_answer = input(f"{q_text}\n> ").strip()
                    if user_answer:
                        answers[q_text] = user_answer

    report = generate_report(client, brand, product, objective, answers)
    result = {
        "brand": brand,
        "product": product,
        "objective": objective,
        "answers": answers,
        "report": report,
    }

    if save_firestore:
        payload = {
            "brand": brand,
            "product": product,
            "objective": objective,
            "answers": answers,
            "report": report,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        save_brief_to_firestore(settings, payload)

    return result
