"""LangGraph analysis pipeline: resume -> ATS -> skill gaps -> retrieval -> questions -> roadmap."""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import PipelineState


@lru_cache(maxsize=1)
def build_pipeline():
    g = StateGraph(PipelineState)
    g.add_node("parse_resume", nodes.parse_resume_node)
    g.add_node("ats_score", nodes.ats_node)
    g.add_node("skill_gap", nodes.skill_gap_node)
    g.add_node("retrieve_context", nodes.retrieve_context_node)
    g.add_node("generate_questions", nodes.questions_node)
    g.add_node("build_roadmap", nodes.roadmap_node)
    g.add_edge(START, "parse_resume")
    g.add_edge("parse_resume", "ats_score")
    g.add_edge("ats_score", "skill_gap")
    g.add_edge("skill_gap", "retrieve_context")
    g.add_edge("retrieve_context", "generate_questions")
    g.add_edge("generate_questions", "build_roadmap")
    g.add_edge("build_roadmap", END)
    return g.compile()


def run_analysis(resume_text: str, jd_text: str, company: str, role: str, weeks: int, session_id: str) -> dict:
    return build_pipeline().invoke({
        "resume_text": resume_text, "jd_text": jd_text, "company": company, "role": role,
        "weeks": weeks, "session_id": session_id, "warnings": [], "trace": [],
    })
