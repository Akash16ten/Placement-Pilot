"""LangGraph nodes for the analysis pipeline:
parse_resume -> ats_and_embeddings -> skill_gap -> retrieve_context -> generate_questions -> build_roadmap
"""
from __future__ import annotations

import logging
import re

import numpy as np

from ..config import settings
from ..core.embeddings import get_embedder, is_semantic
from ..core.llm import LLMError, get_llm
from ..core.pdf_parser import parse_resume
from ..core.skills import category_of, extract_skills
from ..core.vectorstore import VectorStore
from . import offline
from .knowledge import find_company
from .state import PipelineState

log = logging.getLogger("placementpilot.nodes")


# --------------------------------------------------------------------- helpers
def chunk_text(text: str, min_words: int = 4, max_words: int = 70) -> list[str]:
    chunks: list[str] = []
    for raw in re.split(r"\n+", text):
        line = re.sub(r"^[•\-*▪●\u2022\d.)\s]+", "", raw.strip())
        if not line:
            continue
        words = line.split()
        if len(words) <= max_words:
            if len(words) >= min_words:
                chunks.append(line)
        else:
            for i in range(0, len(words), max_words):
                piece = " ".join(words[i : i + max_words])
                if len(piece.split()) >= min_words:
                    chunks.append(piece)
    return chunks


def _calibrate(avg_sim: float, semantic: bool) -> float:
    lo, hi = (0.15, 0.65) if semantic else (0.03, 0.30)
    return float(np.clip((avg_sim - lo) / (hi - lo), 0, 1)) * 100


# ----------------------------------------------------------------------- nodes
def parse_resume_node(state: PipelineState) -> dict:
    parsed = parse_resume(state["resume_text"])
    return {"parsed_resume": parsed, "trace": [f"Parsed resume: {len(parsed['skills'])} skills, {len(parsed['sections_found'])} sections"]}


def ats_node(state: PipelineState) -> dict:
    """Embeds resume + JD chunks, stores resume vectors in FAISS and computes the ATS score."""
    emb = get_embedder()
    parsed, jd = state["parsed_resume"], state["jd_text"]
    resume_chunks = chunk_text(state["resume_text"]) or [state["resume_text"][:500]]
    jd_chunks = chunk_text(jd) or [jd[:500]]

    rv, jv = emb.embed(resume_chunks), emb.embed(jd_chunks)
    store = VectorStore(emb.dim)
    store.add(rv, [{"text": c} for c in resume_chunks])
    try:  # persist 'Resume vectors' (Persistence layer in the architecture)
        store.save(settings.DATA_DIR / "faiss", f"resume_{state.get('session_id', 'tmp')}")
    except Exception as e:  # persistence is best-effort
        log.warning("Could not persist FAISS index: %s", e)

    sims = store.max_similarity(jv)
    semantic = _calibrate(float(sims.mean()), is_semantic(emb))

    # keyword/skill coverage weighted by how often the JD mentions the skill
    jd_skills = extract_skills(jd)
    resume_skills = extract_skills(state["resume_text"])
    total_w = sum(1 + min(c, 3) * 0.5 for c in jd_skills.values())
    got_w = sum(1 + min(c, 3) * 0.5 for s, c in jd_skills.items() if s in resume_skills)
    keyword = (got_w / total_w * 100) if total_w else None

    # format / ATS-friendliness
    found = set(parsed["sections_found"])
    fmt = 0
    fmt += 10 * len({"education", "skills", "projects", "experience"} & found)
    fmt += 10 if parsed["email"] else 0
    fmt += 10 if parsed["links"] else 0
    fmt += 20 if parsed["metric_count"] >= 3 else 10 if parsed["metric_count"] >= 1 else 0
    fmt += 10 if parsed["action_verb_count"] >= 5 else 5 if parsed["action_verb_count"] >= 2 else 0
    fmt += 10 if 250 <= parsed["word_count"] <= 900 else 0
    fmt = min(fmt, 100)

    if keyword is None:
        ats = 0.6 * semantic + 0.4 * fmt
        weights = {"semantic": 0.6, "keyword": 0.0, "format": 0.4}
    else:
        ats = 0.35 * semantic + 0.45 * keyword + 0.20 * fmt
        weights = {"semantic": 0.35, "keyword": 0.45, "format": 0.20}

    tips = []
    if keyword is not None and keyword < 60:
        tips.append("Add the missing JD keywords where you genuinely have the experience (skills section + project bullets).")
    if parsed["metric_count"] < 3:
        tips.append("Quantify impact: add numbers (accuracy %, latency, users, requests, time saved).")
    if parsed["action_verb_count"] < 5:
        tips.append("Start bullets with strong action verbs (built, optimised, deployed, automated).")
    for sec in ("projects", "skills", "education"):
        if sec not in found:
            tips.append(f"Add a clearly titled '{sec.title()}' section so ATS parsers can find it.")
    if not parsed["links"]:
        tips.append("Add GitHub/LinkedIn links.")
    if not (250 <= parsed["word_count"] <= 900):
        tips.append("Keep the resume focused: roughly 1 page for freshers (about 250-700 words).")

    result = {
        "score": round(ats, 1),
        "breakdown": {"semantic_match": round(semantic, 1), "keyword_coverage": None if keyword is None else round(keyword, 1),
                      "format_quality": round(fmt, 1)},
        "weights": weights,
        "embedding_backend": emb.name,
        "tips": tips,
    }
    return {"ats": result, "trace": [f"ATS score {result['score']} (embeddings: {emb.name})"]}


def skill_gap_node(state: PipelineState) -> dict:
    emb = get_embedder()
    jd_skills = extract_skills(state["jd_text"])
    resume_skills = extract_skills(state["resume_text"])
    matched = [s for s in jd_skills if s in resume_skills]
    absent = [s for s in jd_skills if s not in resume_skills]

    # semantic evidence: does any resume chunk strongly relate to the missing skill?
    resume_chunks = chunk_text(state["resume_text"]) or [state["resume_text"][:500]]
    store = VectorStore(emb.dim)
    store.add(emb.embed(resume_chunks), [{"text": c} for c in resume_chunks])
    thresh = 0.55 if is_semantic(emb) else 0.38
    missing, weak = [], []
    if absent:
        sims = store.max_similarity(emb.embed([f"experience with {s}" for s in absent]))
        for s, sim in zip(absent, sims):
            (weak if sim >= thresh else missing).append((s, float(sim)))

    def rank(items):
        return sorted(items, key=lambda x: (-jd_skills[x[0]], x[0]))

    missing_sorted = [{"skill": s, "category": category_of(s), "jd_mentions": jd_skills[s], "evidence": round(sim, 2)} for s, sim in rank(missing)]
    weak_sorted = [{"skill": s, "category": category_of(s), "jd_mentions": jd_skills[s], "evidence": round(sim, 2)} for s, sim in rank(weak)]
    extra = [s for s in resume_skills if s not in jd_skills]
    skills = {"matched": sorted(matched, key=lambda s: -jd_skills[s]), "missing": missing_sorted, "weak": weak_sorted, "extra": extra[:15]}
    return {"skills": skills, "trace": [f"Skill gap: {len(matched)} matched, {len(missing_sorted)} missing, {len(weak_sorted)} weak"]}


def retrieve_context_node(state: PipelineState) -> dict:
    """RAG step: company knowledge from FAISS + JD snippets that mention the student's gaps."""
    emb = get_embedder()
    kb = find_company(state.get("company", ""), state.get("role", ""))
    jd_chunks = chunk_text(state["jd_text"])
    snippets: list[str] = []
    if jd_chunks:
        store = VectorStore(emb.dim)
        store.add(emb.embed(jd_chunks), [{"text": c} for c in jd_chunks])
        for m in state["skills"]["missing"][:4]:
            for _, meta in store.search(emb.embed([f"{m['skill']} requirement"])[0], k=1):
                if meta["text"] not in snippets:
                    snippets.append(meta["text"])
    return {"context": {"company_kb": kb, "jd_snippets": snippets[:6]},
            "trace": [f"Retrieved context for '{kb['company']}' ({kb['matched_by']} match) + {len(snippets)} JD snippets"]}


# ----------------------------------------------------------------- LLM prompts
def _gap_names(state) -> list[str]:
    return [m["skill"] for m in state["skills"]["missing"]] + [w["skill"] for w in state["skills"]["weak"]]


def _normalize_q(items, default_cat: str) -> list[dict]:
    out = []
    for q in items or []:
        if isinstance(q, str):
            q = {"question": q}
        text = (q.get("question") or "").strip()
        if text:
            out.append({"question": text, "category": q.get("category", default_cat), "difficulty": q.get("difficulty", "Medium"),
                        "focus_skill": q.get("focus_skill", ""), "why": q.get("why", ""),
                        "ideal_points": q.get("ideal_points", [])[:6] if isinstance(q.get("ideal_points"), list) else []})
    return out


def _normalize_coding(items) -> list[dict]:
    out = []
    for q in items or []:
        title, stmt = (q.get("title") or "").strip(), (q.get("statement") or "").strip()
        if title and stmt:
            topics = q.get("topics", [])
            out.append({"title": title, "statement": stmt, "difficulty": q.get("difficulty", "Medium"),
                        "topics": topics if isinstance(topics, list) else [str(topics)],
                        "example": q.get("example", ""), "hint": q.get("hint", ""),
                        "expected_complexity": q.get("expected_complexity", ""), "why": q.get("why", "")})
    return out


def questions_node(state: PipelineState) -> dict:
    llm = get_llm()
    kb = state["context"]["company_kb"]
    gaps = _gap_names(state)
    matched = state["skills"]["matched"]
    projects = state["parsed_resume"]["projects"]
    company, role = state.get("company") or "a product/service company", state.get("role") or "Software Engineer"

    warnings, mode = [], "offline"
    iq: list[dict] = []
    cq: list[dict] = []
    if llm.available:
        system = ("You are an expert campus-placement interviewer and coding coach for Indian engineering students. "
                  "Ground every question in the provided resume facts, skill gaps and company context. Do not invent facts about the company; "
                  "use only the provided context and general, widely known interview patterns.")
        user = f"""Target company: {company}
Target role: {role}
Company hiring context (retrieved): process={kb['process']} | focus={kb['focus']} | themes={kb['themes']}
Skills the student already shows (matching the JD): {matched}
Skill gaps (missing from resume): {gaps}
Student's projects (resume): {projects[:6]}
Relevant JD snippets: {state['context']['jd_snippets']}

Create:
- 8 interview_questions: ~3 targeting skill gaps, ~3 deep-dives into the student's resume projects/skills, 1 company-specific, 1 behavioral. 
- 4 coding_questions: realistic for {company} online assessments/interviews, difficulty mix Easy/Medium/Medium/Hard-ish, topics related to the gaps and company focus.

JSON schema:
{{"interview_questions":[{{"question":str,"category":str,"difficulty":"Easy|Medium|Hard","focus_skill":str,"why":str,"ideal_points":[str,str,str]}}],
 "coding_questions":[{{"title":str,"statement":str,"difficulty":"Easy|Medium|Hard","topics":[str],"example":str,"hint":str,"expected_complexity":str,"why":str}}]}}"""
        try:
            data = llm.chat_json(system, user, temperature=0.5, max_tokens=4000)
            iq = _normalize_q(data.get("interview_questions"), "technical")
            cq = _normalize_coding(data.get("coding_questions"))
            mode = "groq"
        except LLMError as e:
            log.warning("LLM failure (%s): %s", e.kind, e.details)
            warnings.append(f"llm:{e.kind}|Questions were generated by the offline engine. {e}")
    if len(iq) < 4:
        iq = offline.offline_interview_questions(company, role, [m['skill'] for m in state["skills"]["missing"]] + [w['skill'] for w in state["skills"]["weak"]],
                                                 matched, kb, projects)
        mode = "offline"
    if len(cq) < 2:
        cq = offline.offline_coding_questions(company, gaps, kb)
    return {"interview_questions": iq, "coding_questions": cq, "generation_mode": mode, "warnings": warnings,
            "trace": [f"Generated {len(iq)} interview + {len(cq)} coding questions ({mode})"]}


def _assign_ids(roadmap: dict) -> dict:
    for w in roadmap["weeks"]:
        for i, t in enumerate(w["tasks"], 1):
            t["id"] = f"w{w['week']}-t{i}"
    return roadmap


def normalize_roadmap(data: dict, weeks: int, fallback: dict) -> dict:
    out_weeks = []
    raw = data.get("weeks") if isinstance(data, dict) else None
    for i, w in enumerate(raw or [], 1):
        tasks = []
        for t in w.get("tasks", []):
            if isinstance(t, str):
                t = {"title": t}
            title = (t.get("title") or "").strip()
            if title:
                try:
                    hrs = float(t.get("est_hours", 2))
                except (TypeError, ValueError):
                    hrs = 2.0
                tasks.append({"title": title, "type": t.get("type", "learn"), "skill": t.get("skill", ""),
                              "est_hours": hrs, "resource": t.get("resource", "")})
        if tasks:
            out_weeks.append({"week": len(out_weeks) + 1, "theme": w.get("theme", f"Week {i}"),
                              "goals": [g for g in w.get("goals", []) if isinstance(g, str)][:4], "tasks": tasks})
    # pad / trim to the requested number of weeks using the offline plan
    fb = fallback["weeks"]
    while len(out_weeks) < weeks:
        extra = dict(fb[len(out_weeks) % len(fb)])
        extra["week"] = len(out_weeks) + 1
        out_weeks.append(extra)
    return _assign_ids({"weeks": out_weeks[:weeks], "summary": (data or {}).get("summary") or fallback["summary"]})


def roadmap_node(state: PipelineState) -> dict:
    llm = get_llm()
    weeks = max(2, min(int(state.get("weeks") or 6), 12))
    missing = [m["skill"] for m in state["skills"]["missing"]]
    weak = [w["skill"] for w in state["skills"]["weak"]]
    company, role = state.get("company", ""), state.get("role", "")
    fallback = offline.offline_roadmap(missing + weak, weak, company, role, weeks)
    roadmap, warnings = None, []
    if llm.available:
        user = f"""Create a {weeks}-week placement preparation roadmap (about 10 hours/week) for a final-year B.Tech student.
Target: {role or 'Software Engineer'} at {company or 'a tech company'}.
Skill gaps to close (priority order): {missing + weak}
Skills already strong: {state['skills']['matched']}
ATS score: {state['ats']['score']}/100. Company hiring focus: {state['context']['company_kb']['focus']}.
Rules: week 1 includes a resume fix task; every week has 3-5 concrete tasks mixing learn/practice/project/interview; the last week has a full mock round; 
name resources generically (e.g. 'NeetCode 150', 'official docs') — do NOT invent URLs.
JSON schema: {{"summary":str,"weeks":[{{"week":int,"theme":str,"goals":[str],"tasks":[{{"title":str,"type":"learn|practice|project|interview|resume","skill":str,"est_hours":number,"resource":str}}]}}]}}"""
        try:
            data = llm.chat_json("You are a pragmatic placement mentor who writes realistic, specific weekly plans.", user, temperature=0.4, max_tokens=4500)
            roadmap = normalize_roadmap(data, weeks, fallback)
        except LLMError as e:
            log.warning("LLM failure (%s): %s", e.kind, e.details)
            warnings.append(f"llm:{e.kind}|The roadmap was built by the offline planner. {e}")
    if roadmap is None:
        roadmap = _assign_ids(fallback)
    return {"roadmap": roadmap, "warnings": warnings, "trace": [f"Built {len(roadmap['weeks'])}-week roadmap"]}
