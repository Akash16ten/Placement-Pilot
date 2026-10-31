"""/resume : upload + full LangGraph analysis (ATS, skill gaps, questions, roadmap)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..agents.graph import run_analysis
from ..config import settings
from ..core import db
from ..core.llm import get_llm
from ..core.pdf_parser import ResumeParseError, extract_text_from_pdf


def create_router(rate_limit) -> APIRouter:
    r = APIRouter(prefix="/resume", tags=["resume"], dependencies=[Depends(rate_limit)])

    @r.post("/analyze")
    def analyze(
        jd_text: str = Form(..., min_length=30, max_length=15000),
        company: str = Form("", max_length=100),
        role: str = Form("Software Engineer", max_length=100),
        weeks: int = Form(6, ge=2, le=12),
        resume_text: str = Form("", max_length=30000),
        resume_file: UploadFile | None = File(None),
    ):
        """Upload a PDF resume (or paste text) + job description + company -> complete preparation plan."""
        if resume_file is not None and resume_file.filename:
            data = resume_file.file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
            if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
                raise HTTPException(413, f"Resume too large (max {settings.MAX_UPLOAD_MB} MB).")
            try:
                text = extract_text_from_pdf(data)
            except ResumeParseError as e:
                raise HTTPException(422, str(e))
        elif len(resume_text.strip()) >= 80:
            text = resume_text.strip()
        else:
            raise HTTPException(422, "Provide a PDF resume or paste at least ~80 characters of resume text.")

        sid = db.new_id()
        state = run_analysis(text, jd_text.strip(), company.strip(), role.strip(), weeks, sid)
        result = {
            "session_id": sid,
            "company": company.strip(), "role": role.strip(), "weeks": weeks,
            "resume_text": text,
            "parsed_resume": {k: v for k, v in state["parsed_resume"].items() if k != "sections"},
            "ats": state["ats"], "skills": state["skills"],
            "context": state["context"],
            "interview_questions": state["interview_questions"], "coding_questions": state["coding_questions"],
            "roadmap": state["roadmap"],
            "generation_mode": state["generation_mode"],
            "warnings": state.get("warnings", []), "trace": state.get("trace", []),
            "jd_text": jd_text.strip(),
        }
        db.save_session(result, sid)
        return _public(result)

    @r.get("/{session_id}")
    def get_analysis(session_id: str):
        s = db.get_session(session_id)
        if not s:
            raise HTTPException(404, "Session not found")
        return _public(s)

    @r.delete("/{session_id}")
    def delete_data(session_id: str):
        """Privacy: erase the resume and all derived data for this session."""
        if not db.delete_session(session_id):
            raise HTTPException(404, "Session not found")
        for ext in ("faiss", "npy", "json"):
            p = settings.DATA_DIR / "faiss" / f"resume_{session_id}.{ext}"
            if p.exists():
                p.unlink()
        return {"deleted": True}

    return r


def _public(s: dict) -> dict:
    """Never echo the raw resume text back in API responses."""
    out = {k: v for k, v in s.items() if k not in ("resume_text", "jd_text")}
    out["llm_mode"] = get_llm().mode
    return out
