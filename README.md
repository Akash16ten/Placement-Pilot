# 🧭 PlacementPilot

**An AI placement-preparation platform.** Give it a resume (PDF), a job description and a target company. It produces an ATS score, a missing-skill report, company-aware interview and coding questions, a mock HR interview, and an adaptive week-by-week roadmap with progress tracking.

Built on **LangGraph · FAISS (RAG) · HuggingFace sentence-transformers · Groq LLM · FastAPI · Streamlit**.

---

## Architecture (matches the project deck)

```
Streamlit client ──HTTP──▶ FastAPI gateway (router factory + rate limiter)
                              │  /resume  /interview  /plan  /progress
                              ▼
                     LangGraph agents ──▶ Groq LLM (+ smaller Groq model as fallback)
                              │
                              ▼
        FAISS (resume vectors, company/JD context) · HF embeddings · SQLite (sessions, progress)
```

| Deck module | Code |
|---|---|
| 1. Resume Analyzer & ATS Scorer | `core/pdf_parser.py`, `agents/nodes.py::ats_node` |
| 2. Skill-Gap & Retrieval Engine | `agents/nodes.py::skill_gap_node / retrieve_context_node`, `agents/knowledge.py`, `core/vectorstore.py` |
| 3. Question Generator | `agents/nodes.py::questions_node` |
| 4. Mock HR Interview Agent | `agents/hr_graph.py` (LangGraph loop: evaluate → follow-up / next / finish) |
| 5. Roadmap Generator | `agents/nodes.py::roadmap_node` |
| 6. Weekly Progress Tracker | `routers/progress.py`, `routers/plan.py`, `agents/adapt.py` |

**Analysis graph:** `parse_resume → ats_score → skill_gap → retrieve_context → generate_questions → build_roadmap`

**ATS score** = 35% semantic match (embedding similarity of JD requirement lines vs resume lines) + 45% weighted keyword/skill coverage + 20% resume format quality. The components are returned too, so the score is explainable.

**Adaptive roadmap** (deterministic, so every change can be explained): carries over unfinished tasks, adds reinforcement tasks for weak mock-HR dimensions, schedules revisits for coding topics you struggled with, and rebalances overloaded weeks.

---

## Quick start

```bash
# 1. install (Python 3.10+)
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. configure
cp .env.example .env        # then put your key in GROQ_API_KEY (free at console.groq.com)

# 3. run (two terminals)
./run_backend.sh            # API  → http://localhost:8000/docs
./run_frontend.sh           # UI   → http://localhost:8501 (run from the project root)
```

Windows: use `run_backend.bat` / `run_frontend.bat`. Docker: `docker compose up --build`.

Try it with `sample_data/sample_resume.txt` and `sample_data/sample_jd.txt` (paste them into the UI).

### Works without a Groq key
If `GROQ_API_KEY` is empty the app runs in **offline mode**. ATS scoring, skill gaps, retrieval and progress tracking work fully; questions, roadmap and interview scoring use rule-based generators. This is good for demos but much weaker than the LLM path. The sidebar shows the current mode.

### Embeddings
`EMBEDDING_BACKEND=auto` uses HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (downloaded on first run, about 90 MB). If it can't be installed or downloaded, it falls back to a built-in hashing embedder so nothing crashes. The ATS response reports which backend was used. Use the real model for meaningful semantic scores.

---

## API (see `/docs` for the full schema)

| Method | Path | Purpose |
|---|---|---|
| POST | `/resume/analyze` | multipart: `resume_file` (PDF) or `resume_text`, `jd_text`, `company`, `role`, `weeks` → full analysis + `session_id` |
| GET / DELETE | `/resume/{session_id}` | fetch results / erase all data for the session |
| GET | `/interview/questions/{session_id}` | interview + coding questions |
| POST | `/interview/start` | start a mock HR interview |
| POST | `/interview/{id}/answer` | submit an answer → scores, follow-up or next question, final report |
| GET | `/interview/{id}/report` | final report + transcript |
| GET | `/plan/{session_id}` | roadmap with completion state |
| POST | `/plan/{session_id}/adapt` | adapt the roadmap from progress and results |
| POST | `/progress/{session_id}/task` · `/coding` · `/score` | log task completion, coding attempts, scores |
| GET | `/progress/{session_id}` | readiness dashboard |

## Frontend design notes
Dark-first SaaS shell: violet is the only brand accent, cyan marks the active navigation item, surfaces use hairline borders. Every number on screen comes from a backend response; empty states are shown until data exists. The session id is kept in the URL (`?sid=`), so a browser reload restores your analysis. Priority labels in Skill Gaps and the Roadmap are derived from JD mention counts, and skill progress is the share of roadmap tasks completed per skill (effort, not tested proficiency).

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 12 tests; run offline (no key, no network)
```

## Project layout

```
backend/app/   main.py · config.py · schemas.py
  core/        pdf_parser · skills · embeddings · vectorstore (FAISS) · llm (Groq) · db · rate_limit
  agents/      graph · nodes · hr_graph · adapt · knowledge · offline · state
  routers/     resume · interview · plan · progress
  data/        skills.json (taxonomy) · company_kb.json (seed company knowledge)
frontend/      streamlit_app.py (shell: sidebar, top bar, routing) · api.py (HTTP client, unchanged contracts)
               theme.py (design system CSS) · ui.py (icons, rings, cards) · charts.py (Plotly theme)
               state.py (session state, URL restore) · data.py (cached reads) · insight.py (derived labels)
               views/  overview · analyzer · skills · prep · mock_interview · roadmap · analytics
.streamlit/    config.toml (dark theme, 5 MB upload cap)
tests/  sample_data/
```

---

## Known limitations (good to state upfront in your viva)

- **Groq path:** written against the Groq SDK and tested with a mocked LLM only. Run it once with your real key and check output quality and model names (`GROQ_MODEL` in `.env`; hosted model names change over time).
- **Company knowledge base** is a small seed file of *general* hiring patterns, not official company statements. Extend `company_kb.json` with real data you collect; more entries give better grounding.
- **Skill taxonomy** (`skills.json`) is hand-curated (about 120 skills). Skills outside it are not detected. Add yours.
- **Scanned/image PDFs** have no extractable text (no OCR), and multi-column layouts can scramble the order.
- **The ATS score is an estimate**, not what any specific commercial ATS would output.
- **No authentication.** Sessions are identified by a random ID, and the rate limiter is in-memory and per-process. Add auth and a shared limiter before any public deployment.
- **Not implemented** (the deck's *future scope*): voice interviews, in-app code execution, multilingual support, placement-cell dashboard.
