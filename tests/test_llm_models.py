"""Groq client: model fallback, discovery of accessible models, and clear error kinds (no network)."""
from types import SimpleNamespace

import pytest

from backend.app.core import llm as llm_mod
from backend.app.core.llm import GroqLLM, LLMError


class NotFound(Exception):
    status_code = 404

    def __init__(self, model):
        super().__init__(f"Error code: 404 - {{'error': {{'message': 'The model `{model}` does not exist or you do not have access to it.', 'code': 'model_not_found'}}}}")


def make(allowed: set[str], listed: list[str], status=None):
    calls = []

    def create(model, **kw):
        calls.append(model)
        if status:
            raise status
        if model not in allowed:
            raise NotFound(model)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))])

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
        models=SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id=i) for i in listed])))
    g = GroqLLM.__new__(GroqLLM)
    g._client, g._working, g._discovered = client, None, None
    return g, calls


def test_discovers_a_model_the_key_can_use():
    g, calls = make(allowed={"openai/gpt-oss-20b"}, listed=["whisper-large-v3", "openai/gpt-oss-20b", "llama-guard-4"])
    assert g.chat_json("s", "u") == {"ok": True}
    assert calls[-1] == "openai/gpt-oss-20b" and g._working == "openai/gpt-oss-20b"
    g.chat_json("s", "u")                       # remembered: goes straight to the working model
    assert calls[-1] == "openai/gpt-oss-20b" and calls[-2] == "openai/gpt-oss-20b"


def test_clear_error_when_no_model_is_accessible():
    g, _ = make(allowed=set(), listed=["llama-3.3-70b-versatile"])
    with pytest.raises(LLMError) as ei:
        g.chat_json("s", "u")
    assert ei.value.kind == "model_unavailable" and "GROQ_MODEL" in str(ei.value) and "404" not in str(ei.value)
    assert ei.value.details  # per-model reasons kept for logs


def test_auth_error_is_reported_as_auth():
    class Unauthorized(Exception):
        status_code = 401
    g, _ = make(allowed=set(), listed=[], status=Unauthorized("Invalid API Key"))
    with pytest.raises(LLMError) as ei:
        g.chat_json("s", "u")
    assert ei.value.kind == "auth"
