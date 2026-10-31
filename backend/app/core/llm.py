"""Groq LLM client with JSON mode, model fallback and a graceful 'unavailable' state."""
from __future__ import annotations

import json
import logging
import re
import time

from ..config import settings

log = logging.getLogger("placementpilot.llm")


class LLMError(RuntimeError):
    """kind: no_key | auth | model_unavailable | rate_limit | bad_output | other"""

    def __init__(self, message: str, kind: str = "other", details: list[str] | None = None):
        super().__init__(message)
        self.kind, self.details = kind, details or []


# Preference order when we have to pick a model ourselves from what the key can access.
PREFERRED = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant",
             "qwen/qwen3-32b", "gemma2-9b-it"]
_NOT_CHAT = ("whisper", "guard", "tts", "playai", "orpheus", "distil-whisper", "embed", "compound")


def _classify(e: Exception) -> str:
    msg = str(e).lower()
    code = getattr(e, "status_code", None)
    if code == 401 or "invalid api key" in msg or "invalid_api_key" in msg:
        return "auth"
    if code in (403, 404) or "model_not_found" in msg or "does not exist" in msg or "model_decommissioned" in msg or "decommissioned" in msg:
        return "model_unavailable"
    if code == 429 or "rate limit" in msg or "rate_limit" in msg:
        return "rate_limit"
    return "other"


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class GroqLLM:
    def __init__(self):
        self._client = None
        self._working: str | None = None      # last model that answered successfully
        self._discovered: list[str] | None = None
        if settings.GROQ_API_KEY:
            try:
                from groq import Groq

                self._client = Groq(api_key=settings.GROQ_API_KEY, timeout=45.0, max_retries=1)
            except Exception as e:  # pragma: no cover
                log.warning("Groq SDK init failed: %s", e)

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def mode(self) -> str:
        return "groq" if self.available else "offline"

    def _discover(self) -> list[str]:
        """Ask Groq which chat models THIS key can use (cached). Used only after configured models fail."""
        if self._discovered is None:
            try:
                ids = [m.id for m in self._client.models.list().data]
                ids = [i for i in ids if not any(x in i.lower() for x in _NOT_CHAT)]
                rank = {m: i for i, m in enumerate(PREFERRED)}
                self._discovered = sorted(ids, key=lambda i: (rank.get(i, 99), i))
            except Exception as e:
                log.warning("Could not list Groq models: %s", e)
                self._discovered = []
        return self._discovered

    def _call(self, model: str, system: str, user: str, temperature: float, max_tokens: int, json_mode: bool = True) -> dict:
        kw = {"response_format": {"type": "json_object"}} if json_mode else {}
        resp = self._client.chat.completions.create(
            model=model, temperature=temperature, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system + "\nRespond with a single valid JSON object only."},
                      {"role": "user", "content": user}], **kw)
        return _extract_json(resp.choices[0].message.content or "")

    def chat_json(self, system: str, user: str, temperature: float = 0.4, max_tokens: int = 3500) -> dict:
        if not self.available:
            raise LLMError("GROQ_API_KEY is not configured.", "no_key")
        order = [m for m in (self._working, settings.GROQ_MODEL, settings.GROQ_FALLBACK_MODEL) if m]
        tried: set[str] = set()
        details: list[str] = []
        kinds: list[str] = []
        discovered_once = False
        queue = list(dict.fromkeys(order))
        while queue:
            model = queue.pop(0)
            if model in tried:
                continue
            tried.add(model)
            for attempt in range(2):
                try:
                    out = self._call(model, system, user, temperature, max_tokens)
                    if model != self._working:
                        log.info("Groq model in use: %s", model)
                    self._working = model
                    return out
                except json.JSONDecodeError:
                    kinds.append("bad_output"); details.append(f"{model}: returned invalid JSON")
                    break
                except Exception as e:
                    kind = _classify(e)
                    short = str(e).split("\n")[0][:160]
                    if kind == "other" and "response_format" in str(e).lower() and attempt == 0:
                        try:   # a few models reject JSON mode: retry plain and rely on our JSON extraction
                            out = self._call(model, system, user, temperature, max_tokens, json_mode=False)
                            self._working = model
                            return out
                        except Exception as e2:
                            short = str(e2).split("\n")[0][:160]
                    kinds.append(kind); details.append(f"{model}: {short}")
                    if kind == "auth":
                        raise LLMError("Groq rejected your API key. Check GROQ_API_KEY in .env.", "auth", details)
                    if kind == "rate_limit" and attempt == 0:
                        time.sleep(2.0); continue
                    break
            # all configured models failed for access reasons -> look at what the key can really use
            if not queue and not discovered_once and any(k == "model_unavailable" for k in kinds):
                discovered_once = True
                queue = [m for m in self._discover() if m not in tried][:3]
        if "model_unavailable" in kinds and "rate_limit" not in kinds:
            raise LLMError("Groq has no usable model for this API key (model not found or no access). "
                           "Set GROQ_MODEL in .env to a model listed in your Groq console.", "model_unavailable", details)
        if "rate_limit" in kinds:
            raise LLMError("Groq rate limit reached. Wait a minute and run the analysis again.", "rate_limit", details)
        raise LLMError("Groq did not return a usable answer.", kinds[-1] if kinds else "other", details)


_llm: GroqLLM | None = None


def get_llm() -> GroqLLM:
    global _llm
    if _llm is None:
        _llm = GroqLLM()
    return _llm
