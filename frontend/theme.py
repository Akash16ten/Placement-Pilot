"""Global design system: tokens + CSS injected once per run.

Design principles
  * Violet is the only brand accent. Cyan is reserved for the active/selected highlight.
  * Surfaces are separated by 1px hairline borders, not shadows.
  * Everything numeric uses tabular figures so dashboards do not jitter.
"""
import streamlit as st

TOKENS = {
    "bg": "#0B1020", "bg2": "#111827", "card": "#161E30", "elev": "#1C263A",
    "violet": "#8B7CFF", "cyan": "#38BDF8", "ok": "#34D399", "warn": "#FBBF24", "bad": "#FB7185",
    "text": "#F1F5F9", "muted": "#94A3B8", "faint": "#64748B",
    "line": "rgba(148,163,184,0.12)", "line2": "rgba(148,163,184,0.22)",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&display=swap');
:root{
  --bg:#0B1020; --bg2:#111827; --card:#161E30; --elev:#1C263A; --inset:#0F1629;
  --violet:#8B7CFF; --violet-d:#6D5EF0; --cyan:#38BDF8; --ok:#34D399; --warn:#FBBF24; --bad:#FB7185;
  --text:#F1F5F9; --muted:#94A3B8; --faint:#64748B;
  --line:rgba(148,163,184,.12); --line2:rgba(148,163,184,.22);
  --r:14px; --r-sm:10px;
}
.stApp, button, input, textarea, select{font-family:'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif !important;}
.stApp{
  background:
    radial-gradient(900px 420px at 82% -10%, rgba(139,124,255,.11), transparent 60%),
    radial-gradient(640px 320px at -5% 0%, rgba(56,189,248,.045), transparent 60%),
    var(--bg);
  color:var(--text); font-feature-settings:'cv11','ss01'; -webkit-font-smoothing:antialiased;
}
::selection{background:rgba(139,124,255,.35)}
*{scrollbar-width:thin; scrollbar-color:rgba(148,163,184,.25) transparent}

/* ---- chrome we do not want ---- */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"]{display:none !important}
header[data-testid="stHeader"]{background:transparent !important; height:2.4rem}
[data-testid="stMainBlockContainer"], .block-container{padding:.4rem 2.2rem 4rem !important; max-width:1260px}
[data-testid="stVerticalBlock"]{gap:.9rem}
h1,h2,h3,h4{letter-spacing:-.02em; font-weight:650; color:var(--text)}
p, li, label{color:var(--text)}
a{color:var(--violet)}
hr{border-color:var(--line) !important}

/* ---- sidebar ---- */
section[data-testid="stSidebar"]{background:#0D1324; border-right:1px solid var(--line)}
section[data-testid="stSidebar"][aria-expanded="true"]{width:236px !important; min-width:236px !important; max-width:236px !important}
[data-testid="stSidebarHeader"]{padding:.5rem .6rem 0 .6rem; height:2.4rem; min-height:0}
[data-testid="stSidebarContent"] > div{padding-top:0}
[data-testid="stSidebarUserContent"]{padding:0 .85rem 1rem}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.25rem}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]{width:100%}
section[data-testid="stSidebar"] .stButton{margin:0}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a, section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]{
  display:flex; align-items:center; gap:.65rem; height:38px; padding:0 .75rem; border-radius:10px; border:1px solid transparent;
  color:var(--muted); text-decoration:none; transition:background .15s,color .15s,border-color .15s}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p{font-size:13.5px; font-weight:500; color:inherit; margin:0}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"]{font-size:19px}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover{background:rgba(148,163,184,.07); color:var(--text)}
section[data-testid="stSidebar"] .st-key-navactive a[data-testid="stPageLink-NavLink"]{
  background:linear-gradient(90deg, rgba(139,124,255,.18), rgba(139,124,255,.06)); color:var(--text); border-color:rgba(139,124,255,.30)}
section[data-testid="stSidebar"] .st-key-navactive [data-testid="stIconMaterial"]{color:var(--cyan)}
section[data-testid="stSidebar"] .stButton button{width:100%; justify-content:flex-start; height:34px; padding:0 .75rem; gap:.65rem; border-radius:10px;
  border:1px solid transparent; background:transparent; color:var(--faint); font-size:12.5px; box-shadow:none}
section[data-testid="stSidebar"] .st-key-side-danger button:hover{color:var(--bad); background:rgba(251,113,133,.08)}
/* status markers pinned to the right of a nav item (absolute, so they never change layout) */
section[data-testid="stSidebar"] [class*="st-key-nav"]{position:relative}
section[data-testid="stSidebar"] [class*="st-key-nav"] [data-testid="stElementContainer"]:has(.navmark){position:absolute; right:10px; top:-5px; height:38px; width:auto; display:flex; align-items:center; pointer-events:none}
.navmark{pointer-events:auto; display:inline-flex; align-items:center; justify-content:center; min-width:20px; height:20px; padding:0 6px; border-radius:7px;
  font-size:11px; font-weight:650; font-variant-numeric:tabular-nums; line-height:1}
.navmark.count{background:rgba(139,124,255,.16); color:#B3A8FF}
.navmark.ok{background:rgba(52,211,153,.14); color:var(--ok)}
/* desktop: the menu is always there. Narrow screens use the top menu instead. */
.st-key-mobilenav{display:none}
@media (min-width:901px){
  [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"]{display:none !important}
}
@media (max-width:900px){
  .st-key-mobilenav{display:block; margin:-.4rem 0 1rem}
  section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"]{display:none !important}
}

.pp-brand{display:flex; align-items:center; gap:.65rem; padding:.35rem .35rem 1.1rem}
.pp-brand .mark{width:30px; height:30px; border-radius:9px; display:grid; place-items:center;
  background:linear-gradient(140deg,#9C8FFF,#6D5EF0); box-shadow:inset 0 0 0 1px rgba(255,255,255,.18), 0 6px 18px -6px rgba(139,124,255,.7)}
.pp-brand .word{font-weight:650; font-size:15.5px; letter-spacing:-.02em}
.pp-brand .word b{color:var(--violet); font-weight:650}
.pp-navlabel{font-size:10.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--faint); font-weight:600; padding:.2rem .5rem .35rem}
.pp-sidefoot{border:1px solid var(--line); background:rgba(255,255,255,.015); border-radius:12px; padding:.7rem .8rem; margin-top:.9rem}
.pp-sidefoot .row{display:flex; align-items:center; justify-content:space-between; font-size:12px; color:var(--muted); padding:2px 0}
.pp-sidefoot .row b{color:var(--text); font-weight:550; font-variant-numeric:tabular-nums}

/* ---- top bar ---- */
.pp-top{display:flex; align-items:center; justify-content:space-between; padding:.35rem 0 1.15rem; gap:1rem; flex-wrap:wrap}
.pp-crumb{display:flex; align-items:center; gap:.5rem; font-size:13px; color:var(--faint)}
.pp-crumb b{color:var(--text); font-weight:600}
.pp-crumb svg{opacity:.5}
.pp-top-right{display:flex; align-items:center; gap:.5rem; flex-wrap:wrap}

/* ---- pills / badges / chips ---- */
.pill{display:inline-flex; align-items:center; gap:.45rem; height:26px; padding:0 .7rem; border-radius:999px; font-size:12px; font-weight:550;
  border:1px solid var(--line2); color:var(--muted); background:rgba(255,255,255,.02); white-space:nowrap}
.pill .dot{width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 0 3px color-mix(in srgb, currentColor 22%, transparent)}
.pill.violet{color:#B3A8FF; border-color:rgba(139,124,255,.35); background:rgba(139,124,255,.10)}
.pill.warn{color:var(--warn); border-color:rgba(251,191,36,.32); background:rgba(251,191,36,.08)}
.pill.bad{color:var(--bad); border-color:rgba(251,113,133,.32); background:rgba(251,113,133,.08)}
.pill.ok{color:var(--ok); border-color:rgba(52,211,153,.32); background:rgba(52,211,153,.08)}
.badge{display:inline-flex; align-items:center; gap:.3rem; height:21px; padding:0 .5rem; border-radius:6px; font-size:11.5px; font-weight:550;
  background:rgba(148,163,184,.10); color:var(--muted); border:1px solid transparent; white-space:nowrap}
.badge.violet{background:rgba(139,124,255,.14); color:#B3A8FF}
.badge.cyan{background:rgba(56,189,248,.12); color:var(--cyan)}
.badge.ok{background:rgba(52,211,153,.12); color:var(--ok)}
.badge.warn{background:rgba(251,191,36,.12); color:var(--warn)}
.badge.bad{background:rgba(251,113,133,.12); color:var(--bad)}
.chip{display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .65rem; border-radius:8px; font-size:12.5px; font-weight:500;
  border:1px solid var(--line2); background:var(--inset); color:var(--text); margin:0 .35rem .4rem 0}
.chip.ok{border-color:rgba(52,211,153,.30); background:rgba(52,211,153,.07); color:#7DE8BE}
.chip.warn{border-color:rgba(251,191,36,.30); background:rgba(251,191,36,.07); color:#FCD34D}
.chip.bad{border-color:rgba(251,113,133,.30); background:rgba(251,113,133,.07); color:#FDA4B1}
.chip.mute{color:var(--muted)}

/* ---- cards ---- */
div[class*="st-key-card"], div[class*="st-key-panel"]{
  background:var(--card); border:1px solid var(--line); border-radius:var(--r); padding:1.15rem 1.25rem;
  transition:border-color .18s, background .18s;
}
div[class*="st-key-card"]:hover{border-color:var(--line2)}
div[class*="st-key-panel"]{background:rgba(22,30,48,.55)}
div[class*="st-key-card"] [data-testid="stVerticalBlock"], div[class*="st-key-panel"] [data-testid="stVerticalBlock"]{gap:.7rem}
.card-title{display:flex; align-items:center; gap:.5rem; font-size:13px; font-weight:600; color:var(--muted); letter-spacing:.01em}
.card-title svg{color:var(--violet)}
.eyebrow{font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--violet); font-weight:650}
.h1{font-size:30px; line-height:1.15; font-weight:680; letter-spacing:-.03em; margin:.2rem 0 .1rem}
.h2{font-size:20px; line-height:1.25; font-weight:650; letter-spacing:-.02em; margin:0}
.sub{color:var(--muted); font-size:14px; line-height:1.55; max-width:62ch}
.mute{color:var(--muted)} .faint{color:var(--faint)}
.num{font-variant-numeric:tabular-nums; letter-spacing:-.02em}
.big{font-size:34px; font-weight:680; line-height:1; letter-spacing:-.035em; font-variant-numeric:tabular-nums}
.big small{font-size:14px; font-weight:500; color:var(--faint); letter-spacing:0; margin-left:.2rem}
.kpi-label{font-size:12.5px; color:var(--muted); font-weight:550; display:flex; align-items:center; gap:.45rem}
.kpi-foot{font-size:12.5px; color:var(--muted)}
.kpi-empty .big{color:var(--faint)}
div[class*="st-key-card-kpiempty"]{border-style:dashed; border-color:var(--line2); background:transparent}

/* ---- hero ---- */
div[class*="st-key-hero"]{
  position:relative; overflow:hidden; border:1px solid rgba(139,124,255,.22); border-radius:18px; padding:1.7rem 1.8rem;
  background:
    radial-gradient(520px 240px at 96% 0%, rgba(139,124,255,.22), transparent 70%),
    linear-gradient(180deg, rgba(28,38,58,.85), rgba(22,30,48,.85));
}
div[class*="st-key-hero"]::after{content:""; position:absolute; inset:0; pointer-events:none; opacity:.5;
  background-image:radial-gradient(rgba(148,163,184,.16) 1px, transparent 1.2px); background-size:22px 22px;
  mask-image:linear-gradient(100deg, transparent 35%, #000 100%); -webkit-mask-image:linear-gradient(100deg, transparent 35%, #000 100%)}
div[class*="st-key-hero"] > *{position:relative; z-index:1}
.flow{display:flex; flex-direction:column; gap:.1rem}
.flow .step{display:flex; align-items:center; gap:.7rem; font-size:13px; color:var(--muted); padding:.32rem 0}
.flow .step .n{width:22px; height:22px; border-radius:7px; display:grid; place-items:center; font-size:11px; font-weight:650;
  color:#B3A8FF; background:rgba(139,124,255,.14); border:1px solid rgba(139,124,255,.25)}
.flow .step b{color:var(--text); font-weight:550}

/* ---- bars ---- */
.bar{height:6px; border-radius:99px; background:rgba(148,163,184,.14); overflow:hidden}
.bar > i{display:block; height:100%; border-radius:99px; background:var(--violet); transition:width .5s cubic-bezier(.2,.8,.2,1)}
.bar.ok > i{background:var(--ok)} .bar.warn > i{background:var(--warn)} .bar.bad > i{background:var(--bad)}
.bar.grad > i{background:linear-gradient(90deg,var(--violet),#9CC9FF)}
.stack{display:flex; height:8px; border-radius:99px; overflow:hidden; gap:2px; background:rgba(148,163,184,.1)}
.stack > i{display:block; height:100%}
.legend{display:flex; gap:1rem; flex-wrap:wrap; font-size:12px; color:var(--muted)}
.legend span{display:inline-flex; align-items:center; gap:.4rem}
.legend span::before{content:""; width:8px; height:8px; border-radius:3px; background:var(--c, var(--violet))}

/* ---- notices / empty / loader ---- */
.notice{display:flex; gap:.7rem; align-items:flex-start; padding:.8rem 1rem; border-radius:12px; font-size:13.5px; line-height:1.5;
  border:1px solid var(--line2); background:var(--elev); color:var(--text)}
.notice svg{flex:none; margin-top:2px}
.notice.ok{border-color:rgba(52,211,153,.3); background:rgba(52,211,153,.06)} .notice.ok svg{color:var(--ok)}
.notice.warn{border-color:rgba(251,191,36,.3); background:rgba(251,191,36,.06)} .notice.warn svg{color:var(--warn)}
.notice.bad{border-color:rgba(251,113,133,.32); background:rgba(251,113,133,.06)} .notice.bad svg{color:var(--bad)}
.notice.info{border-color:rgba(139,124,255,.28); background:rgba(139,124,255,.06)} .notice.info svg{color:var(--violet)}
.empty{display:flex; flex-direction:column; align-items:center; text-align:center; padding:2.6rem 1.5rem; gap:.45rem;
  border:1px dashed var(--line2); border-radius:var(--r); background:rgba(255,255,255,.012)}
.empty .ico{width:46px; height:46px; border-radius:13px; display:grid; place-items:center; color:#B3A8FF;
  background:rgba(139,124,255,.10); border:1px solid rgba(139,124,255,.25); margin-bottom:.4rem}
.empty .t{font-size:16px; font-weight:620; letter-spacing:-.01em}
.empty .d{font-size:13.5px; color:var(--muted); max-width:46ch; line-height:1.55}
.loader{display:flex; gap:1.1rem; align-items:flex-start; padding:1.4rem 1.5rem; border-radius:var(--r); border:1px solid rgba(139,124,255,.25);
  background:linear-gradient(180deg, rgba(139,124,255,.07), rgba(139,124,255,.02))}
.spin{width:22px; height:22px; border-radius:50%; border:2px solid rgba(139,124,255,.25); border-top-color:var(--violet); animation:spin .8s linear infinite; flex:none; margin-top:2px}
@keyframes spin{to{transform:rotate(360deg)}}
.loader ol{list-style:none; margin:.6rem 0 0; padding:0; display:flex; flex-direction:column; gap:.35rem}
.loader li{font-size:13px; color:var(--faint); display:flex; align-items:center; gap:.55rem; animation:pulse 2.4s ease-in-out infinite}
.loader li::before{content:""; width:5px; height:5px; border-radius:50%; background:var(--violet); opacity:.6}
.loader li:nth-child(2){animation-delay:.3s}.loader li:nth-child(3){animation-delay:.6s}.loader li:nth-child(4){animation-delay:.9s}
.loader li:nth-child(5){animation-delay:1.2s}.loader li:nth-child(6){animation-delay:1.5s}
@keyframes pulse{0%,100%{opacity:.45}50%{opacity:1; color:var(--text)}}

/* ---- list rows (activity, attention) ---- */
.rows{display:flex; flex-direction:column}
.rowi{display:flex; gap:.75rem; align-items:flex-start; padding:.65rem 0; border-top:1px solid var(--line); font-size:13.5px}
.rowi:first-child{border-top:0; padding-top:.1rem}
.rowi .ic{width:28px; height:28px; border-radius:8px; display:grid; place-items:center; flex:none; background:rgba(139,124,255,.12); color:#B3A8FF}
.rowi .ic.ok{background:rgba(52,211,153,.12); color:var(--ok)} .rowi .ic.warn{background:rgba(251,191,36,.12); color:var(--warn)}
.rowi .ic.bad{background:rgba(251,113,133,.12); color:var(--bad)} .rowi .ic.cyan{background:rgba(56,189,248,.12); color:var(--cyan)}
.rowi .tx{flex:1; color:var(--text); line-height:1.45} .rowi .tx small{display:block; color:var(--faint); font-size:12px; margin-top:1px}
.rowi .when{font-size:12px; color:var(--faint); white-space:nowrap}

.gapmeta span{white-space:nowrap}
.gapmeta{display:grid; grid-template-columns:118px 124px 108px; gap:.5rem; align-items:center; justify-items:end}
@media (max-width:900px){.gapmeta{grid-template-columns:1fr; justify-items:start}}
/* ---- question cards ---- */
.q-head{display:flex; gap:.7rem; align-items:flex-start}
.q-num{width:26px; height:26px; border-radius:8px; display:grid; place-items:center; font-size:12px; font-weight:650; color:#B3A8FF;
  background:rgba(139,124,255,.12); flex:none; margin-top:1px; font-variant-numeric:tabular-nums}
.q-text{font-size:15px; font-weight:550; line-height:1.5; letter-spacing:-.005em}
.q-meta{display:flex; gap:.4rem; flex-wrap:wrap; margin-top:.5rem}
details.pp{border-top:1px solid var(--line); margin-top:.35rem; padding-top:.55rem}
details.pp summary{cursor:pointer; font-size:12.5px; color:var(--muted); font-weight:550; list-style:none; display:flex; align-items:center; gap:.4rem; user-select:none}
details.pp summary::-webkit-details-marker{display:none}
details.pp summary::before{content:"+"; display:inline-grid; place-items:center; width:16px; height:16px; border-radius:5px; background:rgba(148,163,184,.12); font-size:12px; line-height:1}
details.pp[open] summary::before{content:"–"}
details.pp summary:hover{color:var(--text)}
details.pp .body{font-size:13.5px; color:var(--muted); line-height:1.6; padding:.55rem 0 .2rem}
details.pp .body li{color:var(--muted); margin:.15rem 0}
.mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px}
.codebox{background:var(--inset); border:1px solid var(--line); border-radius:10px; padding:.65rem .8rem; color:#C7D2FE; white-space:pre-wrap}

/* ---- interview ---- */
div[class*="st-key-iq"]{
  background:linear-gradient(180deg, rgba(28,38,58,.9), rgba(22,30,48,.9)); border:1px solid rgba(139,124,255,.25); border-radius:18px; padding:1.5rem 1.6rem}
.iq-who{display:flex; align-items:center; gap:.6rem; font-size:12.5px; color:var(--muted); font-weight:550}
.iq-av{width:28px; height:28px; border-radius:9px; display:grid; place-items:center; background:linear-gradient(140deg,#9C8FFF,#6D5EF0); color:#fff}
.iq-q{font-size:22px; line-height:1.4; font-weight:620; letter-spacing:-.02em; margin:.55rem 0 0}
.dim{display:flex; align-items:center; gap:.7rem; font-size:12.5px; color:var(--muted)}
.dim .l{width:76px} .dim .bar{flex:1} .dim .v{width:34px; text-align:right; color:var(--text); font-weight:600; font-variant-numeric:tabular-nums}

/* ---- timeline (roadmap) ---- */
div[class*="st-key-wk-"]{position:relative; margin-left:30px; width:calc(100% - 30px); background:var(--card); border:1px solid var(--line); border-radius:var(--r); padding:1.1rem 1.25rem}
div[class*="st-key-wk-"]::before{content:""; position:absolute; left:-23px; top:26px; bottom:-1.1rem; width:2px; background:linear-gradient(180deg, var(--line2), var(--line2)); border-radius:2px}
div[class*="st-key-wk-"].st-key-wk-last::before{display:none}
div[class*="st-key-wk-"]::after{content:""; position:absolute; left:-30px; top:19px; width:16px; height:16px; border-radius:50%;
  background:var(--bg); border:2px solid var(--line2); box-sizing:border-box}
div[class*="-s-done"]::after{background:var(--ok); border-color:var(--ok); box-shadow:0 0 0 4px rgba(52,211,153,.14)}
div[class*="-s-done"]::before{background:var(--ok); opacity:.45}
div[class*="-s-now"]{border-color:rgba(139,124,255,.38); background:linear-gradient(180deg, rgba(139,124,255,.07), var(--card))}
div[class*="-s-now"]::after{border-color:var(--violet); background:var(--bg); box-shadow:0 0 0 4px rgba(139,124,255,.18), inset 0 0 0 3px var(--violet)}
.wk-head{display:flex; align-items:flex-start; justify-content:space-between; gap:1rem}
.wk-title{font-size:16px; font-weight:630; letter-spacing:-.015em}
.goal{display:flex; gap:.5rem; font-size:13px; color:var(--muted); line-height:1.5}
.goal svg{color:var(--violet); flex:none; margin-top:3px}
.task-meta{display:flex; gap:.35rem; justify-content:flex-end; flex-wrap:wrap; align-items:center; min-height:28px}
.res{font-size:12px; color:var(--faint); padding-left:1.95rem; margin-top:-.3rem}
.prio{display:inline-flex; align-items:center; gap:.3rem; font-size:11.5px; color:var(--muted); font-weight:550}
.prio i{width:7px; height:7px; border-radius:50%; background:var(--faint)}
.prio.high i{background:var(--bad)} .prio.med i{background:var(--warn)}
div[class*="st-key-task-"]{padding:.05rem 0; border-top:1px solid var(--line)}
div[class*="st-key-task-"]:first-of-type{border-top:0}
[data-testid="stCheckbox"] label{padding:.25rem 0}
[data-testid="stCheckbox"] label p{font-size:14px; line-height:1.45}
[data-testid="stCheckbox"] label:has(input:checked) p{color:var(--faint); text-decoration:line-through; text-decoration-color:rgba(148,163,184,.4)}

/* ---- streamlit widgets ---- */
.stButton button, .stDownloadButton button, [data-testid^="stBaseButton"]{border-radius:10px; font-weight:550; font-size:13.5px; transition:transform .12s, border-color .15s, background .15s, filter .15s}
.stApp .stButton button[data-testid="stBaseButton-primary"], .stApp [data-testid="stBaseButton-primaryFormSubmit"]{
  background:linear-gradient(180deg,#9A8DFF,#7A6BF5); border:1px solid rgba(255,255,255,.16); color:#fff; height:42px;
  box-shadow:0 8px 22px -10px rgba(139,124,255,.9), inset 0 1px 0 rgba(255,255,255,.18)}
.stApp .stButton button[data-testid="stBaseButton-primary"]:hover, .stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover{filter:brightness(1.07); transform:translateY(-1px)}
.stApp .stButton button[data-testid="stBaseButton-primary"]:disabled{background:rgba(148,163,184,.12); color:var(--faint); box-shadow:none; border-color:var(--line); transform:none}
.stApp .stButton button[data-testid="stBaseButton-secondary"], .stApp [data-testid="stBaseButton-secondaryFormSubmit"]{
  background:var(--elev); border:1px solid var(--line2); color:var(--text); height:40px}
.stApp .stButton button[data-testid="stBaseButton-secondary"]:hover{border-color:rgba(139,124,255,.5); background:#212D45}
.stApp .stButton button[data-testid="stBaseButton-tertiary"]{color:var(--muted)}
.stApp .stButton button[data-testid="stBaseButton-tertiary"]:hover{color:var(--text); background:rgba(148,163,184,.08)}
.stButton button:focus-visible{outline:2px solid var(--violet); outline-offset:2px}

[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div{
  background:var(--inset) !important; border:1px solid var(--line2) !important; border-radius:10px !important; transition:border-color .15s, box-shadow .15s}
[data-baseweb="base-input"]{background:transparent !important}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:focus-within > div{
  border-color:var(--violet) !important; box-shadow:0 0 0 3px rgba(139,124,255,.18) !important}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea{color:var(--text) !important; font-size:14px}
[data-baseweb="textarea"] textarea{line-height:1.55}
::placeholder{color:var(--faint) !important; opacity:1 !important}
[data-testid="stWidgetLabel"] p{font-size:12.5px !important; font-weight:550; color:var(--muted)}
[data-testid="stTextInput"], [data-testid="stTextArea"]{margin-bottom:.1rem}

[data-testid="stFileUploaderDropzone"]{
  background:rgba(139,124,255,.035); border:1.5px dashed rgba(139,124,255,.38); border-radius:16px; padding:1.7rem 1rem; min-height:170px;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:.75rem; text-align:center; transition:all .18s}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--violet); background:rgba(139,124,255,.08)}
[data-testid="stFileUploaderDropzone"] > div{display:flex; flex-direction:column; align-items:center; gap:.3rem; text-align:center}
[data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"]{color:var(--violet); font-size:30px}
[data-testid="stFileUploaderDropzone"] small{color:var(--faint)}
[data-testid="stFileUploaderDropzone"] button{background:var(--elev); border:1px solid var(--line2); color:var(--text); height:36px}
[data-testid="stFileUploaderFile"]{background:var(--inset); border:1px solid var(--line); border-radius:10px; padding:.3rem .6rem}

[data-baseweb="tab-list"]{gap:.25rem; border-bottom:1px solid var(--line); padding-bottom:0}
button[data-baseweb="tab"]{height:40px; padding:0 .9rem; background:transparent !important; color:var(--muted); font-size:13.5px; font-weight:550}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--text)}
button[data-baseweb="tab"]:hover{color:var(--text)}
[data-baseweb="tab-highlight"]{background:var(--violet) !important; height:2px !important}
[data-baseweb="tab-border"]{display:none}
[data-testid="stTabs"] [data-testid="stMarkdownContainer"] p{font-size:13.5px}

[data-testid="stButtonGroup"] button{background:var(--inset); border:1px solid var(--line2); color:var(--muted); font-size:13px; height:36px; border-radius:10px}
[data-testid="stButtonGroup"] button:hover{color:var(--text); border-color:rgba(139,124,255,.45)}
[data-testid="stButtonGroup"] button[data-testid*="Active"]{background:rgba(139,124,255,.16); border-color:rgba(139,124,255,.55); color:var(--text)}

[data-testid="stExpander"] details{border:1px solid var(--line); border-radius:12px; background:rgba(22,30,48,.6)}
[data-testid="stExpander"] summary{font-size:13.5px; font-weight:550; color:var(--muted)}
[data-testid="stExpander"] summary:hover{color:var(--text)}
[data-testid="stAlert"]{background:var(--elev); border:1px solid var(--line2); border-radius:12px; color:var(--text)}
[data-testid="stToast"]{background:var(--elev); border:1px solid var(--line2); border-radius:12px; color:var(--text)}
[data-testid="stPlotlyChart"]{background:transparent}
[data-testid="stSlider"] [data-testid="stTickBar"]{display:none}
[data-testid="stSlider"] [data-testid="stThumbValue"]{color:#B3A8FF; font-weight:600}
[data-testid="stProgress"] > div > div{background:rgba(148,163,184,.14); height:6px}
.stSpinner > div{color:var(--muted)}

/* ---- equal-height cards: a card that is the only child of a column fills the column ---- */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]{height:100%}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child{flex:1 1 auto; display:flex; flex-direction:column}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child > [class*="st-key-card"]{flex:1 1 auto}
div[class*="st-key-hero"] .stButton{margin-top:.6rem}

@media (max-width: 900px){
  [data-testid="stMainBlockContainer"], .block-container{padding:.3rem 1rem 3rem !important}
  .h1{font-size:25px} .iq-q{font-size:19px}
}
"""


def inject() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
