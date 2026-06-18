import json
import logging
import os
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .ai_cache import AICache

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Gemini import with debug
try:
    import google.generativeai as genai
    print("✅ Gemini imported successfully")
except Exception as e:
    print("❌ Gemini import error:", repr(e))
    genai = None  # type: ignore


class AIServiceError(Exception):
    """Raised when the AI service cannot produce a valid response."""


class AIService:
    """Centralized Gemini integration with retries, caching, and JSON validation."""

    _configured = False

    @classmethod
    def is_available(cls) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY")) and genai is not None

    @classmethod
    def configure(cls) -> None:
        print("\n========== GEMINI DEBUG ==========")
        print("Python EXE:", sys.executable)
        print("GEMINI_API_KEY exists:", bool(os.environ.get("GEMINI_API_KEY")))
        print("genai module:", genai)
        print("==================================\n")

        if cls._configured:
            return

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.warning(
                "GEMINI_API_KEY not set — AI engines will use rule-based fallbacks."
            )
            return

        if genai is None:
            logger.warning(
                "google-generativeai not installed — AI engines will use rule-based fallbacks."
            )
            return

        try:
            genai.configure(api_key=api_key)
            cls._configured = True
            print("✅ Gemini configured successfully")
        except Exception as e:
            print("❌ Gemini configure error:", repr(e))

    @classmethod
    def _get_model(cls):
        cls.configure()

        if genai is None:
            raise AIServiceError("Gemini library is unavailable.")

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

        return genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": float(
                    os.environ.get("GEMINI_TEMPERATURE", "0.2")
                ),
                "response_mime_type": "application/json",
            },
        )

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as exc:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)

            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            raise AIServiceError(
                f"Invalid JSON from Gemini: {exc}"
            ) from exc

    @staticmethod
    def _validate_fields(
        data: Dict[str, Any],
        required: List[str]
    ) -> Dict[str, Any]:
        missing = [
            field for field in required
            if field not in data
        ]

        if missing:
            raise AIServiceError(
                f"AI response missing required fields: "
                f"{', '.join(missing)}"
            )

        return data

    @classmethod
    def generate_json(
        cls,
        prompt: str,
        *,
        namespace: str,
        cache_payload: str,
        required_fields: List[str],
        validator: Optional[
            Callable[[Dict[str, Any]], Dict[str, Any]]
        ] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:

        if not cls.is_available():
            raise AIServiceError(
                "Gemini API is not configured."
            )

        cache_key = AICache.make_key(
            namespace,
            cache_payload
        )

        if use_cache:
            cached = AICache.get(cache_key)

            if cached is not None:
                logger.debug(
                    "AI cache hit for namespace=%s",
                    namespace,
                )
                return cached

        max_retries = int(
            os.environ.get(
                "GEMINI_MAX_RETRIES",
                "3",
            )
        )

        backoff = float(
            os.environ.get(
                "GEMINI_RETRY_BACKOFF",
                "1.5",
            )
        )

        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                model = cls._get_model()

                response = model.generate_content(prompt)

                raw_text = (
                    getattr(response, "text", None)
                    or ""
                )

                if (
                    not raw_text
                    and hasattr(response, "candidates")
                    and response.candidates
                ):
                    parts = (
                        response.candidates[0]
                        .content.parts
                    )

                    raw_text = "".join(
                        getattr(p, "text", "")
                        for p in parts
                    )

                data = cls._extract_json(raw_text)

                data = cls._validate_fields(
                    data,
                    required_fields,
                )

                if validator:
                    data = validator(data)

                if use_cache:
                    AICache.set(cache_key, data)

                return data

            except Exception as exc:
                last_error = exc

                logger.warning(
                    "Gemini request failed "
                    "(attempt %s/%s) "
                    "namespace=%s: %s",
                    attempt,
                    max_retries,
                    namespace,
                    exc,
                )

                if attempt < max_retries:
                    time.sleep(backoff ** attempt)

        raise AIServiceError(
            f"Gemini failed after "
            f"{max_retries} attempts: "
            f"{last_error}"
        )

    @classmethod
    def run_with_fallback(
        cls,
        ai_callable: Callable[
            [],
            Dict[str, Any],
        ],
        fallback_callable: Callable[
            [],
            T,
        ],
    ) -> T:
        try:
            return ai_callable()  # type: ignore[return-value]

        except AIServiceError as exc:
            logger.info(
                "AI unavailable, using "
                "rule-based fallback: %s",
                exc,
            )

            return fallback_callable()

        except Exception as exc:
            logger.exception(
                "Unexpected AI error, "
                "using fallback: %s",
                exc,
            )

            return fallback_callable()