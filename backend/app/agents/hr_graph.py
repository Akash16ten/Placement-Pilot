"""Mock HR interview agent as a LangGraph state machine.

One graph invocation == one candidate answer:
    evaluate_answer -> (decide) -> ask_followup | next_question | finish_interview
"""
from __future__ import annotations

from functools import lru_cache
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..core.llm import LLMError, get_llm
from . import offline

DIMS = ("clarity", "structure", "impact", "relevance")
MAX_FOLLOWUPS_PER_Q = 1

BASE_HR_QUESTIONS = [
    "Tell me about yourself and what drew you to {role}.",
    "Walk me through your strongest project. What was your role, what was hard, and what was the outcome?",
    "Tell me about a time you faced a conflict or disagreement in a team and how you handled it.",
    "Describe a situation where you had to learn a new technology quickly. How did you approach it?",
    "Why do you want to join {company}, and why should we hire you over other candidates?",
    "What is your biggest weakness, and what are you doing about it?",
    "Tell me about a failure or mistake and what you learned from it.",
    "Where do you see yourself in five years?",
]


class HRState(TypedDict, total=False):
    company: str
    role: str
    questions: list[str]
    idx: int
    followups_used: int
    pending_question: str
    pending_kind: str          # main | followup
    last_answer: str
    history: list[dict]
    last_eval: dict
    decision: str
    finished: bool
    report: dict


def build_question_list(company: str, role: str, missing: list[str], n: int, llm_questions: list[str] | None = None) -> list[str]:
    qs = [q.format(company=company or "our company", role=role or "this role") for q in BASE_HR_QUESTIONS]
    if missing:
        qs.insert(3, f"The role needs {missing[0]}, which isn't prominent on your resume. How would you get up to speed on it in your first month?")
    if llm_questions:
        qs = qs[:1] + llm_questions + qs[1:]
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q); out.append(q)
    return out[: max(3, min(n, 10))]


def generate_hr_questions(company: str, role: str, missing: list[str], projects: list[str], n: int) -> list[str]:
    llm = get_llm()
    extra: list[str] = []
    if llm.available:
        try:
            data = llm.chat_json(
                "You are a warm but rigorous HR interviewer at a technology company.",
                f"Company: {company}. Role: {role}. Candidate projects: {projects[:4]}. Skill gaps: {missing[:4]}.\n"
                'Write 3 HR/behavioral questions tailored to this candidate (not generic). JSON: {"questions":[str,str,str]}',
                temperature=0.6, max_tokens=500)
            extra = [q for q in data.get("questions", []) if isinstance(q, str) and q.strip()][:3]
        except LLMError:
            pass
    return build_question_list(company, role, missing, n, extra)


# ------------------------------------------------------------------- nodes
def evaluate_answer(state: HRState) -> dict:
    answer = state["last_answer"]
    question = state["pending_question"]
    llm = get_llm()
    ev = None
    if llm.available:
        try:
            data = llm.chat_json(
                "You are a strict but fair HR interviewer scoring a fresher's answer. Score each 0-10 as integers.",
                f"""Company: {state.get('company')}  Role: {state.get('role')}
Question: {question}
Candidate answer: {answer}

Score: clarity (easy to follow), structure (STAR/logical flow), impact (specific actions + measurable results), relevance (answers the question, fits the role).
Give 1-3 strengths, 1-3 concrete improvements, a better_answer_tip (one sentence), and ONE follow-up question only if the answer was vague/incomplete (else empty string).
JSON: {{"clarity":int,"structure":int,"impact":int,"relevance":int,"strengths":[str],"improvements":[str],"better_answer_tip":str,"followup":str}}""",
                temperature=0.2, max_tokens=700)
            vals = {d: max(0, min(10, int(float(data.get(d, 5))))) for d in DIMS}
            ev = {**vals, "overall": round(sum(vals.values()) / 4, 1),
                  "strengths": [s for s in data.get("strengths", []) if isinstance(s, str)][:3],
                  "improvements": [s for s in data.get("improvements", []) if isinstance(s, str)][:3],
                  "better_answer_tip": data.get("better_answer_tip", ""),
                  "followup": (data.get("followup") or "").strip()}
        except (LLMError, ValueError, TypeError):
            ev = None
    if ev is None:
        ev = offline.offline_evaluate(answer)
        ev.setdefault("better_answer_tip", "")
    hist = list(state.get("history", []))
    hist.append({"question": question, "kind": state.get("pending_kind", "main"), "answer": answer, "evaluation": ev})
    return {"history": hist, "last_eval": ev}


def decide(state: HRState) -> str:
    ev = state["last_eval"]
    wants_followup = bool(ev.get("followup")) and (ev.get("overall", 10) < 7.0)
    if wants_followup and state.get("followups_used", 0) < MAX_FOLLOWUPS_PER_Q:
        return "ask_followup"
    if state["idx"] + 1 < len(state["questions"]):
        return "next_question"
    return "finish_interview"


def ask_followup(state: HRState) -> dict:
    return {"pending_question": state["last_eval"]["followup"], "pending_kind": "followup",
            "followups_used": state.get("followups_used", 0) + 1, "decision": "followup", "finished": False}


def next_question(state: HRState) -> dict:
    i = state["idx"] + 1
    return {"idx": i, "pending_question": state["questions"][i], "pending_kind": "main",
            "followups_used": 0, "decision": "next", "finished": False}


def finish_interview(state: HRState) -> dict:
    hist = state["history"]
    n = len(hist)
    avg = {d: round(sum(h["evaluation"][d] for h in hist) / n, 1) for d in DIMS} if n else {d: 0 for d in DIMS}
    overall = round(sum(avg.values()) / 4, 1) if n else 0.0
    strengths, improvements = [], []
    for h in hist:
        strengths += h["evaluation"].get("strengths", [])
        improvements += h["evaluation"].get("improvements", [])
    dedup = lambda xs: list(dict.fromkeys(xs))[:5]
    weakest = min(avg, key=avg.get) if n else None
    report = {
        "overall": overall, "dimension_averages": avg, "questions_answered": n,
        "weakest_dimension": weakest, "top_strengths": dedup(strengths), "top_improvements": dedup(improvements),
        "verdict": ("Interview-ready" if overall >= 7.5 else "Getting there: keep practising" if overall >= 5.5 else "Needs focused practice"),
        "per_question": [{"question": h["question"], "kind": h["kind"], "score": h["evaluation"]["overall"],
                          "tip": h["evaluation"].get("better_answer_tip", "")} for h in hist],
    }
    return {"report": report, "finished": True, "decision": "finish", "pending_question": ""}


@lru_cache(maxsize=1)
def build_hr_graph():
    g = StateGraph(HRState)
    g.add_node("evaluate_answer", evaluate_answer)
    g.add_node("ask_followup", ask_followup)
    g.add_node("next_question", next_question)
    g.add_node("finish_interview", finish_interview)
    g.add_edge(START, "evaluate_answer")
    g.add_conditional_edges("evaluate_answer", decide, {
        "ask_followup": "ask_followup", "next_question": "next_question", "finish_interview": "finish_interview"})
    for n in ("ask_followup", "next_question", "finish_interview"):
        g.add_edge(n, END)
    return g.compile()


def step(state: dict, answer: str) -> dict:
    """Run one turn. `state` is the persisted HRState dict; returns the updated one."""
    return build_hr_graph().invoke({**state, "last_answer": answer})
