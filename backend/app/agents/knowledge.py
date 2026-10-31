"""Company/role knowledge base indexed in FAISS (the 'Company / JD context' store from the architecture)."""
from __future__ import annotations

import json
import re
from functools import lru_cache

from ..config import settings
from ..core.embeddings import get_embedder
from ..core.vectorstore import VectorStore


def kb_entry_text(e: dict) -> str:
    return f"{e['company']}. {e['process']} Focus: {'; '.join(e['focus'])}. Themes: {'; '.join(e['themes'])}"


@lru_cache(maxsize=1)
def _load():
    entries = json.loads(settings.KB_PATH.read_text(encoding="utf-8"))
    emb = get_embedder()
    store = VectorStore(emb.dim)
    store.add(emb.embed([kb_entry_text(e) for e in entries]), [{"idx": i} for i in range(len(entries))])
    return entries, store


def find_company(company: str, role: str = "") -> dict:
    """Exact/alias match first, then semantic retrieval from FAISS, then the Generic entry."""
    entries, store = _load()
    name = re.sub(r"[^a-z0-9 ]", " ", (company or "").lower()).strip()
    if name:
        for e in entries:
            names = [e["company"].lower()] + e.get("aliases", [])
            if any(name == n or (len(n) > 3 and n in name) or (len(name) > 3 and name in n) for n in names):
                return {**e, "matched_by": "name", "similarity": 1.0}
        emb = get_embedder()
        hits = store.search(emb.embed([f"{company} {role} hiring interview process"])[0], k=1)
        if hits and hits[0][0] > 0.55:  # only trust semantic match when confident
            return {**entries[hits[0][1]["idx"]], "matched_by": "semantic", "similarity": round(hits[0][0], 3)}
    generic = next(e for e in entries if e["company"] == "Generic")
    return {**generic, "matched_by": "fallback", "similarity": 0.0}
