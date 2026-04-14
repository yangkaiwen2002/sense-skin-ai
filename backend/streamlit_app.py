"""
SkinSense · CS2 Skin AI Agent  (v2 — polished UI)
Run: streamlit run streamlit_app.py  (from backend/)
"""

import re
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from data_sources.steam_client import fetch_price_overview, fetch_listings, search_items
from scoring import compute, agent_reply, SkinScore

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkinSense AI · CS2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

WEAR_MAP = {
    "(Factory New)":    ("FN", "#4db6d4"),
    "(Minimal Wear)":   ("MW", "#5cb85c"),
    "(Field-Tested)":   ("FT", "#f0ad4e"),
    "(Well-Worn)":      ("WW", "#e07b39"),
    "(Battle-Scarred)": ("BS", "#d9534f"),
}

QUICK = [
    ("AK-47 | Redline",        "AK-47 | Redline (Field-Tested)"),
    ("AWP | Dragon Lore",      "AWP | Dragon Lore (Field-Tested)"),
    ("Desert Eagle | Blaze",   "Desert Eagle | Blaze (Factory New)"),
    ("M4A4 | Howl",            "M4A4 | Howl (Field-Tested)"),
    ("Butterfly Knife | Fade", "Butterfly Knife | Fade (Factory New)"),
    ("Glock-18 | Fade",        "Glock-18 | Fade (Factory New)"),
]

STEAM_CDN = "https://community.akamai.steamstatic.com/economy/image"

# ─────────────────────────────────────────────────────────────────────────────
#  i18n — add more langs below following the same key structure
# ─────────────────────────────────────────────────────────────────────────────
I18N: dict[str, dict] = {
    "中文": {
        # sidebar
        "agent_subtitle":   "CS2 饰品智能分析平台",
        "search_label":     "搜索饰品",
        "search_btn":       "搜索",
        "analyze_btn":      "分析",
        "manual_label":     "直接输入 Hash Name",
        "analyze_start":    "开始分析",
        "quick_label":      "快速分析",
        "not_connected":    "未连接",
        # hero
        "lowest_price":     "最低在售价",
        "median_price":     "Steam 均价",
        "volume_24h":       "24h 成交",
        "rating_lbl":       "评分",
        "vs_median":        "vs 均价",
        # score panel
        "sub_scores":       "Sub Scores",
        "score_dims": [
            ("价值",   "Value"),
            ("流动性", "Liquidity"),
            ("稳定性", "Stability"),
            ("趋势",   "Trend"),
        ],
        # tabs
        "tab_market":    "  市场数据  ",
        "tab_listings":  "  挂单列表  ",
        "tab_agent":     "  AI 对话  ",
        # market tab
        "kpi_lowest":    "最低在售价",
        "kpi_median":    "Steam 均价",
        "kpi_vol":       "24h 成交量",
        "kpi_total":     "总挂单量",
        "kpi_std":       "价格标准差",
        "dist_title":    "价格分布",
        "dist_sub":      "基于 {n} 条挂单",
        "pct_title":     "价格分位",
        "pct_rows": [
            (10, "P10 · 低价区", "#5cb85c"),
            (25, "P25",          "#7ec87e"),
            (50, "P50 · 中位",   "#f0ad4e"),
            (75, "P75",          "#e07b39"),
            (90, "P90 · 高价区", "#d9534f"),
        ],
        "no_data":        "暂无数据",
        "all_same_price": "所有挂单价格相同",
        # listings tab
        "listings_title": "在售挂单",
        "listings_sub":   "共 {total:,} 条 · 显示最低价前 {n} 条",
        "col_listing_id": "Listing ID",
        "col_price":      "价格",
        "col_vs_median":  "vs均价",
        "col_grade":      "评级",
        "no_listings":    "暂无挂单数据",
        "bands":          ["优质", "良好", "普通", "偏贵", "高价"],
        # agent tab
        "agent_title":    "AI 饰品分析师",
        "agent_sub":      "基于评分数据实时回答",
        "quick_q_label":  "快速提问",
        "presets": [
            "这个饰品值得买吗？", "为什么分数低？",
            "适合长期持有吗？", "好不好出手？", "综合分析一下",
        ],
        "chat_placeholder": "问我任何关于这个饰品的问题…",
        # empty state
        "brand_sub":       "CS2 饰品智能分析平台 · Steam Market Data",
        "feat_score":      "评分系统",
        "feat_score_desc": "价值 · 流动性 · 稳定性 · 趋势\n综合评分 0–100",
        "feat_market":     "实时市场数据",
        "feat_market_desc":"Steam Market 公开接口\n价格分布 · 挂单列表 · 成交量",
        "feat_ai":         "AI 分析师",
        "feat_ai_desc":    "值得买吗 · 为什么分数低\n适合长期持有吗",
        "empty_hint":      "在左侧搜索饰品，或选择快速分析开始",
        "empty_sub":       "支持输入 Steam Market Hash Name",
        # nav
        "nav_tagline":     "CS2 · Skin Intelligence",
        "nav_data_src":    "Steam Community Market · No login required",
    },

    "English": {
        "agent_subtitle":   "CS2 Skin Intelligence Platform",
        "search_label":     "Search Skins",
        "search_btn":       "Search",
        "analyze_btn":      "Analyze",
        "manual_label":     "Enter Hash Name Directly",
        "analyze_start":    "Analyze",
        "quick_label":      "Quick Analysis",
        "not_connected":    "Disconnected",
        # hero
        "lowest_price":     "Lowest Ask",
        "median_price":     "Steam Median",
        "volume_24h":       "24h Volume",
        "rating_lbl":       "Rating",
        "vs_median":        "vs median",
        # score panel
        "sub_scores":       "Sub Scores",
        "score_dims": [
            ("Value",     ""),
            ("Liquidity", ""),
            ("Stability", ""),
            ("Trend",     ""),
        ],
        # tabs
        "tab_market":    "  Market Data  ",
        "tab_listings":  "  Listings  ",
        "tab_agent":     "  AI Chat  ",
        # market tab
        "kpi_lowest":    "Lowest Ask",
        "kpi_median":    "Median Price",
        "kpi_vol":       "24h Volume",
        "kpi_total":     "Total Listings",
        "kpi_std":       "Price Std Dev",
        "dist_title":    "Price Distribution",
        "dist_sub":      "based on {n} listings",
        "pct_title":     "Price Percentiles",
        "pct_rows": [
            (10, "P10 · Cheap",   "#5cb85c"),
            (25, "P25",           "#7ec87e"),
            (50, "P50 · Median",  "#f0ad4e"),
            (75, "P75",           "#e07b39"),
            (90, "P90 · Pricey",  "#d9534f"),
        ],
        "no_data":        "No data available",
        "all_same_price": "All listings at the same price",
        # listings tab
        "listings_title": "Active Listings",
        "listings_sub":   "{total:,} total · showing {n} lowest",
        "col_listing_id": "Listing ID",
        "col_price":      "Price",
        "col_vs_median":  "vs Median",
        "col_grade":      "Grade",
        "no_listings":    "No listings available",
        "bands":          ["Great", "Good", "Fair", "Pricey", "High"],
        # agent tab
        "agent_title":    "AI Skin Analyst",
        "agent_sub":      "Answers based on live score data",
        "quick_q_label":  "Quick Questions",
        "presets": [
            "Is this worth buying?", "Why is the score low?",
            "Good for long-term hold?", "Easy to sell?", "Give me a full analysis",
        ],
        "chat_placeholder": "Ask me anything about this skin…",
        # empty state
        "brand_sub":       "CS2 Skin Intelligence Platform · Steam Market Data",
        "feat_score":      "Scoring System",
        "feat_score_desc": "Value · Liquidity · Stability · Trend\nComposite score 0–100",
        "feat_market":     "Live Market Data",
        "feat_market_desc":"Steam Market public API\nPrice dist · Listings · Volume",
        "feat_ai":         "AI Analyst",
        "feat_ai_desc":    "Worth buying? · Why is it low?\nGood for holding?",
        "empty_hint":      "Search a skin on the left, or pick a quick analysis",
        "empty_sub":       "Supports Steam Market Hash Name input",
        # nav
        "nav_tagline":     "CS2 · Skin Intelligence",
        "nav_data_src":    "Steam Community Market · No login required",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html,body,[class*="css"]{ font-family:'Inter',-apple-system,sans-serif; }
.stApp{ background:#0b0b0b; }
.block-container{ padding:0 1.5rem 2.5rem !important; max-width:100% !important; }
#MainMenu,footer,header{ visibility:hidden; }

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
    background:#0d0d0d;
    border-right:1px solid #1d1d1d;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.stTextInput input{
    background:#141414 !important; border:1px solid #262626 !important;
    border-radius:8px !important; color:#ddd !important; font-size:.85rem !important;
    padding:.55rem .85rem !important;
}
.stTextInput input:focus{
    border-color:#e05a00 !important;
    box-shadow:0 0 0 2px rgba(224,90,0,.1) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton>button{
    background:linear-gradient(135deg,#e05a00,#c94e00);
    border:none; border-radius:8px; color:#fff;
    font-weight:600; font-size:.83rem; padding:.5rem 1.1rem;
    transition:all .18s ease; width:100%;
    box-shadow:0 2px 10px rgba(224,90,0,.25);
}
.stButton>button:hover{
    background:linear-gradient(135deg,#f06820,#e05a00);
    box-shadow:0 4px 20px rgba(224,90,0,.4);
    transform:translateY(-1px);
}
.stButton>button:active{ transform:translateY(0); }

/* secondary */
.stButton>button[kind="secondary"]{
    background:#161616 !important; border:1px solid #252525 !important;
    color:#555 !important; box-shadow:none !important;
}
.stButton>button[kind="secondary"]:hover{
    background:#1e1e1e !important; color:#bbb !important;
    border-color:#333 !important; transform:none !important; box-shadow:none !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{
    background:transparent !important;
    border-bottom:1px solid #1d1d1d; gap:0; padding:0;
}
.stTabs [data-baseweb="tab"]{
    background:transparent !important; border:none;
    border-bottom:2px solid transparent; border-radius:0 !important;
    color:#3a3a3a; font-size:.84rem; font-weight:500;
    padding:.65rem 1.4rem; transition:all .15s;
}
.stTabs [data-baseweb="tab"]:hover{ color:#aaa; }
.stTabs [aria-selected="true"]{
    color:#e05a00 !important;
    border-bottom:2px solid #e05a00 !important;
    background:transparent !important;
}
.stTabs [data-baseweb="tab-panel"]{ padding:1.25rem 0 0; }

/* ── Chat ────────────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"]{
    background:#121212 !important;
    border:1px solid #1d1d1d !important;
    border-radius:10px !important;
}

/* ── Divider / scrollbar ─────────────────────────────────────────────────── */
hr{ border-color:#1a1a1a !important; }
::-webkit-scrollbar{ width:4px; height:4px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:#222; border-radius:4px; }
::-webkit-scrollbar-thumb:hover{ background:#333; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _icon_src(icon_url: str | None, size: str = "256fx256f") -> str | None:
    return f"{STEAM_CDN}/{icon_url}/{size}" if icon_url else None

def _wear(hash_name: str) -> tuple[str, str]:
    for suffix, pair in WEAR_MAP.items():
        if suffix in hash_name:
            return pair
    return ("", "#555")

def score_color(s: int) -> str:
    if s >= 75: return "#5cb85c"
    if s >= 55: return "#f0ad4e"
    return "#d9534f"

LANG_OPTIONS = list(I18N.keys())   # ["中文", "English"]

def T(key: str) -> str:
    """Return translated string for the active language."""
    return I18N[st.session_state.get("lang", LANG_OPTIONS[0])][key]

def _init():
    for k, v in {
        "hash_name": "", "overview": None, "listings": None,
        "scores": None, "search_results": [], "icon_url": None,
        "chat_history": [], "last_fetched": None, "connected": False,
        "lang": LANG_OPTIONS[0],
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _fetch(hash_name: str):
    with st.spinner("获取价格数据..."):
        ov = fetch_price_overview(hash_name)
    if not ov.get("ok"):
        st.error(f"Steam API 错误：{ov.get('error')}"); return
    with st.spinner("拉取挂单列表..."):
        ls = fetch_listings(hash_name, count=100)
    listing_prices = [l["price"] for l in ls.get("listings", [])]
    sc = compute(
        lowest_price   = ov.get("lowest_price"),
        median_price   = ov.get("median_price"),
        volume         = ov.get("volume"),
        total_listings = ls.get("total"),
        listing_prices = listing_prices,
    )
    st.session_state.update(
        hash_name=hash_name, overview=ov, listings=ls, scores=sc,
        icon_url=ls.get("icon_url"),
        chat_history=[], last_fetched=datetime.now().strftime("%H:%M:%S"),
        connected=True,
    )
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  SVG SCORE RING
# ─────────────────────────────────────────────────────────────────────────────
def _score_ring(score: int, color: str, label: str, size: int = 140) -> str:
    half = size // 2
    r = int(half * 0.77)
    circ = 2 * 3.14159265 * r
    offset = circ * (1 - score / 100)
    fs_score = int(size * 0.225)
    fs_label = int(size * 0.075)
    fs_rating = int(size * 0.083)
    sw = max(6, int(size * 0.052))
    return f"""
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"
     style="display:block;margin:0 auto;overflow:visible">
  <defs>
    <filter id="ring-glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <circle cx="{half}" cy="{half}" r="{r}"
          fill="none" stroke="#1a1a1a" stroke-width="{sw}"/>
  <circle cx="{half}" cy="{half}" r="{r}"
          fill="none" stroke="{color}" stroke-width="{sw}"
          stroke-linecap="round"
          stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"
          transform="rotate(-90 {half} {half})"
          filter="url(#ring-glow)" opacity="0.35"/>
  <circle cx="{half}" cy="{half}" r="{r}"
          fill="none" stroke="{color}" stroke-width="{sw}"
          stroke-linecap="round"
          stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"
          transform="rotate(-90 {half} {half})"/>
  <text x="{half}" y="{half - 8}" text-anchor="middle"
        font-family="Inter,sans-serif" font-size="{fs_score}"
        font-weight="800" fill="{color}">{score}</text>
  <text x="{half}" y="{half + 10}" text-anchor="middle"
        font-family="Inter,sans-serif" font-size="{fs_label}"
        fill="#383838" letter-spacing="2">SCORE</text>
  <text x="{half}" y="{half + 27}" text-anchor="middle"
        font-family="Inter,sans-serif" font-size="{fs_rating}"
        font-weight="600" fill="{color}">{label}</text>
</svg>"""

# ─────────────────────────────────────────────────────────────────────────────
#  SCORE PANEL  (all HTML — avoids open/close div split across st.markdown)
# ─────────────────────────────────────────────────────────────────────────────
def score_panel(sc: SkinScore):
    c = sc.overall_color
    ring = _score_ring(sc.overall, c, sc.overall_label)

    dims = T("score_dims")
    dim_data = [
        (dims[0][0], dims[0][1], sc.value,     sc.value_note),
        (dims[1][0], dims[1][1], sc.liquidity, sc.liquidity_note),
        (dims[2][0], dims[2][1], sc.stability, sc.stability_note),
        (dims[3][0], dims[3][1], sc.trend,     sc.trend_note),
    ]
    bars = ""
    for lbl, en, val, note in dim_data:
        bc = score_color(val)
        en_span = f'<span style="font-size:.67rem;color:#333;font-weight:400;margin-left:5px">{en}</span>' if en else ""
        bars += f"""
<div style="margin-bottom:1.05rem">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px">
    <span style="font-size:.81rem;font-weight:600;color:#ccc">{lbl}{en_span}</span>
    <span style="font-size:.9rem;font-weight:700;color:{bc}">{val}</span>
  </div>
  <div style="background:#181818;border-radius:4px;height:5px;overflow:hidden">
    <div style="background:linear-gradient(90deg,{bc}60,{bc});
                width:{val}%;height:5px;border-radius:4px"></div>
  </div>
  <div style="font-size:.69rem;color:#363636;line-height:1.5;margin-top:4px">{note}</div>
</div>"""

    st.markdown(f"""
<div style="background:linear-gradient(160deg,#141414 0%,#0e0e0e 100%);
            border:1px solid #1e1e1e;border-radius:14px;padding:1.4rem 1.25rem">
  <div style="padding:.6rem 0 1rem">{ring}</div>
  <div style="height:1px;background:#181818;margin:.5rem 0 1.1rem"></div>
  <div style="font-size:.62rem;color:#282828;letter-spacing:.12em;
              text-transform:uppercase;font-weight:600;margin-bottom:.9rem">
    {T("sub_scores")}</div>
  {bars}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HERO SECTION  (skin image + name + key stats)
# ─────────────────────────────────────────────────────────────────────────────
def hero_section(hash_name: str, ov: dict, sc: SkinScore, icon_url: str | None = None):
    lp  = ov.get("lowest_price")
    mp  = ov.get("median_price")
    vol = ov.get("volume")
    wear_abbr, wear_color = _wear(hash_name)
    c = sc.overall_color

    parts  = hash_name.split("|")
    weapon = parts[0].strip() if parts else ""
    skin_raw = parts[1].strip() if len(parts) > 1 else hash_name
    skin = re.sub(r'\s*\([^)]+\)\s*$', '', skin_raw).strip()

    # Price delta vs median
    if lp and mp and mp > 0:
        pct = (lp - mp) / mp * 100
        dc  = "#5cb85c" if pct <= -2 else ("#d9534f" if pct >= 2 else "#666")
        ds  = f"{'▲' if pct > 0 else '▼'} {abs(pct):.1f}% {T('vs_median')}"
    else:
        dc, ds = "#444", ""

    img_src = _icon_src(icon_url)
    if img_src:
        img_block = f"""
<div style="position:relative;flex-shrink:0;width:290px;height:210px;
            display:flex;align-items:center;justify-content:center">
  <div style="position:absolute;inset:0;border-radius:12px;
              background:radial-gradient(ellipse at 50% 55%,{c}1e 0%,transparent 70%)"></div>
  <img src="{img_src}"
       style="position:relative;z-index:1;max-width:280px;max-height:200px;
              object-fit:contain;
              filter:drop-shadow(0 6px 28px {c}55) drop-shadow(0 2px 8px #00000080)"/>
</div>"""
    else:
        img_block = f"""
<div style="flex-shrink:0;width:290px;height:210px;border-radius:12px;
            background:#141414;border:1px dashed #1e1e1e;
            display:flex;align-items:center;justify-content:center;
            font-size:4rem;color:#222">🔫</div>"""

    wear_badge = f"""
<span style="display:inline-block;background:{wear_color}18;
             border:1px solid {wear_color}50;color:{wear_color};
             font-size:.7rem;font-weight:700;padding:.18rem .55rem;
             border-radius:4px;letter-spacing:.04em">{wear_abbr}</span>
""" if wear_abbr else ""

    def stat_col(label, value, value_style="", sub="", sub_color="#444"):
        return f"""
<div>
  <div style="font-size:.6rem;color:#383838;letter-spacing:.07em;margin-bottom:3px">{label}</div>
  <div style="font-size:1.9rem;font-weight:900;color:#e05a00;line-height:1;
              font-feature-settings:'tnum' 1;{value_style}">{value}</div>
  {"" if not sub else f'<div style="font-size:.68rem;color:{sub_color};margin-top:3px">{sub}</div>'}
</div>"""

    def stat_col_sm(label, value):
        return f"""
<div style="border-left:1px solid #1e1e1e;padding-left:1.75rem">
  <div style="font-size:.6rem;color:#383838;letter-spacing:.07em;margin-bottom:3px">{label}</div>
  <div style="font-size:1.15rem;font-weight:700;color:#888">{value}</div>
</div>"""

    lp_str = f"¥{lp:,.2f}" if lp else "—"
    mp_str = f"¥{mp:,.2f}" if mp else "—"
    vol_str = f"{vol:,}" if vol else "—"

    rating_badge = f"""
<div style="flex-shrink:0;background:{c}12;border:1px solid {c}30;
            border-radius:10px;padding:.7rem 1.2rem;text-align:center;
            align-self:flex-start">
  <div style="font-size:.58rem;color:#383838;letter-spacing:.1em;margin-bottom:2px">RATING</div>
  <div style="font-size:1.75rem;font-weight:900;color:{c};line-height:1">{sc.overall}</div>
  <div style="font-size:.7rem;color:{c};opacity:.75;margin-top:3px">{sc.overall_label}</div>
</div>"""

    st.markdown(f"""
<div style="background:linear-gradient(140deg,#141414 0%,#0f0f0f 55%,#131313 100%);
            border:1px solid #202020;border-radius:16px;
            padding:1.5rem 1.75rem;margin-bottom:1.5rem;
            display:flex;align-items:center;gap:1.75rem;flex-wrap:wrap;
            position:relative;overflow:hidden">
  <!-- ambient score-color glow at top -->
  <div style="position:absolute;top:-80px;right:80px;width:400px;height:250px;
              background:radial-gradient(ellipse,{c}08 0%,transparent 65%);
              pointer-events:none"></div>
  {img_block}
  <div style="flex:1;min-width:180px">
    <div style="font-size:.66rem;color:#383838;font-weight:600;
                letter-spacing:.1em;text-transform:uppercase;margin-bottom:.35rem">
      {weapon}</div>
    <div style="display:flex;align-items:center;gap:.65rem;flex-wrap:wrap;margin-bottom:1.1rem">
      <span style="font-size:1.6rem;font-weight:800;color:#f5f5f5;line-height:1.15">{skin}</span>
      {wear_badge}
    </div>
    <div style="display:flex;align-items:flex-end;gap:1.75rem;flex-wrap:wrap">
      {stat_col(T("lowest_price"), lp_str, sub=ds, sub_color=dc)}
      {stat_col_sm(T("median_price"), mp_str)}
      {stat_col_sm(T("volume_24h"), vol_str)}
    </div>
  </div>
  {rating_badge}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  MARKET TAB  (custom HTML histogram + percentile table)
# ─────────────────────────────────────────────────────────────────────────────
def tab_market(ov: dict, ls: dict, sc: SkinScore):
    lp   = ov.get("lowest_price")
    mp   = ov.get("median_price")
    vol  = ov.get("volume")
    tot  = ls.get("total", 0)
    prices = [l["price"] for l in ls.get("listings", [])]

    def kpi(label, val, color="#ddd"):
        return f"""
<div style="background:#111;border:1px solid #1d1d1d;border-radius:10px;
            padding:.75rem 1rem;text-align:center">
  <div style="font-size:.62rem;color:#383838;letter-spacing:.06em;margin-bottom:4px">{label}</div>
  <div style="font-size:1rem;font-weight:700;color:{color}">{val}</div>
</div>"""

    kpis = (
        kpi(T("kpi_lowest"), f"¥{lp:.2f}" if lp else "—", "#e05a00") +
        kpi(T("kpi_median"), f"¥{mp:.2f}" if mp else "—") +
        kpi(T("kpi_vol"),    f"{vol:,}"   if vol else "—") +
        kpi(T("kpi_total"),  f"{tot:,}"   if tot else "—") +
        kpi(T("kpi_std"),    f"¥{sc.price_std:.2f}" if sc.price_std else "—")
    )

    # ── histogram ──────────────────────────────────────────────────────────
    if prices and len(prices) > 1:
        mn, mx = min(prices), max(prices)
        if mn < mx:
            n = 20
            edges = np.linspace(mn, mx, n + 1)
            counts, _ = np.histogram(prices, bins=edges)
            peak = max(counts) or 1
            bar_cols = []
            for i, (cnt, edge) in enumerate(zip(counts, edges)):
                h = int(cnt / peak * 130)
                pos = i / n
                bc = "#5cb85c" if pos < 0.3 else ("#f0ad4e" if pos < 0.65 else "#d9534f")
                is_peak = cnt == peak
                bar_cols.append(
                    f'<div style="flex:1;display:flex;flex-direction:column;'
                    f'align-items:center;justify-content:flex-end;height:130px" '
                    f'title="¥{edge:.0f}–¥{edges[i+1]:.0f} · {cnt}条">'
                    f'<div style="width:100%;height:{h}px;'
                    f'background:{"linear-gradient(180deg," + bc + "dd," + bc + ")" if is_peak else bc + "55"};'
                    f'border-radius:3px 3px 0 0;'
                    f'border-top:{"2px solid " + bc if is_peak else "none"}">'
                    f'</div></div>'
                )
            bar_html = (
                f'<div style="display:flex;align-items:flex-end;gap:2px;'
                f'height:130px;margin-bottom:6px">{"".join(bar_cols)}</div>'
            )
            step = n // 4
            x_labels = "".join(
                f'<span style="font-size:.62rem;color:#303030">¥{edges[min(i*step,n)]:.0f}</span>'
                for i in range(5)
            )
            hist_html = (
                bar_html +
                f'<div style="display:flex;justify-content:space-between">{x_labels}</div>'
            )
        else:
            hist_html = f'<p style="color:#333;font-size:.8rem">{T("all_same_price")}</p>'
    else:
        hist_html = f'<p style="color:#333;font-size:.8rem;padding:2rem 0">{T("no_data")}</p>'

    # ── percentile table ───────────────────────────────────────────────────
    if prices:
        p_arr = np.array(prices)
        pct_rows = ""
        for pct, label, bc in T("pct_rows"):
            val = np.percentile(p_arr, pct)
            pct_rows += (
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;padding:.45rem 0;border-bottom:1px solid #141414">'
                f'<span style="font-size:.78rem;color:#404040">{label}</span>'
                f'<span style="font-size:.92rem;font-weight:700;color:{bc}">¥{val:.2f}</span>'
                f'</div>'
            )
        pct_html = f'<div>{pct_rows}</div>'
    else:
        pct_html = f'<p style="color:#333;font-size:.8rem">{T("no_data")}</p>'

    def sec(title, sub=""):
        s = f'<span style="color:#333;font-size:.75rem;margin-left:.4rem">{sub}</span>' if sub else ""
        return (
            f'<div style="font-size:.82rem;font-weight:600;color:#bbb;'
            f'padding:.3rem 0 .7rem;border-bottom:1px solid #1a1a1a;margin-bottom:.9rem">'
            f'{title}{s}</div>'
        )

    dist_sub = T("dist_sub").format(n=len(prices))
    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.65rem;margin-bottom:1.5rem">
  {kpis}
</div>
<div style="display:grid;grid-template-columns:3fr 2fr;gap:1.5rem">
  <div>
    {sec(T("dist_title"), dist_sub)}
    {hist_html}
  </div>
  <div>
    {sec(T("pct_title"))}
    {pct_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LISTINGS TAB  (color-coded by percentile, delta vs median)
# ─────────────────────────────────────────────────────────────────────────────
def tab_listings(ls: dict, ov: dict):
    listings = ls.get("listings", [])
    if not listings:
        st.markdown(
            f'<div style="color:#2a2a2a;font-size:.85rem;padding:3rem 0;'
            f'text-align:center">{T("no_listings")}</div>',
            unsafe_allow_html=True)
        return

    prices_arr = np.array([l["price"] for l in listings])
    p10 = float(np.percentile(prices_arr, 10)) if len(prices_arr) >= 5 else float(prices_arr[0])
    p25 = float(np.percentile(prices_arr, 25)) if len(prices_arr) >= 5 else float(prices_arr[0])
    p75 = float(np.percentile(prices_arr, 75)) if len(prices_arr) >= 5 else float(prices_arr[-1])
    p90 = float(np.percentile(prices_arr, 90)) if len(prices_arr) >= 5 else float(prices_arr[-1])
    mp  = ov.get("median_price")
    bands = T("bands")

    def row_color(p):
        if p <= p10: return ("#5cb85c", bands[0])
        if p <= p25: return ("#7ec87e", bands[1])
        if p <= p75: return ("#f0ad4e", bands[2])
        if p <= p90: return ("#e07b39", bands[3])
        return ("#d9534f", bands[4])

    header = f"""
<div style="display:grid;grid-template-columns:2.5rem 1fr 5.5rem 4.5rem 4rem;
            gap:0;padding:.45rem .9rem;background:#141414;
            border:1px solid #1d1d1d;border-radius:8px 8px 0 0;
            font-size:.66rem;color:#383838;font-weight:600;letter-spacing:.07em">
  <div>#</div><div>{T("col_listing_id")}</div>
  <div style="text-align:right">{T("col_price")}</div>
  <div style="text-align:right">{T("col_vs_median")}</div>
  <div style="text-align:right">{T("col_grade")}</div>
</div>"""

    rows = ""
    for i, l in enumerate(listings[:60]):
        pc, band = row_color(l["price"])
        bg = "#0f0f0f" if i % 2 == 0 else "#111111"
        if mp and mp > 0:
            delta = (l["price"] - mp) / mp * 100
            ds = f"{'▲' if delta > 0 else '▼'}{abs(delta):.1f}%"
            dc = "#d9534f" if delta > 2 else ("#5cb85c" if delta < -2 else "#404040")
        else:
            ds, dc = "—", "#383838"

        rows += (
            f'<div style="display:grid;grid-template-columns:2.5rem 1fr 5.5rem 4.5rem 4rem;'
            f'gap:0;padding:.5rem .9rem;background:{bg};'
            f'border-left:1px solid #1a1a1a;border-right:1px solid #1a1a1a;'
            f'border-bottom:1px solid #161616;align-items:center">'
            f'<div style="font-size:.66rem;color:#282828">#{i+1:02d}</div>'
            f'<div style="font-size:.7rem;color:#303030;font-family:monospace;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{l["listing_id"][:20]}…</div>'
            f'<div style="text-align:right;font-size:.9rem;font-weight:700;color:{pc}">¥{l["price"]:.2f}</div>'
            f'<div style="text-align:right;font-size:.72rem;color:{dc}">{ds}</div>'
            f'<div style="text-align:right">'
            f'<span style="background:{pc}15;border:1px solid {pc}35;color:{pc};'
            f'font-size:.62rem;font-weight:600;padding:.12rem .38rem;border-radius:3px">{band}</span>'
            f'</div></div>'
        )

    listings_sub = T("listings_sub").format(total=ls.get("total", 0), n=len(listings))
    st.markdown(f"""
<div style="font-size:.8rem;color:#bbb;font-weight:600;
            padding:.3rem 0 .7rem;border-bottom:1px solid #1a1a1a;margin-bottom:.9rem">
  {T("listings_title")}
  <span style="color:#303030;font-size:.75rem;margin-left:.4rem">{listings_sub}</span>
</div>
{header}
<div style="border-radius:0 0 8px 8px;overflow:hidden;
            max-height:440px;overflow-y:auto">{rows}</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  AI AGENT TAB
# ─────────────────────────────────────────────────────────────────────────────
def _chat(question: str, hash_name: str, sc: SkinScore):
    st.session_state.chat_history.append(("user", question))
    reply = agent_reply(question, hash_name, sc)
    st.session_state.chat_history.append(("assistant", reply))
    st.rerun()

def tab_agent(hash_name: str, sc: SkinScore):
    st.markdown(f"""
<div style="font-size:.8rem;color:#bbb;font-weight:600;
            padding:.3rem 0 .7rem;border-bottom:1px solid #1a1a1a;margin-bottom:1rem">
  {T("agent_title")}
  <span style="color:#303030;font-size:.75rem;margin-left:.4rem">{T("agent_sub")}</span>
</div>
<div style="font-size:.7rem;color:#383838;margin-bottom:.5rem;font-weight:500">
  {T("quick_q_label")}</div>
""", unsafe_allow_html=True)

    presets = T("presets")
    cols = st.columns(len(presets))
    for col, q in zip(cols, presets):
        with col:
            if st.button(q, key=f"pre_{q}"):
                _chat(q, hash_name, sc)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input(T("chat_placeholder"))
    if user_input:
        _chat(user_input, hash_name, sc)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        # ── Language selector ──────────────────────────────────────────────
        lang_choice = st.radio(
            "lang", LANG_OPTIONS,
            index=LANG_OPTIONS.index(st.session_state.lang),
            horizontal=True,
            label_visibility="collapsed",
        )
        if lang_choice != st.session_state.lang:
            st.session_state.lang = lang_choice
            st.rerun()

        # ── Logo ──────────────────────────────────────────────────────────
        dot_c = "#5cb85c" if st.session_state.connected else "#252525"
        ts    = st.session_state.last_fetched or T("not_connected")
        st.markdown(f"""
<div style="padding:.75rem 1rem 1rem;border-bottom:1px solid #1a1a1a">
  <div style="font-size:1.15rem;font-weight:900;color:#f0f0f0;letter-spacing:-.02em">
    SkinSense <span style="color:#e05a00">AI</span>
  </div>
  <div style="font-size:.65rem;color:#2a2a2a;margin-top:2px;letter-spacing:.06em">
    CS2 SKIN INTELLIGENCE AGENT</div>
  <div style="margin-top:.6rem;display:flex;align-items:center;gap:5px;font-size:.7rem">
    <span style="width:6px;height:6px;border-radius:50%;
                 background:{dot_c};display:inline-block;
                 box-shadow:{'0 0 6px ' + dot_c if st.session_state.connected else 'none'}"></span>
    <span style="color:{dot_c}">{ts}</span>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Current skin preview ───────────────────────────────────────────
        if st.session_state.connected and st.session_state.scores:
            sc   = st.session_state.scores
            ov   = st.session_state.overview
            ico  = st.session_state.icon_url
            hn   = st.session_state.hash_name
            c    = sc.overall_color
            lp   = ov.get("lowest_price")
            wear_abbr, wear_color = _wear(hn)
            parts = hn.split("|")
            skin = (parts[1].strip() if len(parts) > 1 else hn)
            skin_name = re.sub(r'\s*\([^)]+\)\s*$', '', skin).strip()
            img_src = _icon_src(ico)

            img_tag = (
                f'<img src="{img_src}" '
                f'style="width:100%;height:130px;object-fit:contain;'
                f'filter:drop-shadow(0 4px 16px {c}50)" />'
                if img_src else
                '<div style="width:100%;height:130px;display:flex;align-items:center;'
                'justify-content:center;font-size:3rem;color:#1e1e1e">🔫</div>'
            )

            wear_b = (
                f'<span style="background:{wear_color}18;border:1px solid {wear_color}45;'
                f'color:{wear_color};font-size:.62rem;font-weight:700;'
                f'padding:.1rem .4rem;border-radius:3px">{wear_abbr}</span>'
                if wear_abbr else ""
            )

            st.markdown(f"""
<div style="margin:.9rem .9rem .3rem;background:linear-gradient(135deg,#141414,#0f0f0f);
            border:1px solid #1e1e1e;border-radius:12px;overflow:hidden;
            position:relative">
  <div style="position:absolute;inset:0;
              background:radial-gradient(ellipse at 50% 0%,{c}0c 0%,transparent 60%);
              pointer-events:none"></div>
  <div style="position:relative;padding:.85rem .85rem .5rem;
              display:flex;align-items:center;justify-content:center">
    {img_tag}
  </div>
  <div style="padding:0 .85rem .85rem">
    <div style="display:flex;align-items:center;gap:.4rem;margin-bottom:.3rem;flex-wrap:wrap">
      <span style="font-size:.78rem;font-weight:700;color:#ddd">{skin_name}</span>
      {wear_b}
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.85rem;font-weight:800;color:#e05a00">
        {"¥" + f"{lp:,.2f}" if lp else "—"}</span>
      <div style="background:{c}15;border:1px solid {c}30;border-radius:6px;
                  padding:.15rem .5rem;display:flex;align-items:center;gap:.3rem">
        <span style="font-size:.68rem;color:#444">{T("rating_lbl")}</span>
        <span style="font-size:.85rem;font-weight:800;color:{c}">{sc.overall}</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ── Search ─────────────────────────────────────────────────────────
        with st.container():
            st.markdown(
                f'<div style="padding:0 1rem">'
                f'<div style="font-size:.68rem;color:#383838;font-weight:600;'
                f'letter-spacing:.06em;margin-bottom:.4rem">{T("search_label")}</div></div>',
                unsafe_allow_html=True)
            with st.container():
                kw = st.text_input("kw", placeholder="AK-47 Redline ...",
                                   label_visibility="collapsed")
                if st.button(T("search_btn")):
                    if kw.strip():
                        with st.spinner(""):
                            res = search_items(kw.strip(), count=10)
                        st.session_state.search_results = res.get("items", [])
                        if not st.session_state.search_results:
                            st.warning("No results" if st.session_state.lang == "English" else "未找到结果")

        if st.session_state.search_results:
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            for item in st.session_state.search_results[:8]:
                img = _icon_src(item.get("icon_url"), "96fx96f")
                price = f"¥{item['sell_price']:.2f}" if item.get("sell_price") else "—"
                img_tag = (
                    f'<img src="{img}" style="width:40px;height:30px;object-fit:contain;flex-shrink:0"/>'
                    if img else '<div style="width:40px;height:30px;flex-shrink:0"></div>'
                )
                st.markdown(f"""
<div style="margin:.25rem .75rem;background:#111;border:1px solid #1d1d1d;
            border-radius:8px;padding:.45rem .65rem;
            display:flex;align-items:center;gap:.55rem">
  {img_tag}
  <div style="flex:1;min-width:0">
    <div style="font-size:.72rem;color:#bbb;white-space:nowrap;
                overflow:hidden;text-overflow:ellipsis">{item['name']}</div>
    <div style="font-size:.68rem;color:#e05a00;margin-top:1px">{price}</div>
  </div>
</div>""", unsafe_allow_html=True)
                st.markdown('<div style="margin:0 .75rem">', unsafe_allow_html=True)
                if st.button(T("analyze_btn"), key=f"sr_{item['hash_name']}"):
                    _fetch(item["hash_name"])
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
        st.divider()

        # ── Manual hash name ───────────────────────────────────────────────
        st.markdown(
            f'<div style="padding:0 1rem">'
            f'<div style="font-size:.68rem;color:#383838;font-weight:600;'
            f'letter-spacing:.06em;margin-bottom:.4rem">{T("manual_label")}</div></div>',
            unsafe_allow_html=True)
        manual = st.text_input("manual",
                               placeholder="AWP | Dragon Lore (Field-Tested)",
                               label_visibility="collapsed")
        if st.button(T("analyze_start")):
            if manual.strip():
                _fetch(manual.strip())
            else:
                st.warning("Please enter a hash name" if st.session_state.lang == "English" else "请输入 hash name")

        st.divider()

        # ── Quick items ────────────────────────────────────────────────────
        st.markdown(
            f'<div style="padding:0 1rem">'
            f'<div style="font-size:.68rem;color:#383838;font-weight:600;'
            f'letter-spacing:.06em;margin-bottom:.5rem">{T("quick_label")}</div></div>',
            unsafe_allow_html=True)
        for label, hn in QUICK:
            wear_a, wear_c = _wear(hn)
            parts = hn.split("|")
            w_name = re.sub(r'\s*\([^)]+\)\s*$', '', parts[0].strip())
            s_name = re.sub(r'\s*\([^)]+\)\s*$', '', parts[1].strip()) if len(parts) > 1 else label
            is_active = (hn == st.session_state.hash_name)
            border_c = "#e05a00" if is_active else "#1d1d1d"
            bg_c = "#1a1000" if is_active else "#111"
            wear_b = (
                f'<span style="font-size:.6rem;color:{wear_c};'
                f'background:{wear_c}18;padding:.1rem .3rem;border-radius:2px;'
                f'font-weight:700">{wear_a}</span>'
                if wear_a else ""
            )
            st.markdown(f"""
<div style="margin:.25rem .75rem;background:{bg_c};border:1px solid {border_c};
            border-radius:8px;padding:.5rem .7rem">
  <div style="font-size:.68rem;color:#383838">{w_name}</div>
  <div style="display:flex;align-items:center;gap:.35rem;margin-top:2px">
    <span style="font-size:.78rem;font-weight:600;color:#ccc">{s_name}</span>
    {wear_b}
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("▶", key=f"q_{hn}"):
                _fetch(hn)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
def empty_state():
    ring = _score_ring(82, "#5cb85c", T("feat_score"), size=110)
    fd = T("feat_score_desc").replace("\n", "<br>")
    fm = T("feat_market_desc").replace("\n", "<br>")
    fa = T("feat_ai_desc").replace("\n", "<br>")
    st.markdown(f"""
<div style="padding:3rem 0">
  <div style="text-align:center;margin-bottom:3rem">
    <div style="font-size:2rem;font-weight:900;color:#f0f0f0;letter-spacing:-.02em">
      SkinSense <span style="color:#e05a00">AI</span>
    </div>
    <div style="font-size:.85rem;color:#333;margin-top:.4rem">{T("brand_sub")}</div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;
              max-width:680px;margin:0 auto 3rem">

    <div style="background:#111;border:1px solid #1d1d1d;border-radius:12px;
                padding:1.25rem;text-align:center">
      <div style="margin-bottom:.75rem">{ring}</div>
      <div style="font-size:.85rem;font-weight:700;color:#ccc;margin-bottom:.3rem">{T("feat_score")}</div>
      <div style="font-size:.72rem;color:#333;line-height:1.5">{fd}</div>
    </div>

    <div style="background:#111;border:1px solid #1d1d1d;border-radius:12px;
                padding:1.25rem;text-align:center">
      <div style="font-size:2.5rem;margin-bottom:.6rem;opacity:.35">📈</div>
      <div style="font-size:.85rem;font-weight:700;color:#ccc;margin-bottom:.3rem">{T("feat_market")}</div>
      <div style="font-size:.72rem;color:#333;line-height:1.5">{fm}</div>
    </div>

    <div style="background:#111;border:1px solid #1d1d1d;border-radius:12px;
                padding:1.25rem;text-align:center">
      <div style="font-size:2.5rem;margin-bottom:.6rem;opacity:.35">🤖</div>
      <div style="font-size:.85rem;font-weight:700;color:#ccc;margin-bottom:.3rem">{T("feat_ai")}</div>
      <div style="font-size:.72rem;color:#333;line-height:1.5">{fa}</div>
    </div>

  </div>

  <div style="text-align:center;border:1px dashed #1a1a1a;border-radius:12px;
              padding:1.5rem;max-width:400px;margin:0 auto">
    <div style="font-size:.85rem;color:#333;margin-bottom:.3rem">{T("empty_hint")}</div>
    <div style="font-size:.72rem;color:#222">{T("empty_sub")}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    _init()
    render_sidebar()

    # top nav
    st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:.85rem 0 .7rem;border-bottom:1px solid #181818;margin-bottom:1.5rem">
  <div style="display:flex;align-items:center;gap:.45rem">
    <span style="font-size:.72rem;font-weight:700;color:#2a2a2a;letter-spacing:.07em">
      SKINSENSE AI</span>
    <span style="color:#1d1d1d;font-size:.8rem">/</span>
    <span style="font-size:.72rem;color:#2f2f2f">{T("nav_tagline")}</span>
  </div>
  <span style="font-size:.65rem;color:#1e1e1e">{T("nav_data_src")}</span>
</div>""", unsafe_allow_html=True)

    if not st.session_state.scores:
        empty_state()
        return

    ov  = st.session_state.overview
    ls  = st.session_state.listings
    sc  = st.session_state.scores
    hn  = st.session_state.hash_name
    ico = st.session_state.icon_url

    hero_section(hn, ov, sc, icon_url=ico)

    col_score, col_data = st.columns([1, 2], gap="large")

    with col_score:
        score_panel(sc)

    with col_data:
        t1, t2, t3 = st.tabs([T("tab_market"), T("tab_listings"), T("tab_agent")])
        with t1: tab_market(ov, ls, sc)
        with t2: tab_listings(ls, ov)
        with t3: tab_agent(hn, sc)


main()
