"""Mock HR Interview: setup, focused interview, per-answer feedback and final report."""
import streamlit as st

import api
import data
import state
from state import ss
from ui import badge, bar, card, card_title, chip, empty_state, esc, html, icon, minify, notice, page_header, ring, score_kind, toast_err, toast_ok

DIMS = [("clarity", "Clarity"), ("structure", "Structure"), ("impact", "Impact"), ("relevance", "Relevance")]


def _dim_rows(vals: dict) -> str:
    out = ""
    for k, label in DIMS:
        v = vals.get(k, 0)
        out += f'<div class="dim"><span class="l">{label}</span>{bar(v * 10, score_kind(v * 10), 6)}<span class="v">{v:g}</span></div>'
    return f'<div style="display:flex;flex-direction:column;gap:.55rem">{out}</div>'


def _start(n: int):
    try:
        r = api.start_interview(state.sid(), n)
    except api.ApiError as e:
        toast_err(str(e)); return
    ss.iv = {"id": r["interview_id"], "total": r["total_questions"], "qnum": 1, "question": r["question"], "kind": r["kind"], "history": [], "last": None}
    ss.report, ss.report_hist = None, []


def _exit():
    ss.iv = None


def _again():
    ss.report, ss.report_hist = None, []


def _adapt_and_go():
    try:
        ss.adapt_changes = api.adapt(state.sid())["changes"]
        state.bump(); state.log("adapt", "Adapted roadmap from interview results")
        ss.nav_to = "roadmap"
    except api.ApiError as e:
        toast_err(str(e))


# ------------------------------------------------------------------------------ setup
def setup():
    A, sid = ss.analysis, state.sid()
    d = data.dash(sid, ss.rev)
    hist = d["mock_hr_history"] if d else []
    l, r = st.columns([1.5, 1], gap="medium")
    with l:
        with card("setup"):
            card_title("Interview setup", "mic")
            who = f"{esc(A['role'] or 'your target role')}" + (f" at {esc(A['company'])}" if A["company"] else "")
            html(f'<div class="h2">Practice a realistic HR round for {who}</div>'
                 '<div class="sub">You will get one question at a time. Answer as you would in the room. Vague answers trigger a follow-up, exactly like a real interviewer would.</div>')
            n = st.slider("Number of main questions", 3, 10, 5, key="iv-n", help="Follow-up questions are extra and do not count toward this number.")
            html(f'<div class="faint" style="font-size:12px">About {n * 3 + 2} minutes at a relaxed pace.</div>')
            st.button("Start interview", key="iv-start", icon=":material/play_arrow:", type="primary", on_click=_start, args=(n,))
    with r:
        with card("expect"):
            card_title("How it works", "info")
            items = [("sparkle", "Questions tailored to your resume and skill gaps"), ("refresh", "Adaptive follow-ups when an answer lacks detail"),
                     ("chart", "Scored 0–10 on clarity, structure, impact, relevance"), ("trend", "Results feed your readiness score and roadmap")]
            html('<div class="rows">' + "".join(f'<div class="rowi"><div class="ic">{icon(i, 15)}</div><div class="tx">{t}</div></div>' for i, t in items) + '</div>')
        if hist:
            with card("prev"):
                card_title("Your history", "clock")
                html(f'<div class="big">{hist[-1]["overall_10"]}<small>/ 10 latest</small></div><div class="kpi-foot">{len(hist)} interview{"s" if len(hist) != 1 else ""} completed</div>')


# ------------------------------------------------------------------------------- live
def live():
    iv = ss.iv
    _, mid, _ = st.columns([.35, 3, .35])
    with mid:
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        pct = (iv["qnum"] - 1) / iv["total"] * 100
        c1.markdown(minify(f'<div style="display:flex;justify-content:space-between;font-size:12.5px;color:var(--muted);margin-bottom:6px"><span>Question <b style="color:var(--text)">{iv["qnum"]}</b> of {iv["total"]}'
                           + (f' &nbsp;{badge("Follow-up", "warn")}' if iv["kind"] == "followup" else "") + f'</span><span>{pct:.0f}% complete</span></div>{bar(pct, "grad", 5)}'), unsafe_allow_html=True)
        c2.button("Exit", key="iv-exit", type="tertiary", icon=":material/close:", on_click=_exit, help="Leave this interview. Unfinished interviews are not scored.")

        if iv["last"]:
            ev = iv["last"]["eval"]
            with st.expander("Feedback on your previous answer", expanded=True):
                mini = ring(ev["overall"], 84, 8, f"{ev['overall']:g}", "/10", 10)
                top = f'<div style="display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap"><div>{mini}</div><div style="flex:1;min-width:240px">{_dim_rows(ev)}</div></div>'
                html(top)
                good = "".join(f'<div class="rowi"><div class="ic ok">{icon("check", 14, 2.4)}</div><div class="tx">{esc(x)}</div></div>' for x in ev.get("strengths", []))
                imp = "".join(f'<div class="rowi"><div class="ic warn">{icon("zap", 14)}</div><div class="tx">{esc(x)}</div></div>' for x in ev.get("improvements", []))
                html(f'<div class="rows" style="margin-top:.4rem">{good}{imp}</div>')
                if ev.get("better_answer_tip"):
                    notice("info", f'<b>Tip:</b> {esc(ev["better_answer_tip"])}')

        with st.container(key="iq-main"):
            who = f'HR interviewer{" · " + esc(ss.analysis["company"]) if ss.analysis["company"] else ""}'
            html(f'<div class="iq-who"><span class="iq-av">{icon("message", 15)}</span>{who}</div><div class="iq-q">{esc(iv["question"])}</div>')
        with st.form("ans-form", clear_on_submit=True, border=False):
            ans = st.text_area("Your answer", height=190, key="iv-ans", placeholder="Take your time. Structure your answer: Situation, Task, Action, Result. Add numbers where you can.")
            c1, c2 = st.columns([1.2, 3], vertical_alignment="center")
            sub = c1.form_submit_button("Submit answer", type="primary", icon=":material/send:", width="stretch")
            c2.markdown('<div class="faint" style="font-size:12.5px">Evaluated on clarity, structure, impact and relevance.</div>', unsafe_allow_html=True)
        if sub:
            if len(ans.strip()) < 2:
                toast_err("Write an answer before submitting.")
                return
            with st.spinner("Evaluating your answer…"):
                try:
                    resp = api.answer(iv["id"], ans.strip())
                except api.ApiError as e:
                    toast_err(str(e)); return
            iv["history"].append({"question": iv["question"], "kind": iv["kind"], "answer": ans.strip(), "eval": resp["evaluation"]})
            iv["last"] = {"eval": resp["evaluation"]}
            if resp["finished"]:
                ss.report, ss.report_hist, ss.iv = resp["report"], iv["history"], None
                state.bump(); state.log("interview", f"Completed mock HR interview: {resp['report']['overall']}/10")
                toast_ok("Interview complete. Your report is ready.")
            else:
                iv.update({"question": resp["question"], "kind": resp["kind"], "qnum": resp["question_number"], "total": resp["total_questions"]})
            st.rerun()


# ----------------------------------------------------------------------------- report
def report():
    rep = ss.report
    ov = rep["overall"]
    kind = "ok" if ov >= 7.5 else "warn" if ov >= 5.5 else "bad"
    page_header("Mock HR Interview", "Interview performance report", f"{rep['questions_answered']} answers evaluated.")
    l, r = st.columns([1, 1.5], gap="medium")
    with l:
        with card("rep-score"):
            card_title("Overall", "target")
            big = ring(ov, 170, 13, f"{ov:g}", "out of 10", 10, color=None)
            html(f'<div style="display:flex;flex-direction:column;align-items:center;gap:.7rem;padding:.4rem 0">{big}{badge(rep["verdict"], kind)}</div>')
            if rep.get("weakest_dimension"):
                html(f'<div class="faint" style="font-size:12.5px;text-align:center">Weakest area: <b style="color:var(--text)">{esc(rep["weakest_dimension"].title())}</b></div>')
    with r:
        with card("rep-dims"):
            card_title("Scores by dimension", "chart")
            html(_dim_rows(rep["dimension_averages"]))
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            with card("rep-good"):
                card_title("Strengths", "check-circle")
                html("".join(f'<div class="rowi"><div class="ic ok">{icon("check", 14, 2.4)}</div><div class="tx">{esc(x)}</div></div>' for x in rep["top_strengths"])
                     or '<div class="faint" style="font-size:13px">No standout strengths were identified. Add concrete examples and numbers.</div>')
        with c2:
            with card("rep-imp"):
                card_title("Work on", "zap")
                html("".join(f'<div class="rowi"><div class="ic warn">{icon("zap", 14)}</div><div class="tx">{esc(x)}</div></div>' for x in rep["top_improvements"])
                     or '<div class="faint" style="font-size:13px">Nothing major to fix.</div>')
    with card("rep-q"):
        card_title("Question by question", "list")
        rows = ""
        for i, q in enumerate(rep["per_question"], 1):
            sc = q["score"]
            tip = f'<small>{esc(q["tip"])}</small>' if q.get("tip") else ""
            tag = f' {badge("Follow-up", "warn")}' if q["kind"] == "followup" else ""
            rows += (f'<div class="rowi" style="align-items:center"><div class="q-num" style="margin:0">{i}</div><div class="tx">{esc(q["question"])}{tag}{tip}</div>'
                     f'<div style="width:120px;text-align:right"><b class="num">{sc:g}</b><span class="faint">/10</span>{bar(sc * 10, score_kind(sc * 10), 4)}</div></div>')
        html(f'<div class="rows">{rows}</div>')
    if ss.report_hist:
        with st.expander("Your answers"):
            for h in ss.report_hist:
                html(f'<div style="margin-bottom:1rem"><div style="font-weight:600;font-size:14px">{esc(h["question"])}</div>'
                     f'<div style="color:var(--muted);font-size:13.5px;line-height:1.6;margin-top:.3rem;white-space:pre-wrap">{esc(h["answer"])}</div></div>')
    c1, c2, c3, _ = st.columns([1.2, 1.7, 1.3, 1.5])
    c1.button("Run another", key="rep-again", icon=":material/replay:", type="secondary", width="stretch", on_click=_again)
    c2.button("Adapt my roadmap", key="rep-adapt", icon=":material/auto_fix_high:", type="primary", width="stretch", on_click=_adapt_and_go,
              help="Adds reinforcement tasks for weak dimensions to your roadmap.")
    c3.button("View analytics", key="rep-an", type="secondary", width="stretch", on_click=state.go, args=("analytics",))


def render():
    if not ss.analysis:
        page_header("Mock HR Interview", "Practice with an AI interviewer")
        empty_state("mic", "Analyze your resume first", "The interviewer asks questions tailored to your resume, skill gaps and target company.")
        st.button("Go to Resume Analyzer", key="iv-cta", type="primary", on_click=state.new_analysis)
        return
    if ss.iv:
        live()
    elif ss.report:
        report()
    else:
        page_header("Mock HR Interview", "Practice with an AI interviewer", "A focused, distraction-free HR round with instant feedback.")
        setup()
