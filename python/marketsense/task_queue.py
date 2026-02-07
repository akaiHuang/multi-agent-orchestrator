from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Tuple

try:
    from google.api_core.exceptions import FailedPrecondition
except Exception:  # pragma: no cover
    FailedPrecondition = Exception

try:
    from firebase_admin import firestore
except ImportError:  # pragma: no cover
    class _FirestoreFallback:
        SERVER_TIMESTAMP = "SERVER_TIMESTAMP"

        @staticmethod
        def transactional(func):
            return func

    firestore = _FirestoreFallback()

from .utils import normalize_url, url_hash


ACTIVE_STATUSES = {"pending", "running", "downloaded", "analyzed"}


def enqueue_urls(
    db,
    urls: Iterable[str],
    allow_duplicates: bool = False,
    brand: str = "",
    product: str = "",
    objective: str = "",
) -> int:
    count = 0
    for raw_url in urls:
        raw_url = raw_url.strip()
        if not raw_url:
            continue

        normalized = normalize_url(raw_url)
        hash_id = url_hash(normalized)
        payload = {
            "url": raw_url,
            "normalized_url": normalized,
            "url_hash": hash_id,
            "status": "pending",
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        if brand:
            payload["brand"] = brand
        if product:
            payload["product"] = product
        if objective:
            payload["objective"] = objective

        if allow_duplicates:
            db.collection("crawling_tasks").add(payload)
            count += 1
            continue

        doc_ref = db.collection("crawling_tasks").document(hash_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            status = data.get("status", "")
            if status in ACTIVE_STATUSES:
                continue
            doc_ref.update(
                {
                    "status": "pending",
                    "error_log": "",
                    "last_error": "",
                    "requeued_at": firestore.SERVER_TIMESTAMP,
                }
            )
            count += 1
        else:
            doc_ref.set(payload)
            count += 1

    return count


def claim_pending_tasks(db, limit: int, lease_seconds: int = 600) -> List[Tuple[object, dict]]:
    now = datetime.now(timezone.utc)
    claimed: List[Tuple[object, dict]] = []

    docs = (
        db.collection("crawling_tasks")
        .where("status", "==", "pending")
        .limit(limit * 3 if limit else 50)
        .stream()
    )

    for doc in docs:
        if len(claimed) >= limit:
            break

        doc_ref = doc.reference

        @firestore.transactional
        def _claim(transaction, target_ref):
            snapshot = target_ref.get(transaction=transaction)
            if not snapshot.exists:
                return None
            data = snapshot.to_dict() or {}
            status = data.get("status")
            if status != "pending":
                return None
            locked_until = data.get("locked_until")
            if locked_until and locked_until > now:
                return None

            transaction.update(
                target_ref,
                {
                    "status": "running",
                    "locked_at": now,
                    "locked_until": now + timedelta(seconds=lease_seconds),
                },
            )
            return data

        transaction = db.transaction()
        claimed_data = _claim(transaction, doc_ref)
        if claimed_data is not None:
            claimed.append((doc_ref, claimed_data))

    return claimed


def fetch_pending_tasks(db, limit: int) -> List[Tuple[object, dict]]:
    docs = (
        db.collection("crawling_tasks")
        .where("status", "==", "pending")
        .limit(limit)
        .stream()
    )
    return [(doc.reference, doc.to_dict()) for doc in docs]


def reclaim_expired_leases(db, limit: int, now: datetime) -> int:
    reclaimed = 0
    try:
        docs = (
            db.collection("crawling_tasks")
            .where("status", "==", "running")
            .where("locked_until", "<", now)
            .limit(limit)
            .stream()
        )
        for doc in docs:
            doc.reference.update(
                {
                    "status": "pending",
                    "locked_at": None,
                    "locked_until": None,
                    "reclaimed_at": firestore.SERVER_TIMESTAMP,
                }
            )
            reclaimed += 1
    except FailedPrecondition as exc:
        print(f"⚠️ Firestore index missing for reclaim_expired_leases: {exc}")
    return reclaimed


def requeue_stale_tasks(db, status: str, older_than: datetime, limit: int) -> int:
    reclaimed = 0
    field = "analyzed_at" if status == "analyzed" else "downloaded_at"
    try:
        docs = (
            db.collection("crawling_tasks")
            .where("status", "==", status)
            .where(field, "<", older_than)
            .limit(limit)
            .stream()
        )
        for doc in docs:
            doc.reference.update(
                {
                    "status": "pending",
                    "requeued_at": firestore.SERVER_TIMESTAMP,
                    "locked_at": None,
                    "locked_until": None,
                }
            )
            reclaimed += 1
    except FailedPrecondition as exc:
        print(f"⚠️ Firestore index missing for requeue_stale_tasks({status}): {exc}")
    return reclaimed


def requeue_error_tasks(db, older_than: datetime, limit: int) -> int:
    reclaimed = 0
    try:
        docs = (
            db.collection("crawling_tasks")
            .where("status", "==", "error")
            .where("failed_at", "<", older_than)
            .limit(limit)
            .stream()
        )
        for doc in docs:
            doc.reference.update(
                {
                    "status": "pending",
                    "requeued_at": firestore.SERVER_TIMESTAMP,
                    "locked_at": None,
                    "locked_until": None,
                    "error_log": "",
                    "last_error": "",
                }
            )
            reclaimed += 1
    except FailedPrecondition as exc:
        print(f"⚠️ Firestore index missing for requeue_error_tasks: {exc}")
    return reclaimed
