"""Overview: status at a glance. Shows empty states until real data exists; never fabricates numbers."""
import streamlit as st

import charts
import data
import state
from state import ss
from ui import badge, bar, card, card_title, empty_state, esc, html, icon, kpi, minify, ring, score_kind

COMP_LABEL = {"resume_ats": "Resume (ATS)", "roadmap_completion": "Roadmap", "mock_hr": "Mock HR", "coding_practice": "Coding"}


def _next_actions(A, dash) -> list[tuple[str, str, str]]:
    acts = []
    if not dash["mock_hr_history"]:
        acts.append(("Run your first mock HR interview", "Interview scores feed your readiness and adapt your plan.", "mock"))
    if dash["tasks_done"] == 0:
        acts.append(("Start week 1 of your roadmap", f"{dash['tasks_total']} tasks planned across {len(dash['weekly'])} weeks.", "roadmap"))
    if A["skills"]["missing"]:
        m = A["skills"]["missing"][0]
        acts.append((f"Close your top skill gap: {m['skill']}", f"Mentioned {m['jd_mentions']}x in the job description and absent from your resume.", "skills"))
    if dash["coding"]["attempted"] == 0:
        acts.append(("Log your first coding attempt", "Rate how a problem felt so the roadmap can revisit weak topics.", "prep"))
    if A["ats"]["score"] < 70 and A["ats"]["tips"]:
        acts.append(("Improve your resume", A["ats"]["tips"][0], "analyzer"))
    return acts[:3]


def _activity(dash) -> list[dict]:
    items = list(ss.activity)
    if dash:
        for h in dash["mock_hr_history"]:
            items.append({"ts": h["ts"], "kind": "interview", "text": f"Mock HR interview completed: {h['overall_10']}/10"})
    return sorted(items, key=lambda x: -x["ts"])[:6]


ACT_ICON = {"analysis": ("sparkle", ""), "task": ("check-circle", "ok"), "interview": ("mic", ""), "coding": ("code", "cyan"), "adapt": ("refresh", "warn")}


def render():
    A, s = ss.analysis, state.sid()
    plan = data.plan(s, ss.rev) if A else None
    dash = data.dash(s, ss.rev) if A else None

    # ---------------- hero
    with st.container(key="hero"):
        left, right = st.columns([1.55, 1], gap="large")
        with left:
            if A and dash:
                sub = (f"Targeting <b>{esc(A['role'] or 'your role')}</b>" + (f" at <b>{esc(A['company'])}</b>" if A["company"] else "") +
                       f". {dash['tasks_done']} of {dash['tasks_total']} roadmap tasks complete.")
            else:
                sub = ("Turn your resume, a job description and a target company into an ATS score, a skill-gap report, company-aware practice "
                       "and a week-by-week plan, in one guided workflow.")
            html(f'<div class="eyebrow">AI placement copilot</div><div class="h1" style="font-size:34px">Your placement journey<br>starts here.</div>'
                 f'<div class="sub" style="margin-top:.5rem">{sub}</div>')
            c1, c2, _ = st.columns([1.15, 1, .6])
            c1.button("Start a new analysis" if A else "Start your analysis", key="cta-new", icon=":material/arrow_forward:", type="primary", width="stretch", on_click=state.new_analysis)
            if A:
                c2.button("Continue roadmap", key="cta-road", type="secondary", width="stretch", on_click=state.go, args=("roadmap",))
        with right:
            steps = [("Resume analyzed", bool(A)), ("Skill gaps mapped", bool(A)), ("Practice questions ready", bool(A)),
                     ("Mock HR interview", bool(dash and dash["mock_hr_history"])), ("Roadmap in progress", bool(dash and dash["tasks_done"]))]
            rows = ""
            for i, (t, done) in enumerate(steps, 1):
                mark = icon("check", 13, 2.4) if done else str(i)
                style = ' style="background:rgba(52,211,153,.14);border-color:rgba(52,211,153,.35);color:var(--ok)"' if done else ""
                rows += f'<div class="step"><span class="n"{style}>{mark}</span><span>{"<b>" + t + "</b>" if done else t}</span></div>'
            html(f'<div class="card-title" style="margin-bottom:.3rem">{icon("route", 15)}Your pipeline</div><div class="flow">{rows}</div>')

    # ---------------- empty state
    if not A:
        cols = st.columns(4)
        specs = [("ATS score", "target"), ("Skills matched", "layers"), ("Roadmap completion", "route"), ("Interview readiness", "mic")]
        for col, (lab, ic) in zip(cols, specs):
            with col:
                kpi(lab, ic, "&mdash;", "Unlocks after your first analysis", empty=True)
        l, r = st.columns([1.6, 1], gap="medium")
        with l:
            with card("empty-prog"):
                card_title("Preparation progress", "trend")
                empty_state("chart", "Nothing to show yet", "Upload a resume and a job description. Your readiness, skills and weekly progress will appear here.")
        with r:
            with card("empty-act"):
                card_title("Recent activity", "clock")
                empty_state("clock", "No activity yet", "Actions you take in this session will be listed here.")
        return

    if dash is None or plan is None:
        html('<div class="notice warn"><div>Could not load progress data from the backend. Try again in a moment.</div></div>')
        return

    # ---------------- KPI row
    sk = A["skills"]
    matched, weak, missing = len(sk["matched"]), len(sk["weak"]), len(sk["missing"])
    required = matched + weak + missing
    mocks = dash["mock_hr_history"]
    b = A["ats"]["breakdown"]
    ats_score = A["ats"]["score"]
    ats_ring = ring(ats_score, 92, 9, f"{ats_score:.0f}", "/100")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        with card("kpi-ats"):
            mini = lambda l, v: f'<div class="row" style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted)"><span>{l}</span><b style="color:var(--text)" class="num">{"n/a" if v is None else round(v)}</b></div>'
            html(f'<div class="kpi-label">{icon("target", 15, style="color:var(--violet)")}ATS score</div>'
                 f'<div style="display:flex;gap:1rem;align-items:center">{ats_ring}'
                 f'<div style="flex:1;display:flex;flex-direction:column;gap:5px">{mini("Semantic", b["semantic_match"])}{mini("Keywords", b["keyword_coverage"])}{mini("Format", b["format_quality"])}</div></div>')
    with k2:
        if required:
            seg = lambda n, c: f'<i style="width:{n / required * 100:.1f}%;background:{c}"></i>' if n else ""
            kpi("Skills matched", "layers", f'{matched}<small>/ {required} required</small>',
                f'{missing + weak} to improve · {missing} missing, {weak} weak',
                f'<div class="stack">{seg(matched, "var(--ok)")}{seg(weak, "var(--warn)")}{seg(missing, "var(--bad)")}</div>')
        else:
            kpi("Skills matched", "layers", "&mdash;", "No recognised skills in the job description", empty=True)
    with k3:
        pct = dash["task_completion"]
        kpi("Roadmap completion", "route", f'{pct:.0f}<small>%</small>', f'Week {plan["current_week"]} of {len(plan["weeks"])} · {dash["tasks_done"]}/{dash["tasks_total"]} tasks', bar(pct))
    with k4:
        if mocks:
            last = mocks[-1]["overall_10"]
            kpi("Interview readiness", "mic", f'{last}<small>/ 10</small>',
                f'Latest of {len(mocks)} interview{"s" if len(mocks) != 1 else ""}', bar(last * 10, score_kind(last * 10)))
        else:
            kpi("Interview readiness", "mic", "Not started", "Take a mock HR interview to measure this", empty=True)

    # ---------------- progress + activity
    l, r = st.columns([1.6, 1], gap="medium")
    with l:
        with card("progress"):
            card_title("Preparation progress", "trend")
            comps = dash["readiness"]["components"]
            rd = dash["readiness"]["score"]
            rd_ring = ring(rd, 118, 10, f"{rd:.0f}", "readiness")
            c1, c2 = st.columns([1, 2.1])
            with c1:
                html(f'<div style="display:flex;flex-direction:column;align-items:center;gap:.4rem;padding-top:.3rem">'
                     f'{rd_ring}'
                     f'<div class="faint" style="font-size:12px;text-align:center">Weighted over the<br>components you have data for</div></div>')
            with c2:
                items = [(COMP_LABEL.get(k, k), v) for k, v in comps.items()]
                cols = ["#8B7CFF"] * len(items)
                charts.show(charts.hbar(items, height=max(150, 52 * len(items))), "ov-comp")
    with r:
        with card("activity"):
            card_title("Recent activity", "clock")
            acts = _activity(dash)
            if not acts:
                html('<div class="faint" style="font-size:13px;padding:.6rem 0">No activity yet. Complete a roadmap task or run an interview.</div>')
            else:
                rows = ""
                for a in acts:
                    ic, kind = ACT_ICON.get(a["kind"], ("check-circle", ""))
                    rows += f'<div class="rowi"><div class="ic {kind}">{icon(ic, 15)}</div><div class="tx">{esc(a["text"])}</div><div class="when">{state.ago(a["ts"])}</div></div>'
                html(f'<div class="rows">{rows}</div>')
                html('<div class="faint" style="font-size:11.5px">Mock interviews come from your saved history; other events are from this browser session.</div>')

    # ---------------- next best actions
    acts = _next_actions(A, dash)
    if acts:
        with card("next"):
            card_title("Recommended next steps", "zap")
            for i, (t, d, page) in enumerate(acts):
                c1, c2 = st.columns([5, 1.1], vertical_alignment="center")
                c1.markdown(minify(f'<div style="font-size:14px;font-weight:550">{esc(t)}</div><div class="faint" style="font-size:12.5px">{esc(d)}</div>'), unsafe_allow_html=True)
                c2.button("Open", key=f"next-{i}", type="secondary", width="stretch", on_click=state.go, args=(page,))
