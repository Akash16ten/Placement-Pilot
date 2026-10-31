"""Plotly charts with one consistent theme. Every figure takes real backend data and returns None if there is nothing to plot."""
from __future__ import annotations

import plotly.graph_objects as go

VIOLET, CYAN, OK, WARN, BAD = "#8B7CFF", "#38BDF8", "#34D399", "#FBBF24", "#FB7185"
MUTED, FAINT, GRID = "#94A3B8", "#64748B", "rgba(148,163,184,0.10)"
FONT = "Inter, ui-sans-serif, system-ui, sans-serif"


def _base(fig: go.Figure, height: int, legend: bool = False, margin=(8, 8, 8, 8)) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=MUTED, size=12), margin=dict(l=margin[0], r=margin[1], t=margin[2], b=margin[3]),
        showlegend=legend, legend=dict(orientation="h", y=1.12, x=0, font=dict(size=12, color=MUTED), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1C263A", bordercolor="rgba(148,163,184,.25)", font=dict(family=FONT, color="#F1F5F9", size=12.5)),
    )
    return fig


def _axes(fig: go.Figure, y_range=None, x_grid=False, y_title=None):
    fig.update_xaxes(showgrid=x_grid, gridcolor=GRID, zeroline=False, linecolor="rgba(148,163,184,.18)", tickfont=dict(color=FAINT, size=11.5))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, range=y_range, tickfont=dict(color=FAINT, size=11.5),
                     title=dict(text=y_title, font=dict(size=11.5, color=FAINT)) if y_title else None)


def hbar(items: list[tuple[str, float]], height: int = 220, max_v: float = 100, colors: list[str] | None = None, suffix: str = "") -> go.Figure | None:
    if not items:
        return None
    labels, vals = [i[0] for i in items][::-1], [i[1] for i in items][::-1]
    cols = (colors or [VIOLET] * len(items))[::-1]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker=dict(color=cols, line=dict(width=0), cornerradius=6),
                           text=[f"{v:.0f}{suffix}" for v in vals], textposition="outside", textfont=dict(color="#F1F5F9", size=12),
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>", cliponaxis=False))
    _base(fig, height, margin=(4, 36, 4, 4))
    fig.update_xaxes(range=[0, max_v], visible=False)
    fig.update_yaxes(showgrid=False, tickfont=dict(color=MUTED, size=12.5), linecolor="rgba(0,0,0,0)")
    fig.update_layout(bargap=0.45)
    return fig


def weekly_progress(weekly: list[dict], height: int = 260) -> go.Figure | None:
    if not weekly:
        return None
    x = [f"W{w['week']}" for w in weekly]
    done = [w["done"] for w in weekly]
    left = [max(0, w["total"] - w["done"]) for w in weekly]
    fig = go.Figure()
    fig.add_bar(x=x, y=done, name="Completed", marker=dict(color=VIOLET, cornerradius=5), hovertemplate="%{x}: %{y} done<extra></extra>")
    fig.add_bar(x=x, y=left, name="Remaining", marker=dict(color="rgba(148,163,184,.22)", cornerradius=5), hovertemplate="%{x}: %{y} remaining<extra></extra>")
    _base(fig, height, legend=True, margin=(4, 4, 28, 4))
    fig.update_layout(barmode="stack", bargap=0.38)
    _axes(fig)
    fig.update_yaxes(dtick=2 if max(w["total"] for w in weekly) > 6 else 1, rangemode="tozero")
    return fig


def hr_trend(history: list[dict], height: int = 250) -> go.Figure | None:
    if not history:
        return None
    x = [f"#{i}" for i in range(1, len(history) + 1)]
    fig = go.Figure()
    fig.add_scatter(x=x, y=[h["overall_10"] for h in history], mode="lines+markers", name="Overall",
                    line=dict(color=VIOLET, width=3, shape="spline", smoothing=.6), marker=dict(size=9, color="#0B1020", line=dict(color=VIOLET, width=2.5)),
                    hovertemplate="Interview %{x}: %{y}/10<extra></extra>", fill="tozeroy", fillcolor="rgba(139,124,255,.08)")
    _base(fig, height, margin=(4, 8, 8, 4))
    _axes(fig, y_range=[0, 10])
    fig.update_xaxes(type="category", range=[-.4, len(history) - .6])
    return fig


def radar(labels: list[str], series: list[tuple[str, list[float], str]], max_v: float, height: int = 280) -> go.Figure | None:
    if len(labels) < 3:
        return None
    fig = go.Figure()
    for name, vals, color in series:
        fig.add_scatterpolar(r=vals + vals[:1], theta=labels + labels[:1], name=name, fill="toself",
                             line=dict(color=color, width=2), fillcolor=_alpha(color, .16),
                             hovertemplate="%{theta}: %{r:.1f}<extra>" + name + "</extra>")
    _base(fig, height, legend=len(series) > 1, margin=(28, 28, 22, 18))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, max_v], showline=False, gridcolor=GRID, tickfont=dict(size=10, color=FAINT), angle=90),
                                 angularaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=12, color=MUTED))))
    return fig


def donut(labels: list[str], values: list[float], colors: list[str], center: str, height: int = 230) -> go.Figure | None:
    if not values or sum(values) == 0:
        return None
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.72, marker=dict(colors=colors, line=dict(color="#161E30", width=3)),
                           textinfo="none", sort=False, domain=dict(x=[0, .66], y=[0, 1]), hovertemplate="%{label}: %{value}<extra></extra>"))
    _base(fig, height, legend=True, margin=(4, 4, 4, 4))
    fig.update_layout(legend=dict(orientation="v", x=1.0, y=.5, font=dict(size=12, color=MUTED)),
                      annotations=[dict(text=f"<b>{center}</b>", x=.33, y=.5, showarrow=False, font=dict(size=22, color="#F1F5F9", family=FONT))])
    return fig


def _alpha(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def show(fig: go.Figure | None, key: str, fallback=None):
    import streamlit as st
    if fig is None:
        if fallback:
            fallback()
        return
    st.plotly_chart(fig, key=key, width="stretch", config={"displayModeBar": False, "responsive": True})
