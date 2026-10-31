"""Learning Roadmap: a week-by-week timeline with task tracking and adaptive re-planning."""
import streamlit as st

import api
import data
import state
from insight import priority_of_skill
from state import ss
from ui import badge, bar, card, card_title, empty_state, esc, html, icon, notice, page_header, ring, toast_err, toast_ok

TYPE_KIND = {"learn": "violet", "practice": "cyan", "project": "ok", "interview": "warn", "resume": ""}


def _toggle(sid: str, task_id: str, key: str):
    try:
        api.set_task(sid, task_id, bool(ss[key]))
        state.bump()
        if ss[key]:
            state.log("task", "Completed a roadmap task")
    except api.ApiError as e:
        toast_err(str(e))


def _adapt(sid: str):
    try:
        ss.adapt_changes = api.adapt(sid)["changes"]
        state.bump()
        state.log("adapt", "Adapted roadmap from progress and results")
        toast_ok("Roadmap adapted.")
    except api.ApiError as e:
        toast_err(str(e))


def _flags(t: dict) -> tuple[bool, bool]:
    title = t["title"]
    return title.startswith("[Carried over]"), bool(t.get("adaptive")) or title.startswith("Revisit")


def render():
    page_header("Learning Roadmap", "Your week-by-week plan",
                "Tick tasks off as you finish them. Adapt the plan when you fall behind or after a mock interview.")
    A, sid = ss.analysis, state.sid()
    if not A:
        empty_state("route", "No roadmap yet", "Your roadmap is generated from your skill gaps after you analyze a resume.")
        st.button("Go to Resume Analyzer", key="rm-cta", type="primary", on_click=state.new_analysis)
        return
    plan, dash = data.plan(sid, ss.rev), data.dash(sid, ss.rev)
    if not plan or not dash:
        notice("warn", "Could not load your roadmap from the backend. Try again in a moment.")
        return

    weeks = plan["weeks"]
    cur = plan["current_week"]
    done, total = dash["tasks_done"], dash["tasks_total"]
    pct = dash["task_completion"]

    # ---- summary + adapt
    l, r = st.columns([2.2, 1], gap="medium")
    with l:
        with card("rm-sum"):
            c1, c2 = st.columns([1, 3], vertical_alignment="center")
            c1.markdown(f'<div style="display:flex;justify-content:center">{ring(pct, 104, 9, f"{pct:.0f}%", "done")}</div>', unsafe_allow_html=True)
            with c2:
                html(f'<div class="h2" style="font-size:17px">{esc(plan["summary"])}</div>'
                     f'<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0">{badge(f"{done}/{total} tasks", "violet")}{badge(f"Week {cur} of {len(weeks)}")}</div>'
                     '<div class="legend"><span style="--c:var(--ok)">Completed</span><span style="--c:var(--violet)">In progress</span>'
                     '<span style="--c:var(--warn)">Needs revisit / carried over</span><span style="--c:rgba(148,163,184,.4)">Upcoming</span></div>')
    with r:
        with card("rm-adapt"):
            card_title("Adaptive planning", "refresh")
            html('<div class="faint" style="font-size:12.5px;line-height:1.55">Carries over unfinished tasks, adds practice for weak interview dimensions and revisits coding topics you found hard.</div>')
            st.button("Adapt my plan", key="rm-adapt-btn", icon=":material/auto_fix_high:", type="primary", width="stretch", on_click=_adapt, args=(sid,))

    if ss.adapt_changes:
        with card("rm-changes"):
            card_title("Latest adaptation", "sparkle")
            html('<div class="rows">' + "".join(f'<div class="rowi"><div class="ic warn">{icon("refresh", 14)}</div><div class="tx">{esc(c)}</div></div>' for c in ss.adapt_changes) + '</div>')
    if plan["adaptations"]:
        with st.expander(f"Adaptation history ({len(plan['adaptations'])})"):
            html('<div class="rows">' + "".join(f'<div class="rowi"><div class="ic">{icon("refresh", 14)}</div><div class="tx">{esc(c)}</div></div>' for c in plan["adaptations"][::-1]) + '</div>')

    # ---- timeline
    html('<div style="height:.4rem"></div>')
    for idx, w in enumerate(weeks):
        n = len(w["tasks"])
        wdone = sum(1 for t in w["tasks"] if t["done"])
        status = "done" if (n and wdone == n) else "now" if w["week"] == cur else "todo"
        last = " st-key-wk-last" if idx == len(weeks) - 1 else ""
        with st.container(key=f"wk-{w['week']}-s-{status}"):
            if idx == len(weeks) - 1:
                html('<style>.st-key-wk-' + str(w["week"]) + '-s-' + status + '::before{display:none}</style>')
            tag = {"done": badge("Completed", "ok"), "now": badge("Current week", "violet"), "todo": badge("Upcoming")}[status]
            html(f'<div class="wk-head"><div><div class="faint" style="font-size:11.5px;font-weight:600;letter-spacing:.08em">WEEK {w["week"]}</div>'
                 f'<div class="wk-title">{esc(w["theme"])}</div></div><div style="display:flex;flex-direction:column;align-items:flex-end;gap:.4rem;min-width:130px">{tag}'
                 f'<div style="width:130px">{bar(w["completion"], "ok" if status == "done" else "grad", 5)}</div><div class="faint num" style="font-size:11.5px">{wdone}/{n} tasks · {w["completion"]}%</div></div></div>')
            if w.get("goals"):
                html('<div class="faint" style="font-size:11.5px;font-weight:600;letter-spacing:.08em;margin-top:.2rem">LEARNING OBJECTIVES</div>'
                     + "".join(f'<div class="goal">{icon("flag", 14)}<span>{esc(g)}</span></div>' for g in w["goals"]))
            html('<div class="faint" style="font-size:11.5px;font-weight:600;letter-spacing:.08em;margin-top:.3rem">TASKS</div>')
            for t in w["tasks"]:
                carried, revisit = _flags(t)
                c1, c2 = st.columns([1.9, 1.15], vertical_alignment="center")
                key = f"task_{sid}_{t['id']}"
                title = t["title"].replace("[Carried over] ", "")
                c1.checkbox(title, value=t["done"], key=key, on_change=_toggle, args=(sid, t["id"], key))
                prio = priority_of_skill(t.get("skill", ""), A["skills"])
                p_html = ""
                if prio in ("high", "med") and not t["done"]:
                    p_html = f'<span class="prio {prio}"><i></i>{"High" if prio == "high" else "Medium"}</span>'
                chips = badge(t["type"].title(), TYPE_KIND.get(t["type"], ""))
                if t.get("skill") and t["skill"] not in ("resume", "mock", "communication"):
                    chips += badge(t["skill"])
                if revisit:
                    chips += badge("Revisit", "warn")
                if carried:
                    chips += badge("Carried over", "warn")
                chips += f'<span class="faint num" style="font-size:11.5px">{t.get("est_hours", "?")}h</span>'
                c2.markdown(f'<div class="task-meta">{p_html}{chips}</div>', unsafe_allow_html=True)
                if t.get("resource"):
                    html(f'<div class="res">{icon("book", 12)} {esc(t["resource"])}</div>')
