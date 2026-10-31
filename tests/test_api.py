from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

ROOT = Path(__file__).resolve().parents[1]
RESUME = (ROOT / "sample_data" / "sample_resume.txt").read_text()
JD = (ROOT / "sample_data" / "sample_jd.txt").read_text()

client = TestClient(app)


def make_pdf(text: str) -> bytes:
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(40, y, line[:110])
        y -= 14
        if y < 40:
            c.showPage(); y = 800
    c.save()
    return buf.getvalue()


@pytest.fixture(scope="module")
def analysis():
    r = client.post("/resume/analyze",
                    data={"jd_text": JD, "company": "Amazon", "role": "SDE", "weeks": 4},
                    files={"resume_file": ("resume.pdf", make_pdf(RESUME), "application/pdf")})
    assert r.status_code == 200, r.text
    return r.json()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_analyze_pdf(analysis):
    assert 0 <= analysis["ats"]["score"] <= 100
    missing = [m["skill"] for m in analysis["skills"]["missing"]]
    assert "kubernetes" in missing or "docker" in missing
    assert len(analysis["interview_questions"]) >= 4
    assert len(analysis["coding_questions"]) >= 2
    assert len(analysis["roadmap"]["weeks"]) == 4
    assert "resume_text" not in analysis  # raw resume is never echoed back


def test_analyze_rejects_bad_input():
    assert client.post("/resume/analyze", data={"jd_text": JD}).status_code == 422
    r = client.post("/resume/analyze", data={"jd_text": JD},
                    files={"resume_file": ("x.pdf", b"not a pdf at all", "application/pdf")})
    assert r.status_code == 422


def test_mock_interview_flow(analysis):
    sid = analysis["session_id"]
    r = client.post("/interview/start", json={"session_id": sid, "num_questions": 3})
    assert r.status_code == 200
    iid, total = r.json()["interview_id"], r.json()["total_questions"]
    good = ("In my final-year project I faced a situation where search was slow. My task was to improve it, so I "
            "built a FAISS index, then benchmarked it and finally reduced latency by 40% for 500 users. I learned to measure first.")
    finished, turns = False, 0
    while not finished and turns < 15:
        resp = client.post(f"/interview/{iid}/answer", json={"answer": good}).json()
        finished, turns = resp["finished"], turns + 1
        assert "evaluation" in resp
    assert finished and "report" in resp
    rep = client.get(f"/interview/{iid}/report").json()
    assert 0 <= rep["overall"] <= 10 and rep["questions_answered"] >= total
    assert client.post(f"/interview/{iid}/answer", json={"answer": "x more"}).status_code == 409


def test_weak_answer_triggers_followup(analysis):
    sid = analysis["session_id"]
    iid = client.post("/interview/start", json={"session_id": sid, "num_questions": 3}).json()["interview_id"]
    resp = client.post(f"/interview/{iid}/answer", json={"answer": "I am hardworking."}).json()
    assert resp["kind"] == "followup"


def test_progress_and_adaptation(analysis):
    sid = analysis["session_id"]
    plan = client.get(f"/plan/{sid}").json()
    w1 = plan["weeks"][0]["tasks"]
    assert client.post(f"/progress/{sid}/task", json={"task_id": w1[0]["id"], "done": True}).status_code == 200
    assert client.post(f"/progress/{sid}/task", json={"task_id": "nope", "done": True}).status_code == 404
    client.post(f"/progress/{sid}/coding", json={"title": "LRU Cache", "topics": ["design"], "rating": "failed"})
    changes = client.post(f"/plan/{sid}/adapt").json()["changes"]
    assert changes
    dash = client.get(f"/progress/{sid}").json()
    assert dash["tasks_done"] == 1 and 0 <= dash["readiness"]["score"] <= 100
    plan2 = client.get(f"/plan/{sid}").json()
    ids = [t["id"] for w in plan2["weeks"] for t in w["tasks"]]
    assert len(ids) == len(set(ids))  # ids stay unique after adaptation
    assert next(t for w in plan2["weeks"] for t in w["tasks"] if t["id"] == w1[0]["id"])["done"] is True


def test_delete_session():
    r = client.post("/resume/analyze", data={"jd_text": JD, "resume_text": RESUME, "weeks": 2})
    sid = r.json()["session_id"]
    assert client.delete(f"/resume/{sid}").status_code == 200
    assert client.get(f"/resume/{sid}").status_code == 404
