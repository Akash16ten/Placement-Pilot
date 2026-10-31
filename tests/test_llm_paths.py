"""Exercise the Groq code paths with a fake LLM (no network needed)."""
from pathlib import Path

from backend.app.agents import graph, hr_graph, nodes
from backend.app.core.llm import _extract_json

ROOT = Path(__file__).resolve().parents[1]
RESUME = (ROOT / "sample_data" / "sample_resume.txt").read_text()
JD = (ROOT / "sample_data" / "sample_jd.txt").read_text()


class FakeLLM:
    available = True
    mode = "groq"

    def chat_json(self, system, user, **kw):
        if "interview_questions" in user:
            return {"interview_questions": [{"question": f"Q{i}?", "category": "technical", "difficulty": "Medium"} for i in range(8)],
                    "coding_questions": [{"title": "T1", "statement": "S1", "topics": "arrays"}, {"title": "T2", "statement": "S2"}]}
        if "roadmap" in user:  # only 2 of 4 weeks returned + messy task shapes -> must be padded/normalised
            return {"summary": "plan", "weeks": [{"week": 1, "theme": "A", "tasks": ["just a string", {"title": "x", "est_hours": "bad"}]},
                                                  {"week": 2, "theme": "B", "tasks": [{"title": "y"}]}]}
        if "Score:" in user:
            return {"clarity": 9, "structure": 8, "impact": 7, "relevance": 8, "strengths": ["good"], "improvements": [], "followup": ""}
        return {"questions": ["Custom HR q1?", "Custom HR q2?", "Custom HR q3?"]}


def test_pipeline_with_llm(monkeypatch):
    monkeypatch.setattr(nodes, "get_llm", lambda: FakeLLM())
    s = graph.run_analysis(RESUME, JD, "Amazon", "SDE", 4, "llmtest")
    assert s["generation_mode"] == "groq"
    assert [q["question"] for q in s["interview_questions"]][:2] == ["Q0?", "Q1?"]
    assert s["coding_questions"][0]["topics"] == ["arrays"]
    weeks = s["roadmap"]["weeks"]
    assert len(weeks) == 4 and all(t["id"] for w in weeks for t in w["tasks"])
    assert weeks[0]["tasks"][1]["est_hours"] == 2.0


def test_hr_agent_with_llm(monkeypatch):
    monkeypatch.setattr(hr_graph, "get_llm", lambda: FakeLLM())
    qs = hr_graph.generate_hr_questions("Amazon", "SDE", ["aws"], [], 5)
    assert "Custom HR q1?" in qs
    st = {"company": "Amazon", "role": "SDE", "questions": ["a", "b"], "idx": 0, "followups_used": 0,
          "pending_question": "a", "pending_kind": "main", "history": []}
    st = hr_graph.step(st, "some answer")
    assert st["last_eval"]["overall"] == 8.0 and st["pending_question"] == "b"
    st = hr_graph.step(st, "another")
    assert st["finished"] and st["report"]["overall"] == 8.0


def test_json_extraction():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json('Sure! Here: {"a": {"b": 2}} done') == {"a": {"b": 2}}
