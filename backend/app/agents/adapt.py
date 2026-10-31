"""Adaptive roadmap: carries over unfinished work and adds reinforcement tasks from real results.

Deterministic on purpose, so every change is explainable to the student ('adaptations' log).
"""
from __future__ import annotations

import copy

MAX_HOURS_PER_WEEK = 14


def week_completion(week: dict, done: dict[str, bool]) -> float:
    tasks = week["tasks"]
    return sum(1 for t in tasks if done.get(t["id"])) / len(tasks) if tasks else 1.0


def current_week_index(roadmap: dict, done: dict[str, bool]) -> int:
    for i, w in enumerate(roadmap["weeks"]):
        if week_completion(w, done) < 1.0:
            return i
    return len(roadmap["weeks"]) - 1


def adapt_roadmap(roadmap: dict, done: dict[str, bool], hr_dim_avgs: dict | None, coding_log: list[dict]) -> tuple[dict, list[str]]:
    rm = copy.deepcopy(roadmap)
    log: list[str] = []
    weeks = rm["weeks"]
    cur = current_week_index(rm, done)

    # 1) carry over unfinished tasks from earlier weeks into the current week
    for w in weeks[:cur]:
        left = [t for t in w["tasks"] if not done.get(t["id"])]
        if left:
            w["tasks"] = [t for t in w["tasks"] if done.get(t["id"])]
            for t in left:
                t["title"] = t["title"] if t["title"].startswith("[Carried over]") else "[Carried over] " + t["title"]
                weeks[cur]["tasks"].append(t)
            log.append(f"Moved {len(left)} unfinished task(s) from week {w['week']} to week {weeks[cur]['week']}.")

    # 2) mock-interview feedback -> reinforcement tasks
    fixes = {
        "structure": ("Rewrite 3 of your interview answers using STAR and record yourself answering them", "interview"),
        "impact": ("Add a measurable result to each project story (numbers, %, time saved) and rehearse them", "interview"),
        "clarity": ("Practise 2-minute answers: state the point first, then support it; cut filler words", "interview"),
        "relevance": ("Re-read the job description and map each answer to one required skill or value", "interview"),
    }
    if hr_dim_avgs:
        for dim, (title, typ) in fixes.items():
            if hr_dim_avgs.get(dim, 10) < 6.0:
                target = weeks[min(cur, len(weeks) - 1)]
                if not any(title in t["title"] for t in target["tasks"]):
                    target["tasks"].append({"title": title, "type": typ, "skill": "communication", "est_hours": 1.5, "resource": "", "adaptive": True})
                    log.append(f"Mock HR '{dim}' averaged {hr_dim_avgs[dim]}/10, so added a reinforcement task to week {target['week']}.")

    # 3) coding struggles -> repeat the topic
    struggled: dict[str, int] = {}
    for c in coding_log:
        if c.get("rating") in ("hard", "failed"):
            for t in c.get("topics", []):
                struggled[t] = struggled.get(t, 0) + 1
    for topic, n in sorted(struggled.items(), key=lambda x: -x[1])[:2]:
        target = weeks[min(cur + 1, len(weeks) - 1)]
        title = f"Revisit {topic}: re-solve the problems you struggled with, then 3 new ones without hints"
        if not any(title == t["title"] for t in target["tasks"]):
            target["tasks"].append({"title": title, "type": "practice", "skill": topic, "est_hours": 2, "resource": "", "adaptive": True})
            log.append(f"You found '{topic}' hard {n} time(s), so scheduled a revisit in week {target['week']}.")

    # 4) workload guard: spill extra tasks to following week
    for i, w in enumerate(weeks[:-1]):
        while sum(t.get("est_hours", 2) for t in w["tasks"]) > MAX_HOURS_PER_WEEK and len(w["tasks"]) > 3:
            movable = [t for t in w["tasks"] if not done.get(t["id"])]
            if not movable:
                break
            t = movable[-1]
            w["tasks"].remove(t)
            weeks[i + 1]["tasks"].append(t)
            log.append(f"Week {w['week']} was overloaded, so moved '{t['title'][:40]}...' to week {weeks[i + 1]['week']}.")

    # re-id: done-state must survive, so keep existing ids, only give new ones to tasks without an id
    used = {t["id"] for w in weeks for t in w["tasks"] if t.get("id")}
    for w in weeks:
        for t in w["tasks"]:
            if not t.get("id"):
                k = 1
                while f"w{w['week']}-a{k}" in used:
                    k += 1
                t["id"] = f"w{w['week']}-a{k}"
                used.add(t["id"])
    if not log:
        log.append("No changes needed: you are on track.")
    return rm, log
