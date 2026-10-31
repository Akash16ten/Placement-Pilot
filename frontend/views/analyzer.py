"""Resume Analyzer: input form (PDF upload or pasted text) and the ATS results view."""
import streamlit as st

import api
import data
import state
from state import ss
from ui import (badge, bar, card, card_title, chip, esc, html, icon, loader, notice, page_header, ring, score_kind, toast_err, toast_ok)

LOADER_STEPS = ["Parsing your resume", "Embedding resume and job description", "Scoring ATS fit and detecting skill gaps",
                "Retrieving company context", "Generating interview and coding questions", "Building your weekly roadmap"]


class _Upload:
    """Minimal stand-in for Streamlit's UploadedFile, so api.analyze() stays unchanged."""
    def __init__(self, name: str, data: bytes):
        self.name, self._data = name, data

    def getvalue(self) -> bytes:
        return self._data


def _clear_pdf():
    ss.f_pdf = None


def _show_results():
    ss.an_view = "results"


def _run_analysis(placeholder):
    pdf = None
    if ss.f_mode == "Upload PDF" and ss.f_pdf:
        pdf = _Upload(*ss.f_pdf)
    text = ss.f_text if ss.f_mode == "Paste text" else ""
    placeholder.markdown(loader("Analyzing your profile", LOADER_STEPS), unsafe_allow_html=True)
    try:
        res = api.analyze(ss.f_jd, ss.f_company, ss.f_role, int(ss.f_weeks), pdf, text)
    except api.ApiError as e:
        placeholder.empty()
        notice("bad", f"<b>Analysis failed.</b> {esc(e)}")
        return
    placeholder.empty()
    for k in [k for k in ss.keys() if str(k).startswith(("task_", "hint", "rate"))]:
        del ss[k]
    ss.pop("w_an_view", None)
    ss.analysis, ss.an_view = res, "results"
    ss.iv = ss.report = ss.adapt_changes = None
    ss.report_hist = []
    state.bump()
    state.log("analysis", f"Analyzed resume for {res['role'] or 'target role'}" + (f" at {res['company']}" if res["company"] else "") + f": ATS {res['ats']['score']:.0f}")
    toast_ok("Analysis complete.")
    st.rerun()


# ------------------------------------------------------------------------------ form
def form():
    page_header("Resume Analyzer", "Analyze your profile against a role",
                "Give PlacementPilot your resume, the job description and a target company. It scores ATS fit, finds skill gaps and builds your practice plan.")
    left, right = st.columns([1, 1], gap="medium")
    with left:
        with card("resume"):
            card_title("Your resume", "file")
            mode = st.segmented_control("Resume source", ["Upload PDF", "Paste text"], default=ss.f_mode, key="w_f_mode",
                                        label_visibility="collapsed", on_change=lambda: ss.__setitem__("f_mode", ss.w_f_mode or ss.f_mode))
            mode = mode or ss.f_mode
            if mode == "Upload PDF":
                up = st.file_uploader("Resume PDF", type=["pdf"], key="w_pdf", label_visibility="collapsed",
                                      help="Text-based PDFs only. Scanned images cannot be read (no OCR).")
                if up is not None:
                    ss.f_pdf = (up.name, up.getvalue())
                elif ss.f_pdf:
                    c1, c2 = st.columns([4, 1.2], vertical_alignment="center")
                    c1.markdown(f'<div class="chip ok" style="margin:0">{icon("file", 14)}{esc(ss.f_pdf[0])} · {len(ss.f_pdf[1]) // 1024} KB attached</div>', unsafe_allow_html=True)
                    c2.button("Remove", key="rm-pdf", type="tertiary", on_click=_clear_pdf)
                html('<div class="faint" style="font-size:12px">PDF, up to 5 MB. Your resume is used only to build your own analysis and can be deleted at any time.</div>')
            else:
                state.sticky(st.text_area, "f_text", "Resume text", height=250, label_visibility="collapsed",
                             placeholder="Paste the plain text of your resume: education, skills, projects, experience…")
                n = len(ss.f_text.strip())
                html(f'<div class="faint" style="font-size:12px">{n} characters {"" if n >= 80 else "· at least 80 needed"}</div>')
        with card("target"):
            card_title("Target", "target")
            c1, c2 = st.columns(2)
            with c1:
                state.sticky(st.text_input, "f_company", "Target company", placeholder="e.g. Amazon, TCS, Infosys", max_chars=100)
            with c2:
                state.sticky(st.text_input, "f_role", "Target role", max_chars=100)
            state.sticky(st.slider, "f_weeks", "Roadmap duration (weeks)", min_value=2, max_value=12)
            html(f'<div class="faint" style="font-size:12px">Plans are sized for roughly 10 focused hours per week, about {int(ss.f_weeks) * 10} hours in total.</div>')
    with right:
        with card("jd"):
            card_title("Job description", "building")
            state.sticky(st.text_area, "f_jd", "Job description", height=470, label_visibility="collapsed", max_chars=15000,
                         placeholder="Paste the full job description: responsibilities, requirements, preferred skills…")
            n = len(ss.f_jd.strip())
            html(f'<div class="faint" style="font-size:12px">{n} characters {"" if n >= 30 else "· at least 30 needed"}</div>')

    resume_ok = bool(ss.f_pdf) if ss.f_mode == "Upload PDF" else len(ss.f_text.strip()) >= 80
    jd_ok = len(ss.f_jd.strip()) >= 30
    c1, c2 = st.columns([1.1, 2.5], vertical_alignment="center")
    go_ = c1.button("Analyze My Profile", key="analyze", icon=":material/auto_awesome:", type="primary", width="stretch", disabled=not (resume_ok and jd_ok))
    c2.markdown(f'<div style="display:flex;gap:.4rem;flex-wrap:wrap">{chip("Resume", "ok" if resume_ok else "mute")}{chip("Job description", "ok" if jd_ok else "mute")}'
                f'{chip("Company (optional, improves question relevance)", "ok" if ss.f_company.strip() else "mute")}</div>', unsafe_allow_html=True)
    ph = st.empty()
    if go_:
        _run_analysis(ph)


# ---------------------------------------------------------------------------- results
def _verdict(score: float):
    if score >= 75: return "Strong match", "ok"
    if score >= 55: return "Promising, with gaps", "warn"
    return "Needs work", "bad"


JUMPS = [("skills", "Skill gaps", ":material/track_changes:"), ("prep", "Interview prep", ":material/quiz:"), ("mock", "Mock interview", ":material/mic:"),
         ("roadmap", "Roadmap", ":material/route:"), ("analytics", "Analytics", ":material/monitoring:")]


def _jump_strip():
    """Equal-weight shortcuts: no section is presented as 'the next step'."""
    html('<div class="faint" style="font-size:11px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;margin:.2rem 0 -.1rem">Jump to</div>')
    for col, (key, label, mic) in zip(st.columns(len(JUMPS)), JUMPS):
        col.button(label, key=f"jump-{key}", icon=mic, type="secondary", width="stretch", on_click=state.go, args=(key,))


def results():
    A = ss.analysis
    ats = A["ats"]
    page_header("Resume Analyzer", "Your ATS analysis",
                f"{A['role'] or 'Target role'}" + (f" at {A['company']}" if A["company"] else "") + " · scored against the job description you provided.")
    _warnings(A.get("warnings", []))
    _jump_strip()

    l, r = st.columns([1.15, 1], gap="medium")
    with l:
        with card("ats"):
            card_title("Overall ATS score", "target")
            verdict, kind = _verdict(ats["score"])
            b = ats["breakdown"]

            def row(label, val, desc):
                if val is None:
                    return (f'<div style="margin-top:.8rem"><div class="dim" style="gap:.5rem"><span style="flex:1;color:var(--text);font-weight:550;font-size:13.5px">{label}</span>'
                            f'<span class="faint">n/a</span></div><div class="faint" style="font-size:12px">The job description had no recognised skills to compare.</div></div>')
                return (f'<div style="margin-top:.8rem"><div style="display:flex;justify-content:space-between;font-size:13.5px"><span style="font-weight:550">{label}</span>'
                        f'<b class="num">{val:.0f}<span class="faint" style="font-weight:500">/100</span></b></div>{bar(val, score_kind(val), 6)}'
                        f'<div class="faint" style="font-size:12px;margin-top:4px">{desc}</div></div>')
            big_ring = ring(ats["score"], 168, 13, f"{ats['score']:.0f}", "out of 100")
            html(f'<div style="display:flex;gap:1.6rem;align-items:center;flex-wrap:wrap"><div>{big_ring}</div>'
                 f'<div style="flex:1;min-width:220px">{badge(verdict, kind)}<div class="faint" style="font-size:12.5px;margin-top:.5rem;line-height:1.55">'
                 f'Blend of semantic match, keyword coverage and format quality. Embeddings: {esc(ats["embedding_backend"])}.</div></div></div>'
                 + row("Semantic match", b["semantic_match"], "How closely your resume lines match the job requirement lines.")
                 + row("Keyword / skill coverage", b["keyword_coverage"], "Required skills found in your resume, weighted by how often the JD mentions them.")
                 + row("Resume formatting", b["format_quality"], "Section structure, contact links, quantified impact and action verbs."))
    with r:
        with card("tips"):
            card_title("Actionable recommendations", "list")
            if ats["tips"]:
                rows = "".join(f'<div class="rowi"><div class="ic warn">{icon("zap", 15)}</div><div class="tx">{esc(t)}</div></div>' for t in ats["tips"])
                html(f'<div class="rows">{rows}</div>')
            else:
                notice("ok", "No structural issues found. Your resume is well formatted for ATS parsing.")
        with card("peek"):
            sk = A["skills"]
            card_title("Skill snapshot", "layers")
            ch = "".join(chip(s, "ok") for s in sk["matched"]) or '<span class="faint" style="font-size:13px">No required skills matched yet.</span>'
            html(f'<div class="faint" style="font-size:12px;margin-bottom:.35rem">MATCHED ({len(sk["matched"])})</div>{ch}')
            ch = "".join(chip(m["skill"], "bad") for m in sk["missing"]) or '<span class="faint" style="font-size:13px">Nothing missing.</span>'
            html(f'<div class="faint" style="font-size:12px;margin:.5rem 0 .35rem">MISSING ({len(sk["missing"])})</div>{ch}')
            if sk["weak"]:
                ch = "".join(chip(m["skill"], "warn") for m in sk["weak"])
                html(f'<div class="faint" style="font-size:12px;margin:.5rem 0 .35rem">WEAK EVIDENCE ({len(sk["weak"])})</div>{ch}')

    pr = A["parsed_resume"]
    with st.expander("What we parsed from your resume"):
        secs = "".join(chip(s.title(), "ok") for s in pr["sections_found"]) or "None detected"
        html(f'<div class="faint" style="font-size:12px;margin-bottom:.3rem">SECTIONS DETECTED</div>{secs}'
             f'<div style="display:flex;gap:2rem;flex-wrap:wrap;margin-top:.8rem;font-size:13.5px">'
             f'<div><b class="num">{pr["word_count"]}</b> <span class="mute">words</span></div>'
             f'<div><b class="num">{pr["metric_count"]}</b> <span class="mute">quantified results</span></div>'
             f'<div><b class="num">{pr["action_verb_count"]}</b> <span class="mute">action verbs</span></div>'
             f'<div><b class="num">{len(pr["skills"])}</b> <span class="mute">skills recognised</span></div>'
             f'<div><b class="num">{len(pr["links"])}</b> <span class="mute">profile links</span></div></div>')
    with st.expander("Pipeline trace"):
        html("".join(f'<div class="rowi"><div class="ic">{icon("check", 14, 2.2)}</div><div class="tx">{esc(t)}</div></div>' for t in A.get("trace", [])))


LLM_HELP = {
    "model_unavailable": "Groq has no usable model for your API key, so questions and the roadmap came from the offline engine. "
                         "Set <code>GROQ_MODEL</code> in <code>.env</code> to a model available in your Groq console, restart the backend and run the analysis again.",
    "auth": "Groq rejected your API key, so the offline engine was used. Check <code>GROQ_API_KEY</code> in <code>.env</code>.",
    "rate_limit": "Groq's rate limit was reached, so the offline engine was used. Wait a minute and run the analysis again.",
    "no_key": "No Groq key is configured, so the offline engine was used.",
}


def _warnings(ws: list[str]) -> None:
    """One calm notice instead of raw API errors; technical detail stays available but tucked away."""
    kinds, raw, plain = [], [], []
    for w in ws:
        if w.startswith("llm:"):
            k, _, msg = w[4:].partition("|")
            if k not in kinds:
                kinds.append(k)
            raw.append(msg)
        else:
            plain.append(w)
    for k in kinds[:1]:
        notice("warn", "<b>AI generation fell back to offline mode.</b> " + LLM_HELP.get(k, "The AI model did not return a usable answer, so the offline engine was used. Try again in a moment."))
    for w in plain:
        notice("warn", esc(w))
    if raw:
        with st.expander("Technical details"):
            html("".join(f'<div class="rowi"><div class="tx">{esc(m)}</div></div>' for m in dict.fromkeys(raw)))


def render():
    if ss.analysis:
        want = "Current results" if ss.an_view == "results" else "New analysis"
        view = st.segmented_control("View", ["Current results", "New analysis"], default=want, key="w_an_view", label_visibility="collapsed",
                                    on_change=lambda: ss.__setitem__("an_view", "form" if ss.w_an_view == "New analysis" else "results"))
        ss.an_view = "form" if (view or want) == "New analysis" else "results"
    if ss.analysis and ss.an_view == "results":
        results()
    else:
        form()
