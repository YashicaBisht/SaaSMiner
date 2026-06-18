import hashlib
import json
import os
import time
from typing import Any, Dict, Optional

CACHE_DIR = os.environ.get("AI_CACHE_DIR", "./cache/ai_responses")
CACHE_TTL_SECONDS = int(os.environ.get("AI_CACHE_TTL_SECONDS", str(7 * 24 * 3600)))


class AICache:
    """File-based cache for Gemini responses to reduce token usage and latency."""

    @staticmethod
    def _cache_path(cache_key: str) -> str:
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, f"{cache_key}.json")

    @staticmethod
    def make_key(namespace: str, payload: str) -> str:
        digest = hashlib.sha256(f"{namespace}:{payload}".encode("utf-8")).hexdigest()
        return digest

    @staticmethod
    def get(cache_key: str) -> Optional[Dict[str, Any]]:
        path = AICache._cache_path(cache_key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if time.time() - entry.get("cached_at", 0) > CACHE_TTL_SECONDS:
                return None
            return entry.get("data")
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def set(cache_key: str, data: Dict[str, Any]) -> None:
        path = AICache._cache_path(cache_key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"cached_at": time.time(), "data": data}, f, ensure_ascii=False)
        except OSError:
            pass
