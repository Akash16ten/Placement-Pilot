"""Reusable UI primitives. All of them render real data passed in by the views, nothing is hardcoded."""
from __future__ import annotations

import html as _html
import itertools

import streamlit as st

_uid = itertools.count(1)

# --- Lucide-style 24px stroke icons (inline SVG so they inherit currentColor) -------------
_P = {
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "upload": '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
    "alert": '<path d="M12 3.5L2.8 19.5h18.4z"/><path d="M12 10v4M12 17.2v.3"/>',
    "x-circle": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.7v.3"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 17v4M17 19h4"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "chevron": '<path d="M9 6l6 6-6 6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "code": '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
    "building": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h2M13 8h2M9 12h2M13 12h2M10 21v-4h4v4"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
    "route": '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5"/>',
    "zap": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>',
    "flag": '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "message": '<path d="M4 5h16v11H9l-5 4z"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>',
    "send": '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
    "logo": '<path d="M12 3.2l6.2 15.3L12 15.3 5.8 18.5z" fill="currentColor" stroke="none" opacity=".95"/>',
}


def icon(name: str, size: int = 16, stroke: float = 1.8, style: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="flex:none;{style}">{_P[name]}</svg>')


def esc(x) -> str:
    return _html.escape(str(x if x is not None else ""))


def minify(s: str) -> str:
    """Markdown treats indented/blank-line-separated HTML as code. Collapse to one line."""
    return "".join(line.strip() for line in s.strip().splitlines())


def html(s: str) -> None:
    st.markdown(minify(s), unsafe_allow_html=True)


def card(key: str):
    """Bordered surface. The key becomes a CSS class (st-key-card-*) so styling is stable."""
    return st.container(key=f"card-{key}")


def panel(key: str):
    return st.container(key=f"panel-{key}")


# --- small components ---------------------------------------------------------------------
def badge(text: str, kind: str = "") -> str:
    return f'<span class="badge {kind}">{esc(text)}</span>'


def chip(text: str, kind: str = "") -> str:
    return f'<span class="chip {kind}">{esc(text)}</span>'


def card_title(text: str, ic: str | None = None) -> None:
    html(f'<div class="card-title">{icon(ic, 15) if ic else ""}{esc(text)}</div>')


def page_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    html(f'<div style="margin-bottom:.9rem"><div class="eyebrow">{esc(eyebrow)}</div>'
         f'<div class="h1">{esc(title)}</div>' + (f'<div class="sub">{esc(subtitle)}</div>' if subtitle else "") + '</div>')


def section_title(text: str, hint: str = "") -> None:
    html(f'<div style="display:flex;align-items:baseline;justify-content:space-between;margin:.6rem 0 .1rem">'
         f'<div class="h2">{esc(text)}</div><div class="faint" style="font-size:12.5px">{esc(hint)}</div></div>')


def notice(kind: str, text: str) -> None:
    ic = {"ok": "check-circle", "warn": "alert", "bad": "x-circle", "info": "info"}[kind]
    html(f'<div class="notice {kind}">{icon(ic, 18)}<div>{text}</div></div>')


def empty_state(ic: str, title: str, text: str) -> None:
    html(f'<div class="empty"><div class="ico">{icon(ic, 22)}</div><div class="t">{esc(title)}</div><div class="d">{esc(text)}</div></div>')


def bar(pct: float, kind: str = "grad", height: int | None = None) -> str:
    pct = max(0, min(100, pct or 0))
    st_ = f' style="height:{height}px"' if height else ""
    return f'<div class="bar {kind}"{st_}><i style="width:{pct:.1f}%"></i></div>'


def score_kind(pct: float) -> str:
    return "ok" if pct >= 70 else "warn" if pct >= 45 else "bad"


def ring(value: float, size: int = 140, thickness: int = 10, center: str | None = None, sub: str = "", maxv: float = 100,
         color: str | None = None) -> str:
    """SVG circular progress. Violet->sky gradient stroke unless a semantic colour is passed."""
    pct = max(0.0, min(1.0, (value or 0) / maxv))
    r = (size - thickness) / 2
    c = 2 * 3.14159265 * r
    gid = f"rg{next(_uid)}"
    stroke = f"url(#{gid})" if not color else color
    center = center if center is not None else f"{value:.0f}"
    fs = size * 0.27
    return (f'<div style="position:relative;width:{size}px;height:{size}px;flex:none">'
            f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="transform:rotate(-90deg)">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8B7CFF"/><stop offset="1" stop-color="#7DD3FC"/></linearGradient></defs>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="rgba(148,163,184,.14)" stroke-width="{thickness}"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{stroke}" stroke-width="{thickness}" stroke-linecap="round" '
            f'stroke-dasharray="{c*pct:.2f} {c:.2f}"/></svg>'
            f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">'
            f'<div class="num" style="font-size:{fs:.0f}px;font-weight:700;line-height:1">{center}</div>'
            + (f'<div style="font-size:11.5px;color:var(--faint);margin-top:4px">{esc(sub)}</div>' if sub else "") +
            '</div></div>')


def kpi(label: str, ic: str, value_html: str, foot_html: str = "", extra_html: str = "", empty: bool = False):
    """One KPI card (rendered inside a keyed container so it gets the card surface)."""
    with st.container(key=f"{'card-kpiempty-' if empty else 'card-kpi-'}{next(_uid)}"):
        html(f'<div class="kpi-label">{icon(ic, 15, style="color:var(--violet)")}{esc(label)}</div>'
             f'<div class="big {"kpi-empty" if empty else ""}">{value_html}</div>' + extra_html +
             (f'<div class="kpi-foot">{foot_html}</div>' if foot_html else ""))


def loader(title: str, steps: list[str]):
    """Returns the HTML for an animated loading card (put it in an st.empty placeholder)."""
    li = "".join(f"<li>{esc(s)}</li>" for s in steps)
    return minify(f'<div class="loader"><div class="spin"></div><div><div style="font-weight:620;font-size:15px">{esc(title)}</div>'
                  f'<div class="faint" style="font-size:12.5px;margin-top:2px">This usually takes a few seconds. LLM calls can take longer.</div><ol>{li}</ol></div></div>')


def toast_ok(msg: str):
    st.toast(msg, icon=":material/check_circle:")


def toast_err(msg: str):
    st.toast(msg, icon=":material/error:")
