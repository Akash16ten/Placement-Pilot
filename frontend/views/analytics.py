"""Progress & Analytics: every number and chart here comes from the backend's progress/plan endpoints."""
import streamlit as st

import charts
import data
import state
from insight import tasks_by_skill
from state import ss
from ui import badge, bar, card, card_title, empty_state, esc, html, icon, kpi, notice, page_header, ring, score_kind

COMP_LABEL = {"resume_ats": "Resume (ATS)", "roadmap_completion": "Roadmap", "mock_hr": "Mock HR", "coding_practice": "Coding"}
DIM_LABEL = {"clarity": "Clarity", "structure": "Structure", "impact": "Impact", "relevance": "Relevance"}
RATING_LABEL = {"easy": "Easy", "ok": "Solved", "hard": "Hard", "failed": "Couldn't solve"}
RATING_COLOR = {"easy": charts.OK, "ok": charts.CYAN, "hard": charts.WARN, "failed": charts.BAD}


def _attention(A, dash, plan) -> list[tuple[str, str, str]]:
    """(kind, title, detail). Derived only from real data; empty list means nothing needs attention."""
    out = []
    if dash["mock_hr_history"]:
        dims = dash["mock_hr_history"][-1]["dims"]
        if dims:
            weakest = min(dims, key=dims.get)
            if dims[weakest] < 6:
                out.append(("bad", f"Interview {DIM_LABEL.get(weakest, weakest).lower()} is low ({dims[weakest]}/10)", "Your latest mock interview scored lowest here. Run Adapt on the roadmap to add practice."))
    topics: dict[str, int] = {}
    for c in dash["coding"]["log"]:
        if c.get("rating") in ("hard", "failed"):
            for t in c.get("topics", []):
                topics[t] = topics.get(t, 0) + 1
    for t, n in sorted(topics.items(), key=lambda x: -x[1])[:2]:
        out.append(("warn", f"Coding topic needs work: {t}", f"You rated {n} problem{'s' if n != 1 else ''} on this topic as hard or unsolved."))
    cur = plan["current_week"]
    behind = [w for w in plan["weeks"] if w["week"] < cur and w["completion"] < 100]
    if behind:
        out.append(("warn", f"{len(behind)} earlier week{'s have' if len(behind) != 1 else ' has'} unfinished tasks", "Use Adapt my plan to carry them over."))
    gaps = [m["skill"] for m in A["skills"]["missing"][:3]]
    by = tasks_by_skill(plan)
    uncovered = [g for g in gaps if not any(t["done"] for t in by.get(g, []))]
    if uncovered:
        out.append(("bad", "Top skill gaps without progress: " + ", ".join(uncovered), "No completed roadmap task covers these yet."))
    return out


def render():
    page_header("Progress & Analytics", "How your preparation is going", "Live metrics from your roadmap, mock interviews and coding practice.")
    A, sid = ss.analysis, state.sid()
    if not A:
        empty_state("chart", "No data to analyze yet", "Analytics appear after you analyze a resume and start working through the roadmap, interviews and coding problems.")
        st.button("Go to Resume Analyzer", key="an-cta", type="primary", on_click=state.new_analysis)
        return
    dash, plan = data.dash(sid, ss.rev), data.plan(sid, ss.rev)
    if not dash or not plan:
        notice("warn", "Could not load analytics from the backend. Try again in a moment.")
        return

    rd = dash["readiness"]
    hr, coding = dash["mock_hr_history"], dash["coding"]
    # ---- KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Placement readiness", "target", f'{rd["score"]:.0f}<small>/ 100</small>', "Weighted over components with data", bar(rd["score"], score_kind(rd["score"])))
    with k2:
        kpi("Tasks completed", "check-circle", f'{dash["tasks_done"]}<small>/ {dash["tasks_total"]}</small>', f'{dash["task_completion"]:.0f}% of your roadmap', bar(dash["task_completion"]))
    with k3:
        if hr:
            kpi("Mock interview", "mic", f'{hr[-1]["overall_10"]}<small>/ 10</small>', f'{len(hr)} interview{"s" if len(hr) != 1 else ""} completed')
        else:
            kpi("Mock interview", "mic", "&mdash;", "No interviews completed yet", empty=True)
    with k4:
        if coding["attempted"]:
            kpi("Coding practice", "code", f'{coding["solved"]}<small>/ {coding["attempted"]} solved</small>', "From attempts you logged")
        else:
            kpi("Coding practice", "code", "&mdash;", "No attempts logged yet", empty=True)

    # ---- weekly + readiness
    l, r = st.columns([1.5, 1], gap="medium")
    with l:
        with card("an-week"):
            card_title("Weekly learning progress", "chart")
            charts.show(charts.weekly_progress(dash["weekly"]), "an-weekly")
    with r:
        with card("an-comp"):
            card_title("Readiness components", "layers")
            items = [(COMP_LABEL.get(k, k), v) for k, v in rd["components"].items()]
            charts.show(charts.hbar(items, height=max(170, 56 * len(items))), "an-comps")
            html('<div class="faint" style="font-size:12px">Each component enters the score once it has data. ATS 25%, roadmap 35%, mock HR 25%, coding 15%, renormalised.</div>')

    # ---- interviews + coding
    l, r = st.columns(2, gap="medium")
    with l:
        with card("an-hr"):
            card_title("Mock interview scores", "mic")
            if not hr:
                empty_state("mic", "No interviews yet", "Complete a mock HR interview to see your score trend and dimension breakdown.")
                st.button("Start an interview", key="an-iv", type="secondary", on_click=state.go, args=("mock",))
            else:
                charts.show(charts.hr_trend(hr), "an-hr-trend")
                dims = hr[-1]["dims"]
                if dims:
                    labels = [DIM_LABEL.get(k, k) for k in dims]
                    series = [("Latest", list(dims.values()), charts.VIOLET)]
                    if len(hr) > 1 and hr[0]["dims"]:
                        series.insert(0, ("First", [hr[0]["dims"].get(k, 0) for k in dims], charts.CYAN))
                    html('<div class="faint" style="font-size:12px;margin-top:.2rem">Dimension scores (0–10)</div>')
                    charts.show(charts.radar(labels, series, 10, 250), "an-hr-radar")
    with r:
        with card("an-code"):
            card_title("Coding practice performance", "code")
            if not coding["attempted"]:
                empty_state("code", "No attempts logged", "Log how each coding problem went in Interview Preparation. This chart and your roadmap adapt to it.")
                st.button("Open coding questions", key="an-cq", type="secondary", on_click=state.go, args=("prep",))
            else:
                counts: dict[str, int] = {}
                for c in coding["log"]:
                    counts[c["rating"]] = counts.get(c["rating"], 0) + 1
                order = [k for k in ("easy", "ok", "hard", "failed") if k in counts]
                charts.show(charts.donut([RATING_LABEL[k] for k in order], [counts[k] for k in order], [RATING_COLOR[k] for k in order], f'{coding["solved"]}/{coding["attempted"]}', 230), "an-code-donut")
                mins = [c["minutes"] for c in coding["log"] if c.get("minutes")]
                if mins:
                    html(f'<div class="faint" style="font-size:12.5px">Average logged time: <b style="color:var(--text)">{sum(mins) / len(mins):.0f} min</b></div>')
                rows = "".join(f'<div class="rowi"><div class="tx">{esc(c["title"])}<small>{esc(", ".join(c.get("topics", [])))}</small></div>{badge(RATING_LABEL[c["rating"]], "ok" if c["rating"] in ("easy", "ok") else "warn" if c["rating"] == "hard" else "bad")}</div>' for c in coding["log"][::-1][:6])
                html(f'<div class="rows">{rows}</div>')

    # ---- skill progress + attention
    l, r = st.columns([1.5, 1], gap="medium")
    with l:
        with card("an-skill"):
            card_title("Skill progress through your roadmap", "trend")
            by = tasks_by_skill(plan)
            items = []
            for skill, tasks in by.items():
                if skill and skill not in ("resume", "mock", "communication") and tasks:
                    items.append((skill, sum(1 for t in tasks if t["done"]) / len(tasks) * 100, len(tasks)))
            if not items:
                html('<div class="faint" style="font-size:13px">No skill-tagged tasks in your roadmap.</div>')
            else:
                items.sort(key=lambda x: (-x[1], -x[2]))
                charts.show(charts.hbar([(f"{s}  ({n})", p) for s, p, n in items[:8]], max(180, 42 * min(len(items), 8)), 100, suffix="%"), "an-skills")
                html('<div class="faint" style="font-size:12px">Share of roadmap tasks completed per skill (task count in brackets). Tracks learning effort, not tested proficiency.</div>')
    with r:
        with card("an-attn"):
            card_title("Areas requiring attention", "alert")
            att = _attention(A, dash, plan)
            if not att:
                notice("ok", "Nothing is flagged right now. Keep going through your roadmap.")
            else:
                html('<div class="rows">' + "".join(f'<div class="rowi"><div class="ic {k}">{icon("alert", 14)}</div><div class="tx">{esc(t)}<small>{esc(d)}</small></div></div>' for k, t, d in att) + '</div>')
