from __future__ import annotations

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    _FIREBASE_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback for test environments
    firebase_admin = None
    credentials = None
    firestore = None
    storage = None
    _FIREBASE_AVAILABLE = False

from .config import Settings


def get_db_and_bucket(settings: Settings):
    if not _FIREBASE_AVAILABLE:
        raise RuntimeError("firebase-admin is not installed. Install requirements.txt to use Firebase.")
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_service_account)
        options = {"storageBucket": settings.firebase_storage_bucket} if settings.firebase_storage_bucket else {}
        firebase_admin.initialize_app(cred, options)

    db = firestore.client()
    bucket = storage.bucket()
    return db, bucket
