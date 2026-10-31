"""Skill Gap Analysis: what the job needs vs what your resume shows, and what to learn first."""
import streamlit as st

import charts
import data
import state
from insight import CAT_LABEL, by_category, gap_priorities, tasks_by_skill
from state import ss
from ui import badge, bar, card, card_title, chip, empty_state, esc, html, icon, page_header, ring, score_kind

PRIO = {"high": ("High priority", "bad"), "med": ("Medium", "warn"), "low": ("Low", ""), "reinforce": ("Reinforce", "warn")}


def render():
    page_header("Skill Gap Analysis", "What to learn first",
                "Your resume skills compared with what the job description requires, ranked by how much each gap matters.")
    A = ss.analysis
    if not A:
        empty_state("layers", "No analysis yet", "Analyze a resume and job description to see which required skills you already show and which you are missing.")
        st.button("Go to Resume Analyzer", key="sk-cta", type="primary", on_click=state.new_analysis)
        return

    sk = A["skills"]
    matched, weak, missing = len(sk["matched"]), len(sk["weak"]), len(sk["missing"])
    required = matched + weak + missing
    if required == 0:
        empty_state("info", "No recognised skills in the job description",
                    "The job description did not mention any skills from PlacementPilot's skill list, so there is nothing to compare. Try pasting the full description including its requirements section.")
        return
    plan = data.plan(state.sid(), ss.rev)
    by_skill = tasks_by_skill(plan)
    cover = matched / required * 100

    # ---- summary strip
    l, r = st.columns([1, 2.2], gap="medium")
    with l:
        with card("cover"):
            card_title("Requirement coverage", "target")
            c = ring(cover, 132, 11, f"{cover:.0f}%", "covered")
            html(f'<div style="display:flex;justify-content:center;padding:.3rem 0">{c}</div>'
                 f'<div class="faint" style="font-size:12.5px;text-align:center">{matched} of {required} required skills found on your resume</div>')
    with r:
        with card("legend"):
            card_title("Where you stand", "layers")
            seg = lambda n, col: f'<i style="width:{n / required * 100:.1f}%;background:{col}"></i>' if n else ""
            tile = lambda n, label, col, hint: (f'<div style="flex:1;min-width:120px;padding:.7rem .85rem;border:1px solid var(--line);border-radius:12px;background:var(--inset)">'
                                                 f'<div style="display:flex;align-items:center;gap:.4rem;font-size:12px;color:var(--muted)"><span style="width:8px;height:8px;border-radius:3px;background:{col}"></span>{label}</div>'
                                                 f'<div class="big" style="font-size:26px;margin-top:.35rem">{n}</div><div class="faint" style="font-size:11.5px;margin-top:2px">{hint}</div></div>')
            html(f'<div class="stack" style="height:10px">{seg(matched, "var(--ok)")}{seg(weak, "var(--warn)")}{seg(missing, "var(--bad)")}</div>'
                 f'<div style="display:flex;gap:.7rem;flex-wrap:wrap;margin-top:.4rem">'
                 f'{tile(matched, "Matched", "var(--ok)", "On your resume")}{tile(weak, "Weak evidence", "var(--warn)", "Related, not explicit")}'
                 f'{tile(missing, "Missing", "var(--bad)", "Not on your resume")}{tile(len(sk["extra"]), "Extra", "var(--faint)", "Resume only")}</div>')

    # ---- priority list
    gaps = gap_priorities(sk)
    with card("prio"):
        card_title("Learn these first", "flag")
        if not gaps:
            html('<div class="notice ok"><div>You cover every skill the job description asks for. Focus on interview practice next.</div></div>')
        else:
            html('<div class="faint" style="font-size:12.5px;margin-top:-.3rem">Ranked by how often the job description mentions each skill. High priority means mentioned 2+ times or among your top 3 gaps.</div>')
            rows = ""
            for i, g in enumerate(gaps, 1):
                label, kind = PRIO[g["priority"]]
                tasks = by_skill.get(g["skill"], [])
                road = (f'<span class="badge violet">{len(tasks)} roadmap task{"s" if len(tasks) != 1 else ""}</span>' if tasks
                        else '<span class="badge">Not in roadmap</span>')
                demand = "".join(f'<i style="display:inline-block;width:14px;height:5px;border-radius:3px;margin-right:2px;background:{"var(--violet)" if k < min(g["jd_mentions"], 4) else "rgba(148,163,184,.2)"}"></i>' for k in range(4))
                rows += (f'<div class="rowi" style="align-items:center"><div class="q-num" style="margin:0">{i}</div>'
                         f'<div class="tx" style="font-weight:600;font-size:14.5px">{esc(g["skill"])}<small>{esc(CAT_LABEL.get(g["category"], g["category"]))} · {"related content found, not explicit" if g["state"] == "weak" else "absent from your resume"}</small></div>'
                         f'<div class="gapmeta">'
                         f'<span title="Mentioned {g["jd_mentions"]}x in the job description" style="display:inline-flex;align-items:center;gap:.4rem;font-size:11.5px;color:var(--faint)">{demand}JD ×{g["jd_mentions"]}</span>'
                         f'{road}{badge(label, kind)}</div></div>')
            html(f'<div class="rows">{rows}</div>')

    # ---- by category
    cats = by_category(sk)
    labels, cov = [], []
    for k, v in cats.items():
        total = len(v["matched"]) + len(v["weak"]) + len(v["missing"])
        labels.append(CAT_LABEL.get(k, k)); cov.append(len(v["matched"]) / total * 100 if total else 0)
    l, r = st.columns([1, 1.6], gap="medium")
    with l:
        with card("radar"):
            card_title("Coverage by area", "chart")
            fig = (charts.radar(labels, [("Your coverage", cov, charts.VIOLET)], 100, 290) if len(labels) >= 3
                   else charts.hbar(list(zip(labels, cov)), 120 + 50 * len(labels), 100, suffix="%"))
            charts.show(fig, "sk-radar")
    with r:
        with card("cats"):
            card_title("Skills by area", "layers")
            for k, v in sorted(cats.items(), key=lambda kv: -len(kv[1]["missing"])):
                total = len(v["matched"]) + len(v["weak"]) + len(v["missing"])
                pct = len(v["matched"]) / total * 100
                chips = ("".join(chip(s, "ok") for s in v["matched"]) + "".join(chip(s, "warn") for s in v["weak"]) + "".join(chip(s, "bad") for s in v["missing"]))
                html(f'<div style="padding:.55rem 0;border-top:1px solid var(--line)"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem">'
                     f'<b style="font-size:13.5px">{esc(CAT_LABEL.get(k, k))}</b><span class="faint num" style="font-size:12px">{len(v["matched"])}/{total} covered</span></div>'
                     f'{bar(pct, score_kind(pct), 5)}<div style="margin-top:.55rem">{chips}</div></div>')
            html('<div class="legend" style="margin-top:.2rem"><span style="--c:var(--ok)">Matched</span><span style="--c:var(--warn)">Weak evidence</span><span style="--c:var(--bad)">Missing</span></div>')

    if sk["extra"]:
        with st.expander(f"Skills on your resume that this job did not ask for ({len(sk['extra'])})"):
            html("".join(chip(s, "mute") for s in sk["extra"]))
    c1, c2, _ = st.columns([1.2, 1.2, 3])
    c1.button("Practice these skills", key="sk-prep", icon=":material/quiz:", type="secondary", width="stretch", on_click=state.go, args=("prep",))
    c2.button("See roadmap", key="sk-road", icon=":material/route:", type="secondary", width="stretch", on_click=state.go, args=("roadmap",))
