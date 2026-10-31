"""Session state, navigation and the small activity log. Single source of truth for st.session_state keys."""
from __future__ import annotations

import time

import streamlit as st

import api

ss = st.session_state

# (key, label, material icon used by the sidebar button)
PAGES = [
    ("overview", "Overview", ":material/dashboard:"),
    ("analyzer", "Resume Analyzer", ":material/description:"),
    ("skills", "Skill Gap Analysis", ":material/track_changes:"),
    ("prep", "Interview Preparation", ":material/quiz:"),
    ("mock", "Mock HR Interview", ":material/mic:"),
    ("roadmap", "Learning Roadmap", ":material/route:"),
    ("analytics", "Progress & Analytics", ":material/monitoring:"),
]
PAGE_KEYS = [p[0] for p in PAGES]
PAGE_LABEL = {k: l for k, l, _ in PAGES}

DEFAULTS = {
    "page": "overview",
    "analysis": None,       # response of POST /resume/analyze (or GET /resume/{id})
    "rev": 0,               # bumped after every mutation so cached GETs refresh
    "activity": [],         # in-session events [{ts, kind, text}]
    "an_view": "form",      # analyzer: form | results
    "iv": None,             # live interview {id,total,qnum,question,kind,history,last}
    "report": None,         # final HR report
    "report_hist": [],      # answers given in the interview that produced `report`
    "adapt_changes": None,  # last result of POST /plan/{id}/adapt
    "f_company": "", "f_role": "Software Engineer", "f_weeks": 6, "f_jd": "", "f_text": "", "f_mode": "Upload PDF",
    "f_pdf": None,          # (name, bytes) kept across page switches
    "restore_tried": False,
}


def init() -> None:
    for k, v in DEFAULTS.items():
        ss.setdefault(k, v)
    qp = st.query_params
    if not ss.restore_tried:
        ss.restore_tried = True
        sid = qp.get("sid")
        if sid and not ss.analysis:
            try:
                ss.analysis = api.get_analysis(sid)
                ss.an_view = "results"
            except api.ApiError:
                qp.pop("sid", None)  # stale / deleted session
    if ss.analysis and qp.get("sid") != ss.analysis["session_id"]:
        qp["sid"] = ss.analysis["session_id"]


def go(page: str) -> None:
    """on_click callback: request navigation. The shell performs st.switch_page, which pushes a real browser-history entry."""
    ss.nav_to = page


def bump() -> None:
    ss.rev += 1


def log(kind: str, text: str) -> None:
    ss.activity.insert(0, {"ts": time.time(), "kind": kind, "text": text})
    del ss.activity[40:]


def sid() -> str | None:
    return ss.analysis["session_id"] if ss.analysis else None


def new_analysis() -> None:
    """on_click: open the analyzer on a fresh form."""
    ss.an_view = "form"
    ss.pop("w_an_view", None)
    ss.nav_to = "analyzer"


def reset_all() -> None:
    for k in [k for k in ss.keys() if str(k).startswith(("w_", "task_", "hint", "rate"))]:
        del ss[k]
    for k, v in DEFAULTS.items():
        ss[k] = v
    ss.restore_tried = True
    st.query_params.pop("sid", None)


def ago(ts: float) -> str:
    d = max(0, time.time() - ts)
    if d < 60: return "just now"
    if d < 3600: return f"{int(d // 60)} min ago"
    if d < 86400: return f"{int(d // 3600)} h ago"
    return f"{int(d // 86400)} d ago"


def sticky(widget, name: str, label: str, **kw):
    """Widget whose value survives page switches (Streamlit drops state of un-rendered widgets).
    The real value lives in ss[name]; the widget key is `w_<name>`."""
    wkey = f"w_{name}"

    def _sync():
        ss[name] = ss[wkey]

    return widget(label, value=ss[name], key=wkey, on_change=_sync, **kw)
