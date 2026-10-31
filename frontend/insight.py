"""Pure helpers that derive display metadata from real backend data (no I/O, no invented numbers)."""
from __future__ import annotations

CAT_LABEL = {"languages": "Languages", "web": "Web & APIs", "data_ml": "Data & AI", "cloud_devops": "Cloud & DevOps",
             "databases": "Databases", "cs_fundamentals": "CS fundamentals", "practices_soft": "Practices & soft skills", "other": "Other"}


def gap_priorities(skills: dict) -> list[dict]:
    """Missing skills are already sorted by backend (JD mentions desc). Priority rule, shown to the user:
    High = mentioned 2+ times in the JD or among the top 3 gaps, Medium = next 3, Low = the rest. Weak-evidence skills are 'Reinforce'."""
    out = []
    for i, m in enumerate(skills["missing"]):
        pr = "high" if (m["jd_mentions"] >= 2 or i < 3) else "med" if i < 6 else "low"
        out.append({**m, "priority": pr, "state": "missing"})
    for m in skills["weak"]:
        out.append({**m, "priority": "reinforce", "state": "weak"})
    return out


def priority_of_skill(skill: str, skills: dict) -> str | None:
    for g in gap_priorities(skills):
        if g["skill"] == (skill or "").lower():
            return g["priority"]
    return None


def tasks_by_skill(plan: dict | None) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for w in (plan or {}).get("weeks", []):
        for t in w["tasks"]:
            out.setdefault((t.get("skill") or "").lower(), []).append({**t, "week": w["week"]})
    return out


def by_category(skills: dict) -> dict[str, dict]:
    cats: dict[str, dict] = {}
    for s in skills["matched"]:
        cats.setdefault(_cat(s, skills), {"matched": [], "weak": [], "missing": []})["matched"].append(s)
    for m in skills["weak"]:
        cats.setdefault(m["category"], {"matched": [], "weak": [], "missing": []})["weak"].append(m["skill"])
    for m in skills["missing"]:
        cats.setdefault(m["category"], {"matched": [], "weak": [], "missing": []})["missing"].append(m["skill"])
    return cats


_MATCHED_CAT: dict[str, str] = {}


def _cat(skill: str, skills: dict) -> str:
    # backend returns category only for gaps; classify matched skills with the same taxonomy file knowledge
    return _MATCHED_CAT.get(skill) or _load_cat().get(skill, "other")


def _load_cat() -> dict:
    if not _MATCHED_CAT:
        import json
        from pathlib import Path
        p = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "skills.json"
        try:
            for cat, items in json.loads(p.read_text(encoding="utf-8")).items():
                for name in items:
                    _MATCHED_CAT[name] = cat
        except OSError:
            pass
    return _MATCHED_CAT
