"""Skill taxonomy loader + matcher (used for ATS keyword coverage and skill-gap detection)."""
from __future__ import annotations

import json
import re
from collections import Counter
from functools import lru_cache

from ..config import settings

# Aliases that are too ambiguous as bare words in prose.
_BLACKLIST = {"ts", "dl", "rest"}


@lru_cache(maxsize=1)
def load_taxonomy() -> dict:
    """Returns {canonical: {"category": str, "aliases": [..]}}"""
    raw = json.loads(settings.SKILLS_PATH.read_text(encoding="utf-8"))
    out = {}
    for category, skills in raw.items():
        for canonical, aliases in skills.items():
            out[canonical] = {
                "category": category,
                "aliases": sorted({a.lower() for a in aliases + [canonical] if a.lower() not in _BLACKLIST}),
            }
    return out


@lru_cache(maxsize=1)
def _compiled() -> dict:
    compiled = {}
    for canonical, info in load_taxonomy().items():
        parts = [re.escape(a) for a in sorted(info["aliases"], key=len, reverse=True)]
        compiled[canonical] = re.compile(r"(?<![\w+#.])(?:" + "|".join(parts) + r")(?![\w+#])", re.I)
    return compiled


def extract_skills(text: str) -> Counter:
    """Count skill mentions (canonical names) in free text."""
    counts: Counter = Counter()
    for canonical, rx in _compiled().items():
        n = len(rx.findall(text))
        if n:
            counts[canonical] = n
    return counts


def category_of(skill: str) -> str:
    return load_taxonomy().get(skill, {}).get("category", "other")
