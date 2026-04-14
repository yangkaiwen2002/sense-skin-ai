"""
SkinSense · CS2 Skin AI Agent
Steam Market data + rule-based scoring + AI chat

Run: streamlit run streamlit_app.py  (from backend/)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from data_sources.steam_client import (
    fetch_price_overview,
    fetch_listings,
    search_items,
)
from scoring import compute, agent_reply, SkinScore

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkinSense AI",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html,body,[class*="css"]{ font-family:'Inter',-apple-system,sans-serif; }
.stApp{ background:#0f0f0f; }
.block-container{ padding:0 1.5rem 2rem !important; max-width:100% !important; }
#MainMenu,footer,header{ visibility:hidden; }

/* sidebar */
section[data-testid="stSidebar"]{ background:#111; border-right:1px solid #1e1e1e; }

/* inputs */
.stTextInput input,.stNumberInput input{
    background:#1a1a1a !important; border:1px solid #2a2a2a !important;
    border-radius:6px !important; color:#e0e0e0 !important; font-size:.85rem !important;
}
.stTextInput input:focus,.stNumberInput input:focus{
    border-color:#e05a00 !important; box-shadow:0 0 0 2px rgba(224,90,0,.15) !important;
}
div[data-baseweb="select"]>div{
    background:#1a1a1a !important; border:1px solid #2a2a2a !important;
    border-radius:6px !important; color:#e0e0e0 !important;
}

/* buttons */
.stButton>button{
    background:#e05a00; border:none; border-radius:6px; color:#fff;
    font-weight:600; font-size:.83rem; padding:.45rem 1rem;
    transition:background .15s; width:100%;
}
.stButton>button:hover{ background:#f06510; }
.stButton>button[kind="secondary"]{
    background:#1e1e1e; border:1px solid #2a2a2a; color:#888;
}
.stButton>button[kind="secondary"]:hover{ background:#252525; color:#ddd; }

/* metrics */
[data-testid="metric-container"]{
    background:#161616; border:1px solid #222;
    border-radius:8px; padding:1rem 1.1rem;
}
[data-testid="stMetricLabel"]>div{
    color:#555 !important; font-size:.73rem !important;
    font-weight:500 !important;
}
[data-testid="stMetricValue"]{
    color:#fff !important; font-size:1.4rem !important; font-weight:700 !important;
}

/* tabs */
.stTabs [data-baseweb="tab-list"]{
    background:transparent !important; border-bottom:1px solid #1e1e1e; gap:0; padding:0;
}
.stTabs [data-baseweb="tab"]{
    background:transparent !important; border:none;
    border-bottom:2px solid transparent; border-radius:0 !important;
    color:#555; font-size:.85rem; font-weight:500; padding:.6rem 1.25rem; transition:all .15s;
}
.stTabs [data-baseweb="tab"]:hover{ color:#ccc; }
.stTabs [aria-selected="true"]{
    color:#e05a00 !important; border-bottom:2px solid #e05a00 !important;
    background:transparent !important;
}
.stTabs [data-baseweb="tab-panel"]{ padding:1.25rem 0 0; }

/* chat messages */
[data-testid="stChatMessage"]{ background:#161616; border:1px solid #1e1e1e; border-radius:8px; }

/* scrollbar */
::-webkit-scrollbar{ width:5px; height:5px; }
::-webkit-scrollbar-track{ background:#0f0f0f; }
::-webkit-scrollbar-thumb{ background:#252525; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  QUICK ITEMS
# ─────────────────────────────────────────────────────────────────────────────
QUICK = [
    ("AK-47 | 红线 FT",    "AK-47 | Redline (Field-Tested)"),
    ("AWP | 龙狙 FT",      "AWP | Dragon Lore (Field-Tested)"),
    ("沙漠之鹰 | 火焰 FN", "Desert Eagle | Blaze (Factory New)"),
    ("M4A4 | 嚎叫 FT",     "M4A4 | Howl (Field-Tested)"),
    ("蝴蝶刀 | 渐变 FN",   "Butterfly Knife | Fade (Factory New)"),
    ("格洛克 | 渐变 FN",   "Glock-18 | Fade (Factory New)"),
]

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init():
    for k, v in {
        "hash_name": "", "overview": None, "listings": None,
        "scores": None, "search_results": [],
        "chat_history": [], "last_fetched": None, "connected": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _fetch(hash_name: str):
    with st.spinner("获取价格概览..."):
        ov = fetch_price_overview(hash_name)
    if not ov.get("ok"):
        st.error(f"Steam API 错误：{ov.get('error')}"); return
    with st.spinner("拉取挂单数据..."):
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
        chat_history=[], last_fetched=datetime.now().strftime("%H:%M:%S"),
        connected=True,
    )
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def score_color(s: int) -> str:
    if s >= 75: return "#5cb85c"
    if s >= 55: return "#f0ad4e"
    return "#d9534f"

def overall_card(sc: SkinScore):
    c = sc.overall_color
    st.markdown(f"""
    <div style="text-align:center;padding:1.5rem 0 1rem">
        <div style="
            width:130px;height:130px;border-radius:50%;
            border:4px solid {c};background:{c}15;
            display:flex;flex-direction:column;
            align-items:center;justify-content:center;
            margin:0 auto;box-shadow:0 0 32px {c}25">
            <div style="font-size:2.4rem;font-weight:800;color:{c};line-height:1">
                {sc.overall}</div>
            <div style="font-size:.65rem;color:#555;letter-spacing:.12em;
                        text-transform:uppercase;margin-top:2px">SCORE</div>
        </div>
        <div style="margin-top:.9rem;font-size:.95rem;font-weight:700;color:{c}">
            {sc.overall_label}</div>
        <div style="font-size:.72rem;color:#444;margin-top:3px">Overall Rating</div>
    </div>
    """, unsafe_allow_html=True)

def sub_score_bar(label: str, en: str, score: int, note: str):
    c = score_color(score)
    st.markdown(f"""
    <div style="margin-bottom:1.1rem">
        <div style="display:flex;justify-content:space-between;
                    align-items:baseline;margin-bottom:4px">
            <div>
                <span style="font-size:.82rem;font-weight:600;color:#ccc">{label}</span>
                <span style="font-size:.68rem;color:#444;margin-left:5px">{en}</span>
            </div>
            <span style="font-size:.95rem;font-weight:700;color:{c}">{score}</span>
        </div>
        <div style="background:#1a1a1a;border-radius:3px;height:5px;margin-bottom:4px">
            <div style="background:{c};width:{score}%;height:5px;
                        border-radius:3px;transition:width .4s ease"></div>
        </div>
        <div style="font-size:.72rem;color:#555;line-height:1.4">{note}</div>
    </div>
    """, unsafe_allow_html=True)

def score_panel(sc: SkinScore):
    overall_card(sc)
    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.68rem;font-weight:600;color:#333;'
        'letter-spacing:.1em;text-transform:uppercase;'
        'padding-bottom:.5rem;border-bottom:1px solid #1a1a1a;margin-bottom:.9rem">'
        'Sub Scores</div>', unsafe_allow_html=True)
    sub_score_bar("价值",  "Value",     sc.value,     sc.value_note)
    sub_score_bar("流动性","Liquidity", sc.liquidity, sc.liquidity_note)
    sub_score_bar("稳定性","Stability", sc.stability, sc.stability_note)
    sub_score_bar("趋势",  "Trend",     sc.trend,     sc.trend_note)

def item_header(hash_name: str, ov: dict, sc: SkinScore):
    lp  = ov.get("lowest_price")
    mp  = ov.get("median_price")
    vol = ov.get("volume")
    parts = hash_name.split("|")
    weapon = parts[0].strip() if parts else ""
    skin   = parts[1].strip() if len(parts) > 1 else hash_name
    c = sc.overall_color

    st.markdown(f"""
    <div style="background:#141414;border:1px solid #1e1e1e;border-radius:10px;
                padding:1.1rem 1.4rem;margin-bottom:1.25rem;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem">
        <div>
            <div style="font-size:1.3rem;font-weight:800;color:#f0f0f0;line-height:1.2">
                {skin}</div>
            <div style="font-size:.78rem;color:#444;margin-top:3px">{weapon}</div>
        </div>
        <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap">
            <div style="text-align:right">
                <div style="font-size:.68rem;color:#444;margin-bottom:1px">最低在售价</div>
                <div style="font-size:1.8rem;font-weight:800;color:#e05a00;line-height:1">
                    {"¥" + f"{lp:.2f}" if lp else "—"}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:.68rem;color:#444;margin-bottom:1px">均价</div>
                <div style="font-size:1.1rem;font-weight:600;color:#aaa">
                    {"¥" + f"{mp:.2f}" if mp else "—"}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:.68rem;color:#444;margin-bottom:1px">24h 成交量</div>
                <div style="font-size:1.1rem;font-weight:600;color:#aaa">
                    {f"{vol:,}" if vol else "—"}</div>
            </div>
            <div style="background:{c}15;border:1px solid {c}40;border-radius:6px;
                        padding:.35rem .75rem;text-align:center">
                <div style="font-size:.65rem;color:#555;margin-bottom:1px">RATING</div>
                <div style="font-size:1rem;font-weight:800;color:{c}">{sc.overall}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

def section_hdr(text: str, sub: str = ""):
    s = f'<span style="color:#444;font-size:.78rem;margin-left:.5rem">{sub}</span>' if sub else ""
    st.markdown(
        f'<div style="font-size:.85rem;font-weight:600;color:#ccc;'
        f'padding:.5rem 0 .75rem;border-bottom:1px solid #1a1a1a;margin-bottom:.9rem">'
        f'{text}{s}</div>', unsafe_allow_html=True)

def stat_grid(items: list[tuple[str,str]]):
    cols = st.columns(len(items))
    for col, (label, val) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div style="background:#141414;border:1px solid #1e1e1e;border-radius:8px;
                        padding:.7rem .9rem;text-align:center">
                <div style="font-size:.68rem;color:#444;margin-bottom:3px">{label}</div>
                <div style="font-size:1rem;font-weight:700;color:#ddd">{val}</div>
            </div>""", unsafe_allow_html=True)

def empty_state(msg="在左侧搜索饰品并点击「分析」开始"):
    st.markdown(f"""
    <div style="text-align:center;padding:5rem 0;
                border:1px dashed #1a1a1a;border-radius:10px;margin:1rem 0">
        <div style="font-size:2.5rem;margin-bottom:.75rem">🔫</div>
        <div style="font-size:.9rem;color:#333">{msg}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        dot_c = "#5cb85c" if st.session_state.connected else "#333"
        ts    = st.session_state.last_fetched or "未连接"
        st.markdown(f"""
        <div style="padding:1.25rem .75rem 1rem;border-bottom:1px solid #1a1a1a">
            <div style="font-size:1.2rem;font-weight:800;color:#f0f0f0;letter-spacing:-.01em">
                🔫 SkinSense <span style="color:#e05a00">AI</span>
            </div>
            <div style="font-size:.68rem;color:#333;margin-top:3px;letter-spacing:.05em">
                CS2 Skin Intelligence Agent
            </div>
            <div style="margin-top:.6rem;display:flex;align-items:center;gap:5px;
                        font-size:.72rem;color:{dot_c}">
                <span style="width:6px;height:6px;border-radius:50%;
                             background:{dot_c};display:inline-block"></span>
                {ts}
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

        # search
        st.markdown('<div style="font-size:.72rem;color:#444;margin-bottom:.3rem;font-weight:500">搜索饰品</div>', unsafe_allow_html=True)
        kw = st.text_input("kw", placeholder="AK-47 Redline ...", label_visibility="collapsed")
        if st.button("🔍 搜索"):
            if kw:
                with st.spinner(""):
                    res = search_items(kw, count=12)
                st.session_state.search_results = res.get("items", [])
                if not st.session_state.search_results:
                    st.warning("未找到结果")

        if st.session_state.search_results:
            opts = st.session_state.search_results
            idx  = st.selectbox(
                "sel", range(len(opts)),
                format_func=lambda i: f"{opts[i]['name']}  ¥{opts[i]['sell_price'] or '—'}",
                label_visibility="collapsed",
            )
            if st.button("分析该饰品"):
                _fetch(opts[idx]["hash_name"])

        st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
        st.divider()

        # manual
        st.markdown('<div style="font-size:.72rem;color:#444;margin-bottom:.3rem;font-weight:500">直接输入 Hash Name</div>', unsafe_allow_html=True)
        manual = st.text_input("manual", placeholder="AWP | Dragon Lore (Field-Tested)",
                               label_visibility="collapsed")
        if st.button("⚡ 开始分析"):
            if manual.strip():
                _fetch(manual.strip())
            else:
                st.warning("请输入 hash name")

        st.divider()

        # quick
        st.markdown('<div style="font-size:.72rem;color:#444;margin-bottom:.4rem;font-weight:500">快速分析</div>', unsafe_allow_html=True)
        for label, hn in QUICK:
            if st.button(label, key=hn):
                _fetch(hn)

# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────
def tab_market(ov: dict, ls: dict, sc: SkinScore):
    lp  = ov.get("lowest_price")
    mp  = ov.get("median_price")
    vol = ov.get("volume")
    tot = ls.get("total", 0)
    prices = [l["price"] for l in ls.get("listings", [])]

    spread = round(lp - (mp * 0.87), 2) if lp and mp else None  # ~13% Steam fee proxy

    stat_grid([
        ("最低在售价",  f"¥{lp:.2f}" if lp else "—"),
        ("中位在售价",  f"¥{mp:.2f}" if mp else "—"),
        ("24h 成交量",  f"{vol:,}"   if vol else "—"),
        ("总挂单量",    f"{tot:,}"   if tot else "—"),
        ("价格标准差",  f"¥{sc.price_std:.2f}" if sc.price_std else "—"),
    ])

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        section_hdr("价格分布", f"基于 {len(prices)} 条挂单")
        if prices:
            mn, mx = min(prices), max(prices)
            if mn < mx:
                edges  = np.linspace(mn, mx, 20)
                counts, bins = np.histogram(prices, bins=edges)
                df = pd.DataFrame({"数量": counts},
                                   index=[f"¥{b:.0f}" for b in bins[:-1]])
                st.bar_chart(df, color="#e05a00", height=200)
            else:
                st.caption("所有挂单价格相同")
        else:
            st.caption("暂无挂单数据")

    with col_b:
        section_hdr("价格区间")
        if prices:
            p_arr = np.array(prices)
            for pct, label, color in [
                (10, "低价区 P10", "#5cb85c"),
                (25, "P25",       "#7ec87e"),
                (50, "中位 P50",  "#f0ad4e"),
                (75, "P75",       "#e07b39"),
                (90, "高价区 P90","#d9534f"),
            ]:
                val = np.percentile(p_arr, pct)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                            padding:.35rem 0;border-bottom:1px solid #141414">
                    <span style="font-size:.8rem;color:#555">{label}</span>
                    <span style="font-size:.9rem;font-weight:600;color:{color}">
                        ¥ {val:.2f}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("暂无数据")


def tab_listings(ls: dict):
    listings = ls.get("listings", [])
    if not listings:
        st.markdown('<div style="color:#333;font-size:.85rem;padding:2rem 0;'
                    'text-align:center">暂无挂单数据</div>', unsafe_allow_html=True)
        return

    section_hdr("在售挂单", f"共 {ls.get('total',0):,} 条 · 显示最低价前 {len(listings)} 条")

    # table header
    st.markdown("""
    <div style="display:grid;grid-template-columns:3rem 1fr 6rem;
                gap:0;padding:.4rem .9rem;background:#141414;
                border:1px solid #1e1e1e;border-radius:6px 6px 0 0;
                font-size:.7rem;color:#444;font-weight:600;letter-spacing:.05em">
        <div>#</div><div>Listing ID</div>
        <div style="text-align:right">价格</div>
    </div>""", unsafe_allow_html=True)

    rows = ""
    for i, l in enumerate(listings[:50]):
        bg = "#111" if i % 2 == 0 else "#131313"
        rows += f"""
        <div style="display:grid;grid-template-columns:3rem 1fr 6rem;
                    gap:0;padding:.5rem .9rem;background:{bg};
                    border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;
                    border-bottom:1px solid #161616;align-items:center">
            <div style="color:#333;font-size:.7rem">{i+1:02d}</div>
            <div style="font-size:.72rem;color:#444;font-family:monospace">
                {l['listing_id'][:16]}…</div>
            <div style="text-align:right;font-size:.95rem;font-weight:700;color:#e05a00">
                ¥ {l['price']:.2f}</div>
        </div>"""

    st.markdown(
        f'<div style="border-radius:0 0 6px 6px;overflow:hidden;'
        f'max-height:420px;overflow-y:auto">{rows}</div>',
        unsafe_allow_html=True,
    )


def tab_agent(hash_name: str, sc: SkinScore):
    # preset prompts
    section_hdr("AI 饰品分析师", "基于评分数据实时回答")

    st.markdown("""
    <div style="background:#141414;border:1px solid #1e1e1e;border-radius:8px;
                padding:.75rem 1rem;margin-bottom:1rem;
                display:flex;flex-wrap:wrap;gap:.5rem;align-items:center">
        <span style="font-size:.72rem;color:#444;font-weight:500">快速提问：</span>
    </div>""", unsafe_allow_html=True)

    presets = ["这个饰品值得买吗？", "为什么分数低？", "适合长期持有吗？",
               "好不好出手？", "综合帮我分析一下"]
    cols = st.columns(len(presets))
    for col, q in zip(cols, presets):
        with col:
            if st.button(q, key=f"preset_{q}"):
                _chat(q, hash_name, sc)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # chat history
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    # input
    user_input = st.chat_input("问我任何关于这个饰品的问题…")
    if user_input:
        _chat(user_input, hash_name, sc)

def _chat(question: str, hash_name: str, sc: SkinScore):
    st.session_state.chat_history.append(("user", question))
    reply = agent_reply(question, hash_name, sc)
    st.session_state.chat_history.append(("assistant", reply))
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    _init()
    render_sidebar()

    # top bar
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:.9rem 0 .75rem;border-bottom:1px solid #1a1a1a;margin-bottom:1.25rem">
        <div style="display:flex;align-items:center;gap:.5rem">
            <span style="font-size:.75rem;font-weight:600;color:#333;letter-spacing:.05em">
                SKINSENSE AI</span>
            <span style="color:#1e1e1e">/</span>
            <span style="font-size:.75rem;color:#444">CS2 · Skin Intelligence</span>
        </div>
        <span style="font-size:.68rem;color:#222">
            Data: Steam Community Market · No login required</span>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.scores:
        empty_state()
        return

    ov = st.session_state.overview
    ls = st.session_state.listings
    sc = st.session_state.scores
    hn = st.session_state.hash_name

    # item header
    item_header(hn, ov, sc)

    # score panel + tabs
    col_score, col_data = st.columns([1, 2], gap="large")

    with col_score:
        st.markdown(
            '<div style="background:#111;border:1px solid #1e1e1e;'
            'border-radius:10px;padding:1rem 1.25rem">',
            unsafe_allow_html=True,
        )
        score_panel(sc)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_data:
        t1, t2, t3 = st.tabs(["📈  市场数据", "📋  挂单列表", "🤖  AI 对话"])
        with t1: tab_market(ov, ls, sc)
        with t2: tab_listings(ls)
        with t3: tab_agent(hn, sc)


main()
