"""Thin HTTP client for the PlacementPilot backend."""
import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 180  # LLM-backed analysis can take a while


class ApiError(Exception):
    pass


def _handle(r: requests.Response):
    if r.ok:
        return r.json()
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text
    raise ApiError(f"{r.status_code}: {detail}")


def _req(method: str, path: str, **kw):
    try:
        return _handle(requests.request(method, f"{API_URL}{path}", timeout=TIMEOUT, **kw))
    except requests.ConnectionError:
        raise ApiError(f"Cannot reach the backend at {API_URL}. Start it with ./run_backend.sh")


def health():
    return _req("GET", "/health")


def analyze(jd_text, company, role, weeks, resume_file=None, resume_text=""):
    files = {"resume_file": (resume_file.name, resume_file.getvalue(), "application/pdf")} if resume_file else None
    data = {"jd_text": jd_text, "company": company, "role": role, "weeks": weeks, "resume_text": resume_text}
    return _req("POST", "/resume/analyze", data=data, files=files)


def get_analysis(session_id):
    """Existing backend endpoint (GET /resume/{id}); used to restore a session after a browser reload."""
    return _req("GET", f"/resume/{session_id}")


def start_interview(session_id, n):
    return _req("POST", "/interview/start", json={"session_id": session_id, "num_questions": n})


def answer(interview_id, text):
    return _req("POST", f"/interview/{interview_id}/answer", json={"answer": text})


def plan(session_id):
    return _req("GET", f"/plan/{session_id}")


def adapt(session_id):
    return _req("POST", f"/plan/{session_id}/adapt")


def set_task(session_id, task_id, done):
    return _req("POST", f"/progress/{session_id}/task", json={"task_id": task_id, "done": done})


def log_coding(session_id, title, topics, rating):
    return _req("POST", f"/progress/{session_id}/coding", json={"title": title, "topics": topics, "rating": rating})


def dashboard(session_id):
    return _req("GET", f"/progress/{session_id}")


def delete_session(session_id):
    return _req("DELETE", f"/resume/{session_id}")
