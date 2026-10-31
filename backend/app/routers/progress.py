"""/progress : task tracking, scores and the readiness dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core import db
from ..schemas import CodingLog, ScoreIn, TaskUpdate


def readiness(ats: float, task_completion: float | None, hr_overall_10: float | None, coding_solved: int, coding_total: int) -> dict:
    """Weighted readiness (0-100) over whatever components exist so far."""
    parts = {"resume_ats": (ats, 0.25)}
    if task_completion is not None:
        parts["roadmap_completion"] = (task_completion, 0.35)
    if hr_overall_10 is not None:
        parts["mock_hr"] = (hr_overall_10 * 10, 0.25)
    if coding_total:
        parts["coding_practice"] = (coding_solved / coding_total * 100, 0.15)
    wsum = sum(w for _, w in parts.values())
    score = sum(v * w for v, w in parts.values()) / wsum
    return {"score": round(score, 1), "components": {k: round(v, 1) for k, (v, _) in parts.items()}}


def create_router(rate_limit) -> APIRouter:
    r = APIRouter(prefix="/progress", tags=["progress"], dependencies=[Depends(rate_limit)])

    def _session(sid: str) -> dict:
        s = db.get_session(sid)
        if not s:
            raise HTTPException(404, "Session not found")
        return s

    @r.post("/{session_id}/task")
    def set_task(session_id: str, body: TaskUpdate):
        s = _session(session_id)
        valid = {t["id"] for w in s["roadmap"]["weeks"] for t in w["tasks"]}
        if body.task_id not in valid:
            raise HTTPException(404, "Unknown task id")
        db.set_task(session_id, body.task_id, body.done)
        return {"ok": True}

    @r.post("/{session_id}/coding")
    def log_coding(session_id: str, body: CodingLog):
        _session(session_id)
        solved = body.rating in ("easy", "ok", "hard")
        db.add_score(session_id, "coding", body.title, 1.0 if solved else 0.0,
                     {"topics": body.topics, "rating": body.rating, "minutes": body.minutes})
        return {"ok": True}

    @r.post("/{session_id}/score")
    def add_score(session_id: str, body: ScoreIn):
        _session(session_id)
        db.add_score(session_id, body.kind, body.ref, body.score)
        return {"ok": True}

    @r.get("/{session_id}")
    def dashboard(session_id: str):
        s = _session(session_id)
        done = db.get_task_state(session_id)
        tasks = [t for w in s["roadmap"]["weeks"] for t in w["tasks"]]
        completion = (sum(1 for t in tasks if done.get(t["id"])) / len(tasks) * 100) if tasks else 0.0
        hr = db.get_scores(session_id, "mock_hr")
        coding = db.get_scores(session_id, "coding")
        solved = sum(1 for c in coding if c["score"] >= 1)
        hr_last = hr[-1]["score"] / 10 if hr else None
        weekly = []
        for w in s["roadmap"]["weeks"]:
            n = len(w["tasks"])
            weekly.append({"week": w["week"], "done": sum(1 for t in w["tasks"] if done.get(t["id"])), "total": n})
        rd = readiness(s["ats"]["score"], completion if done else None, hr_last, solved, len(coding))
        return {
            "readiness": rd, "ats_score": s["ats"]["score"],
            "task_completion": round(completion, 1), "tasks_done": sum(done.values()), "tasks_total": len(tasks),
            "mock_hr_history": [{"ts": h["ts"], "overall_10": round(h["score"] / 10, 1), "dims": h["meta"].get("dims", {})} for h in hr],
            "coding": {"attempted": len(coding), "solved": solved,
                       "log": [{"title": c["ref"], **c["meta"]} for c in coding][-20:]},
            "weekly": weekly,
        }

    return r
