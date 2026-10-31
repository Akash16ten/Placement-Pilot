"""/plan : weekly roadmap + adaptation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..agents.adapt import adapt_roadmap, current_week_index, week_completion
from ..core import db


def create_router(rate_limit) -> APIRouter:
    r = APIRouter(prefix="/plan", tags=["plan"], dependencies=[Depends(rate_limit)])

    def _session(session_id: str) -> dict:
        s = db.get_session(session_id)
        if not s:
            raise HTTPException(404, "Session not found")
        return s

    @r.get("/{session_id}")
    def get_plan(session_id: str):
        s = _session(session_id)
        done = db.get_task_state(session_id)
        rm = s["roadmap"]
        weeks = [{**w, "tasks": [{**t, "done": done.get(t["id"], False)} for t in w["tasks"]],
                  "completion": round(week_completion(w, done) * 100)} for w in rm["weeks"]]
        return {"summary": rm.get("summary", ""), "current_week": rm["weeks"][current_week_index(rm, done)]["week"],
                "weeks": weeks, "adaptations": s.get("adaptations", [])}

    @r.post("/{session_id}/adapt")
    def adapt(session_id: str):
        s = _session(session_id)
        done = db.get_task_state(session_id)
        hr = db.get_scores(session_id, "mock_hr")
        dims = hr[-1]["meta"].get("dims") if hr else None
        coding = [{**x["meta"]} for x in db.get_scores(session_id, "coding")]
        new_rm, log = adapt_roadmap(s["roadmap"], done, dims, coding)
        s["roadmap"] = new_rm
        s["adaptations"] = (s.get("adaptations", []) + log)[-30:]
        db.save_session(s, session_id)
        return {"changes": log}

    return r
