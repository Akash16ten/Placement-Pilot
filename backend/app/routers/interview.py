"""/interview : mock HR interview (LangGraph agent) + question bank access."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..agents import hr_graph
from ..core import db
from ..schemas import InterviewAnswerRequest, InterviewStartRequest


def create_router(rate_limit) -> APIRouter:
    r = APIRouter(prefix="/interview", tags=["interview"], dependencies=[Depends(rate_limit)])

    @r.get("/questions/{session_id}")
    def questions(session_id: str):
        s = db.get_session(session_id)
        if not s:
            raise HTTPException(404, "Session not found")
        return {"interview_questions": s["interview_questions"], "coding_questions": s["coding_questions"]}

    @r.post("/start")
    def start(req: InterviewStartRequest):
        s = db.get_session(req.session_id)
        if not s:
            raise HTTPException(404, "Session not found")
        missing = [m["skill"] for m in s["skills"]["missing"]]
        qs = hr_graph.generate_hr_questions(s["company"], s["role"], missing, s["parsed_resume"].get("projects", []), req.num_questions)
        iid = db.new_id()
        state = {"company": s["company"], "role": s["role"], "questions": qs, "idx": 0, "followups_used": 0,
                 "pending_question": qs[0], "pending_kind": "main", "history": [], "finished": False}
        db.save_interview(iid, req.session_id, state)
        return {"interview_id": iid, "total_questions": len(qs), "question_number": 1, "question": qs[0], "kind": "main"}

    @r.post("/{interview_id}/answer")
    def answer(interview_id: str, req: InterviewAnswerRequest):
        row = db.get_interview(interview_id)
        if not row:
            raise HTTPException(404, "Interview not found")
        session_id, state = row
        if state.get("finished"):
            raise HTTPException(409, "Interview already finished. Fetch the report.")
        if len(req.answer.strip()) < 2:
            raise HTTPException(422, "Answer is empty.")
        new_state = hr_graph.step(state, req.answer.strip())
        db.save_interview(interview_id, session_id, new_state)
        resp = {"evaluation": new_state["last_eval"], "finished": new_state["finished"],
                "total_questions": len(new_state["questions"])}
        if new_state["finished"]:
            rep = new_state["report"]
            db.add_score(session_id, "mock_hr", interview_id, rep["overall"] * 10, {"dims": rep["dimension_averages"]})
            resp["report"] = rep
        else:
            resp.update({"question": new_state["pending_question"], "kind": new_state["pending_kind"],
                         "question_number": new_state["idx"] + 1})
        return resp

    @r.get("/{interview_id}/report")
    def report(interview_id: str):
        row = db.get_interview(interview_id)
        if not row:
            raise HTTPException(404, "Interview not found")
        _, state = row
        if not state.get("finished"):
            raise HTTPException(409, "Interview not finished yet.")
        return {**state["report"], "transcript": state["history"]}

    return r
