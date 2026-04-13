"""
SkinSense · BUFF Market Intelligence
CS2 饰品市场分析面板

Run from backend/:
    streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from data_sources.buff_client import (
    fetch_buff_sell_orders,
    fetch_buff_goods_info,
    fetch_buff_search,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="SkinSense · Market",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CSS — CS2 / BUFF market aesthetic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── base & reset ─────────────────────────────────────────────────────── */
html, body { margin: 0; }
.stApp {
    background: #0a0e13;
    background-image:
        radial-gradient(ellipse at 20% 0%, rgba(77,182,212,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(207,106,50,0.04) 0%, transparent 50%);
}
.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 100% !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0d1520;
    border-right: 1px solid #1a2d42;
    padding-top: 0;
}
section[data-testid="stSidebar"] > div { padding-top: 0; }

/* ── inputs ───────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input {
    background: #0a1220 !important;
    border: 1px solid #1e3a54 !important;
    border-radius: 4px !important;
    color: #c6d4df !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 0.75rem !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #4db6d4 !important;
    box-shadow: 0 0 0 1px rgba(77,182,212,0.2) !important;
}
.stSelectbox > div > div {
    background: #0a1220 !important;
    border: 1px solid #1e3a54 !important;
    border-radius: 4px !important;
    color: #c6d4df !important;
}

/* ── buttons ──────────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent;
    border: 1px solid #4db6d4;
    border-radius: 3px;
    color: #4db6d4;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.4rem 1rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: rgba(77,182,212,0.12);
    border-color: #7ecfe0;
    color: #7ecfe0;
}
.stButton > button[kind="primary"] {
    background: #cf6a32;
    border-color: #cf6a32;
    color: #fff;
}
.stButton > button[kind="primary"]:hover {
    background: #e07a40;
    border-color: #e07a40;
}

/* ── metrics ──────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #111822;
    border: 1px solid #1a2d42;
    border-top: 2px solid #cf6a32;
    border-radius: 0 0 4px 4px;
    padding: 0.9rem 1rem 0.75rem;
}
[data-testid="stMetricLabel"] > div {
    color: #7ea0b7 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #c6d4df !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}

/* ── tabs ─────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1a2d42;
    gap: 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0 !important;
    color: #7ea0b7;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 0.6rem 1.4rem;
    text-transform: uppercase;
    transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover { color: #c6d4df; background: rgba(255,255,255,0.03) !important; }
.stTabs [aria-selected="true"] {
    color: #4db6d4 !important;
    border-bottom: 2px solid #4db6d4 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 1.25rem 0 0 0; }

/* ── dataframe ────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a2d42;
    border-radius: 4px;
    overflow: hidden;
}
[data-testid="stDataFrame"] th {
    background: #0d1520 !important;
    color: #7ea0b7 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* ── checkbox ─────────────────────────────────────────────────────────── */
.stCheckbox > label { color: #7ea0b7; font-size: 0.82rem; }

/* ── slider ───────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [data-testid="stThumbValue"] { color: #4db6d4; }

/* ── divider ──────────────────────────────────────────────────────────── */
hr { border-color: #1a2d42 !important; margin: 0.75rem 0 !important; }

/* ── expander ─────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #111822;
    border: 1px solid #1a2d42;
    border-radius: 4px;
}
[data-testid="stExpander"] summary {
    color: #7ea0b7;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0e13; }
::-webkit-scrollbar-thumb { background: #1e3a54; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2a4f70; }
</style>
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTML COMPONENT HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# CS2 rarity colours ─ used for item card borders / accents
RARITY = {
    "Consumer":    "#b0c3d9",
    "Industrial":  "#5e98d9",
    "Mil-Spec":    "#4b69ff",
    "Restricted":  "#8847ff",
    "Classified":  "#d32ce6",
    "Covert":      "#eb4b4b",
    "Contraband":  "#e4ae39",
}

WEAR_LABEL = {
    (0.00, 0.07): ("FN", "崭新出厂", "#4db6d4"),
    (0.07, 0.15): ("MW", "略有磨损", "#5ba642"),
    (0.15, 0.38): ("FT", "久经沙场", "#c6b441"),
    (0.38, 0.45): ("WW", "破损不堪", "#cf6a32"),
    (0.45, 1.00): ("BS", "战痕累累", "#c23b22"),
}

def wear_info(w: float | None):
    if w is None:
        return "—", "—", "#7ea0b7"
    for (lo, hi), (short, zh, color) in WEAR_LABEL.items():
        if lo <= w < hi:
            return short, zh, color
    return "BS", "战痕累累", "#c23b22"


def panel_header(title: str, subtitle: str = "", accent: str = "#4db6d4"):
    """Section divider styled like a CS2 UI panel label."""
    sub_html = f'<span style="color:#4a6580;font-size:0.72rem;margin-left:0.75rem;font-family:Inter,sans-serif;font-weight:400">{subtitle}</span>' if subtitle else ""
    st.markdown(f"""
    <div style="
        display:flex;align-items:center;gap:0;
        margin:0.25rem 0 0.9rem;padding-bottom:0.5rem;
        border-bottom:1px solid #1a2d42;">
        <span style="
            background:{accent};width:3px;height:1rem;
            border-radius:1px;margin-right:0.6rem;display:inline-block"></span>
        <span style="
            font-family:'Rajdhani',sans-serif;font-weight:700;
            font-size:0.82rem;letter-spacing:0.1em;text-transform:uppercase;
            color:#c6d4df">{title}</span>
        {sub_html}
    </div>""", unsafe_allow_html=True)


def sidebar_label(text: str):
    st.markdown(
        f'<div style="font-family:Rajdhani,sans-serif;font-size:0.7rem;font-weight:700;'
        f'letter-spacing:0.1em;text-transform:uppercase;color:#4a6580;'
        f'margin:0.9rem 0 0.25rem">{text}</div>',
        unsafe_allow_html=True,
    )


def live_badge(ok: bool, ts: str | None = None):
    if ok:
        dot, label, color = "●", "LIVE", "#5ba642"
    else:
        dot, label, color = "●", "OFFLINE", "#c23b22"
    ts_html = f'<span style="color:#4a6580;margin-left:6px;font-size:0.65rem">{ts}</span>' if ts else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:5px;'
        f'font-family:Rajdhani,sans-serif;font-weight:700;font-size:0.72rem;'
        f'letter-spacing:0.08em;color:{color}">'
        f'<span style="font-size:0.55rem;animation:pulse 2s infinite">{dot}</span>'
        f'&nbsp;{label}{ts_html}</div>',
        unsafe_allow_html=True,
    )


def item_card_html(name_zh: str, name_en: str, sell_min: float | None,
                   buy_max: float | None, sell_num: int | None,
                   rarity_color: str = "#eb4b4b") -> str:
    """Big item display card — like a CS2 inventory inspect panel."""
    spread = round(sell_min - buy_max, 2) if sell_min and buy_max else None
    spread_pct = round(spread / buy_max * 100, 1) if spread and buy_max else None
    spread_str = f"¥{spread:.2f}  ({spread_pct}%)" if spread else "—"

    return f"""
    <div style="
        background:linear-gradient(135deg,#111822 60%,#0d1824 100%);
        border:1px solid #1a2d42;border-left:3px solid {rarity_color};
        border-radius:4px;padding:1.2rem 1.4rem;margin-bottom:1rem;
        box-shadow:0 4px 24px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03)">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.8rem">
            <div>
                <div style="
                    font-family:'Rajdhani',sans-serif;font-weight:700;
                    font-size:1.35rem;color:#e8eef2;letter-spacing:0.01em;
                    line-height:1.1">{name_zh or "—"}</div>
                <div style="
                    font-family:'Inter',sans-serif;font-size:0.72rem;
                    color:#4a6580;margin-top:3px;letter-spacing:0.03em">{name_en or ""}</div>
            </div>
            <div style="
                background:rgba(207,106,50,0.1);border:1px solid rgba(207,106,50,0.3);
                border-radius:3px;padding:2px 8px;
                font-family:'Rajdhani',sans-serif;font-weight:700;
                font-size:0.68rem;letter-spacing:0.12em;color:#cf6a32;
                text-transform:uppercase;white-space:nowrap">BUFF · CSGO</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:0;
                    border:1px solid #1a2d42;border-radius:3px;overflow:hidden">
            {_stat_cell("最低卖价", f"¥ {sell_min:.2f}" if sell_min else "—", "#cf6a32", True)}
            {_stat_cell("最高求购", f"¥ {buy_max:.2f}" if buy_max else "—", "#5ba642", False)}
            {_stat_cell("买卖价差", spread_str, "#4db6d4", False)}
            {_stat_cell("挂单数量", f"{sell_num:,} 件" if sell_num else "—", "#c6d4df", False)}
        </div>
    </div>"""


def _stat_cell(label: str, value: str, color: str, first: bool) -> str:
    border = "" if first else "border-left:1px solid #1a2d42;"
    return f"""
    <div style="padding:0.65rem 0.9rem;background:#0d1520;{border}">
        <div style="font-family:'Rajdhani',sans-serif;font-size:0.65rem;font-weight:700;
                    letter-spacing:0.1em;text-transform:uppercase;color:#4a6580;
                    margin-bottom:3px">{label}</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.05rem;
                    font-weight:700;color:{color}">{value}</div>
    </div>"""


def order_row_html(idx: int, price: float, wear: float | None,
                   seed: int | None, stickers: list[str],
                   cooldown: str | None) -> str:
    w_short, w_zh, w_color = wear_info(wear)
    wear_str = f"{wear:.6f}" if wear is not None else "—"
    sticker_html = ""
    for s in stickers[:3]:
        sticker_html += (
            f'<span style="background:rgba(136,71,255,0.12);border:1px solid rgba(136,71,255,0.3);'
            f'border-radius:2px;padding:1px 5px;font-size:0.65rem;color:#a87fef;'
            f'margin-right:3px">{s}</span>'
        )
    if len(stickers) > 3:
        sticker_html += f'<span style="color:#4a6580;font-size:0.65rem">+{len(stickers)-3}</span>'

    tradable = not cooldown or cooldown == "可交易"
    td_color  = "#5ba642" if tradable else "#cf6a32"
    td_label  = "✓" if tradable else "⏱"

    bg = "#0d1520" if idx % 2 == 0 else "#0a1118"

    return f"""
    <div style="
        display:grid;grid-template-columns:2.5rem 6rem 7rem 5rem 1fr 4rem;
        gap:0;align-items:center;padding:0.5rem 0.9rem;
        background:{bg};border-bottom:1px solid rgba(26,45,66,0.5);
        font-family:'Inter',sans-serif;font-size:0.8rem">
        <div style="color:#4a6580;font-size:0.7rem">{idx+1:02d}</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;
                    font-weight:700;color:#cf6a32">¥ {price:.2f}</div>
        <div>
            <span style="color:{w_color};font-family:'Rajdhani',sans-serif;
                         font-weight:700;font-size:0.78rem">{w_short}</span>
            <span style="color:#4a6580;font-size:0.68rem;margin-left:4px">{wear_str}</span>
        </div>
        <div style="color:#7ea0b7;font-size:0.72rem">{f"#{seed}" if seed else "—"}</div>
        <div>{sticker_html if sticker_html else '<span style="color:#2a3d52">—</span>'}</div>
        <div style="color:{td_color};font-size:0.8rem;text-align:right">{td_label}</div>
    </div>"""


def price_histogram_html(orders: list[dict]) -> None:
    """Render a simple ASCII-style bar chart using st.bar_chart."""
    prices = [o["price"] for o in orders]
    if not prices:
        return
    mn, mx = min(prices), max(prices)
    if mn == mx:
        st.bar_chart(pd.DataFrame({"价格": [mn], "数量": [len(prices)]}).set_index("价格"))
        return
    bins = np.linspace(mn, mx, 16)
    counts, edges = np.histogram(prices, bins=bins)
    labels = [f"¥{e:.0f}" for e in edges[:-1]]
    df = pd.DataFrame({"分布": counts}, index=labels)
    st.bar_chart(df, color="#cf6a32", height=180)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _init():
    defaults = {
        "goods_id": 38211,
        "goods_info": None,
        "orders_data": None,
        "search_results": [],
        "last_fetched": None,
        "connected": False,
        "page_num": 1,
        "sort_by": "default",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _fetch(goods_id: int, page_num: int, sort_by: str):
    with st.spinner("正在连接 BUFF 服务器..."):
        info = fetch_buff_goods_info(goods_id)
    if not info.get("ok"):
        st.session_state.connected = False
        return False, info.get("error")
    with st.spinner("拉取卖单数据..."):
        orders = fetch_buff_sell_orders(goods_id, page_num=page_num, sort_by=sort_by)
    if not orders.get("ok"):
        st.session_state.connected = False
        return False, orders.get("error")
    st.session_state.update(
        goods_id=goods_id, goods_info=info, orders_data=orders,
        page_num=page_num, sort_by=sort_by,
        last_fetched=datetime.now().strftime("%H:%M:%S"), connected=True,
    )
    return True, None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_sidebar():
    with st.sidebar:

        # ── logo ──────────────────────────────────────────────────────────
        st.markdown("""
        <div style="
            padding:1.4rem 1rem 1rem;
            border-bottom:1px solid #1a2d42;
            margin-bottom:0.25rem">
            <div style="
                font-family:'Rajdhani',sans-serif;font-weight:700;
                font-size:1.35rem;letter-spacing:0.04em;color:#e8eef2">
                ⚔&nbsp; SKIN<span style="color:#cf6a32">SENSE</span>
            </div>
            <div style="
                font-family:'Inter',sans-serif;font-size:0.65rem;
                letter-spacing:0.15em;text-transform:uppercase;
                color:#4a6580;margin-top:2px">
                BUFF · Market Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── connection status ──────────────────────────────────────────────
        live_badge(st.session_state.connected, st.session_state.last_fetched)
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        # ── search ────────────────────────────────────────────────────────
        sidebar_label("🔍  Search Item")
        keyword = st.text_input("keyword", placeholder="AK-47 Redline ...",
                                label_visibility="collapsed", key="kw")
        if st.button("SEARCH", use_container_width=True):
            if keyword:
                with st.spinner("搜索中..."):
                    res = fetch_buff_search(keyword)
                st.session_state.search_results = res.get("items", []) if res["ok"] else []
                if not st.session_state.search_results:
                    st.warning("未找到结果，请检查 BUFF_COOKIE")

        if st.session_state.search_results:
            opts = st.session_state.search_results[:10]
            choice = st.selectbox(
                "选择结果",
                range(len(opts)),
                format_func=lambda i: (opts[i]["name_zh"] or opts[i]["name"] or "—"),
                label_visibility="collapsed",
            )
            if st.button("LOAD  →", use_container_width=True, type="primary"):
                st.session_state.goods_id = opts[choice]["goods_id"]
                st.session_state.search_results = []
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── goods id & controls ───────────────────────────────────────────
        sidebar_label("⚙  Query Config")
        goods_id = st.number_input(
            "Goods ID", value=st.session_state.goods_id,
            step=1, label_visibility="visible",
        )

        sort_map = {
            "综合排序":     "default",
            "价格 ↑":      "price.asc",
            "价格 ↓":      "price.desc",
            "磨损 ↑":      "paintwear.asc",
            "磨损 ↓":      "paintwear.desc",
        }
        sort_label = st.selectbox("排序方式", list(sort_map.keys()), label_visibility="visible")

        col_pg, col_sz = st.columns(2)
        with col_pg:
            page_num = st.number_input("页码", value=st.session_state.page_num,
                                       min_value=1, step=1)

        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        if st.button("⚡  FETCH DATA", use_container_width=True, type="primary"):
            ok, err = _fetch(int(goods_id), int(page_num), sort_map[sort_label])
            if not ok:
                st.error(f"请求失败：{err}")
                st.caption("请检查 backend/.env 中的 BUFF_COOKIE")

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── quick ids ─────────────────────────────────────────────────────
        sidebar_label("⭐  Quick Access")
        QUICK = [
            ("AWP | 龙狙 FT",    38211),
            ("AK-47 | 红线 FT",  3004),
            ("蝴蝶刀 | 渐变",    42944),
        ]
        for label, gid in QUICK:
            if st.button(label, use_container_width=True, key=f"q{gid}"):
                ok, err = _fetch(gid, 1, "default")
                if not ok:
                    st.error(err)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tab_market(info: dict, odata: dict):
    orders = odata["orders"]
    prices = [o["price"] for o in orders]

    # item card
    st.markdown(item_card_html(
        name_zh=info.get("name_zh") or "—",
        name_en=info.get("name") or "",
        sell_min=info.get("sell_min_price"),
        buy_max=info.get("buy_max_price"),
        sell_num=info.get("sell_num"),
    ), unsafe_allow_html=True)

    # metrics
    panel_header("价格指标", f"本页 {len(orders)} 条 · 共 {odata['total']:,} 挂单")
    c1, c2, c3, c4, c5 = st.columns(5)
    lowest = odata.get("lowest_price")
    median = odata.get("median_price")
    buy_max = info.get("buy_max_price")
    spread = round(lowest - buy_max, 2) if lowest and buy_max else None
    p_arr = np.array(prices) if prices else np.array([0.0])

    with c1: st.metric("本页最低卖价",  f"¥{lowest:.2f}"  if lowest  else "—")
    with c2: st.metric("本页中位价",    f"¥{median:.2f}"  if median  else "—")
    with c3: st.metric("最高求购价",    f"¥{buy_max:.2f}" if buy_max else "—")
    with c4: st.metric("买卖价差",      f"¥{spread:.2f}"  if spread  else "—")
    with c5: st.metric("标准差",        f"¥{np.std(p_arr):.2f}" if len(prices) > 1 else "—")

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # charts
    col_hist, col_info = st.columns([3, 2])
    with col_hist:
        panel_header("价格分布", "Price Distribution")
        price_histogram_html(orders)

    with col_info:
        panel_header("磨损分布", "Wear Breakdown")
        wear_vals = [o["paintwear"] for o in orders if o["paintwear"] is not None]
        if wear_vals:
            counts = {}
            for w in wear_vals:
                _, zh, _ = wear_info(w)
                counts[zh] = counts.get(zh, 0) + 1
            for label, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                pct = cnt / len(wear_vals) * 100
                _, _, color = next(
                    (v for k, v in WEAR_LABEL.items() if v[1] == label), ("", "", "#7ea0b7")
                )
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.35rem 0;border-bottom:1px solid #1a2d42">
                    <span style="color:#c6d4df;font-size:0.82rem">{label}</span>
                    <span style="color:{color};font-family:'Rajdhani',sans-serif;
                                 font-weight:700;font-size:0.9rem">{cnt}&nbsp;
                        <span style="color:#4a6580;font-size:0.7rem">({pct:.0f}%)</span>
                    </span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#4a6580;font-size:0.82rem;padding:0.5rem 0">无磨损数据</div>',
                        unsafe_allow_html=True)


def tab_orders(odata: dict):
    orders = odata["orders"]
    if not orders:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;color:#2a3d52">
            <div style="font-size:2rem;margin-bottom:0.5rem">📭</div>
            <div>该页暂无卖单</div>
        </div>""", unsafe_allow_html=True)
        return

    prices = [o["price"] for o in orders]
    panel_header("筛选器", "Order Filters")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        mn, mx = float(min(prices)), float(max(prices))
        price_range = st.slider("价格区间", mn, mx, (mn, mx), step=0.01,
                                format="¥%.2f", label_visibility="collapsed") if mn < mx else (mn, mx)
    with c2:
        only_stickers = st.checkbox("含贴纸")
    with c3:
        only_tradable = st.checkbox("仅可交易")

    filtered = [
        o for o in orders
        if price_range[0] <= o["price"] <= price_range[1]
        and (not only_stickers or o["stickers"])
        and (not only_tradable or not o.get("tradable_cooldown_text") or o["tradable_cooldown_text"] == "可交易")
    ]

    st.markdown(f'<div style="color:#4a6580;font-size:0.72rem;margin-bottom:0.5rem">'
                f'显示 {len(filtered)} / {len(orders)} 条</div>', unsafe_allow_html=True)

    # table header
    st.markdown("""
    <div style="
        display:grid;grid-template-columns:2.5rem 6rem 7rem 5rem 1fr 4rem;
        gap:0;padding:0.4rem 0.9rem;
        background:#0d1520;border:1px solid #1a2d42;
        border-radius:4px 4px 0 0;
        font-family:'Rajdhani',sans-serif;font-size:0.68rem;
        font-weight:700;letter-spacing:0.1em;
        text-transform:uppercase;color:#4a6580">
        <div>#</div><div>价格</div><div>磨损</div>
        <div>图案</div><div>贴纸</div><div style="text-align:right">状态</div>
    </div>""", unsafe_allow_html=True)

    # table rows
    rows_html = "".join(
        order_row_html(i, o["price"], o["paintwear"], o["paintseed"],
                       o["stickers"], o.get("tradable_cooldown_text"))
        for i, o in enumerate(filtered)
    )
    st.markdown(
        f'<div style="border:1px solid #1a2d42;border-top:none;border-radius:0 0 4px 4px;'
        f'max-height:480px;overflow-y:auto">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def tab_analysis(info: dict, odata: dict):
    orders = odata["orders"]
    prices = np.array([o["price"] for o in orders]) if orders else np.array([0.0])
    buy_max = info.get("buy_max_price") or 0
    sell_min = info.get("sell_min_price") or (float(prices.min()) if len(prices) else 0)

    col_l, col_r = st.columns([1, 2])

    with col_l:
        panel_header("价格统计", "Price Percentiles")
        for pct, label in [(10, "P10  低价区"), (25, "P25"), (50, "P50  中位"),
                           (75, "P75"), (90, "P90  高价区")]:
            val = np.percentile(prices, pct)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.38rem 0;border-bottom:1px solid #1a2d42">
                <span style="color:#4a6580;font-family:'Rajdhani',sans-serif;
                             font-size:0.72rem;font-weight:700;letter-spacing:0.06em;
                             text-transform:uppercase">{label}</span>
                <span style="color:#cf6a32;font-family:'Rajdhani',sans-serif;
                             font-weight:700;font-size:1rem">¥{val:.2f}</span>
            </div>""", unsafe_allow_html=True)

    with col_r:
        panel_header("市场洞察", "Market Signals")

        spread = sell_min - buy_max
        spread_pct = (spread / buy_max * 100) if buy_max else 0
        cv = float(prices.std() / prices.mean()) if prices.mean() else 0
        sticker_orders = [o for o in orders if o["stickers"]]
        wear_orders    = [o for o in orders if o["paintwear"] is not None]

        signals = []
        if spread_pct < 5:
            signals.append(("🟢", "流动性优秀", f"买卖价差仅 {spread_pct:.1f}%，套利空间极小", "#5ba642"))
        elif spread_pct < 12:
            signals.append(("🟡", "流动性正常", f"买卖价差 {spread_pct:.1f}%，市场活跃", "#c6b441"))
        else:
            signals.append(("🔴", "流动性偏低", f"买卖价差 {spread_pct:.1f}%，持仓成本较高", "#c23b22"))

        if cv < 0.03:
            signals.append(("📊", "价格高度集中", f"变异系数 {cv:.3f}，卖家定价一致", "#4db6d4"))
        elif cv < 0.08:
            signals.append(("📊", "价格分布适中", f"变异系数 {cv:.3f}，存在一定议价空间", "#a87fef"))
        else:
            signals.append(("📊", "价格分布宽泛", f"变异系数 {cv:.3f}，注意特殊品溢价（贴纸/磨损）", "#cf6a32"))

        if sticker_orders:
            pct = len(sticker_orders) / len(orders) * 100
            signals.append(("🏷️", "贴纸溢价存在", f"{pct:.0f}% 卖单含贴纸，注意辨别溢价", "#d32ce6"))

        if wear_orders:
            avg_wear = np.mean([o["paintwear"] for o in wear_orders])
            short, zh, color = wear_info(avg_wear)
            signals.append(("🔍", f"平均磨损：{zh}", f"均值 {avg_wear:.4f} ({short})", color))

        for icon, title, desc, color in signals:
            st.markdown(f"""
            <div style="
                background:#0d1520;border:1px solid #1a2d42;
                border-left:3px solid {color};border-radius:3px;
                padding:0.7rem 1rem;margin-bottom:0.5rem">
                <div style="font-family:'Rajdhani',sans-serif;font-weight:700;
                            font-size:0.85rem;color:#c6d4df;margin-bottom:2px">
                    {icon}&nbsp; {title}</div>
                <div style="font-size:0.78rem;color:#4a6580">{desc}</div>
            </div>""", unsafe_allow_html=True)

        # sticker freq
        if sticker_orders:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            panel_header("贴纸频次", "Top Stickers")
            from collections import Counter
            top = Counter(s for o in sticker_orders for s in o["stickers"]).most_common(6)
            max_cnt = top[0][1] if top else 1
            for name, cnt in top:
                bar_w = int(cnt / max_cnt * 100)
                st.markdown(f"""
                <div style="margin-bottom:0.4rem">
                    <div style="display:flex;justify-content:space-between;
                                font-size:0.75rem;color:#7ea0b7;margin-bottom:2px">
                        <span>{name}</span><span style="color:#a87fef">{cnt}</span>
                    </div>
                    <div style="background:#1a2d42;border-radius:2px;height:4px">
                        <div style="background:#8847ff;width:{bar_w}%;height:4px;border-radius:2px"></div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init()
    render_sidebar()

    # ── top bar ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        display:flex;align-items:center;justify-content:space-between;
        padding:0.9rem 0 0.75rem;border-bottom:1px solid #1a2d42;
        margin-bottom:1.25rem">
        <div style="display:flex;align-items:center;gap:0.75rem">
            <span style="
                font-family:'Rajdhani',sans-serif;font-size:0.72rem;
                font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                color:#4a6580">SKINSENSE</span>
            <span style="color:#1a2d42">|</span>
            <span style="
                font-family:'Rajdhani',sans-serif;font-size:0.72rem;
                letter-spacing:0.1em;text-transform:uppercase;
                color:#cf6a32">BUFF · SELL ORDER ANALYSIS</span>
        </div>
        <div style="
            font-family:'Inter',sans-serif;font-size:0.65rem;
            letter-spacing:0.08em;color:#2a3d52">
            CS2 · COUNTER-STRIKE 2
        </div>
    </div>""", unsafe_allow_html=True)

    # ── no data state ─────────────────────────────────────────────────────
    if not st.session_state.goods_info:
        st.markdown("""
        <div style="
            text-align:center;padding:5rem 0;
            border:1px dashed #1a2d42;border-radius:4px;
            margin-top:1rem">
            <div style="font-size:2.5rem;margin-bottom:1rem">🎮</div>
            <div style="
                font-family:'Rajdhani',sans-serif;font-weight:700;
                font-size:1.1rem;letter-spacing:0.08em;text-transform:uppercase;
                color:#2a3d52;margin-bottom:0.5rem">NO ITEM SELECTED</div>
            <div style="color:#2a3d52;font-size:0.82rem">
                在左侧面板输入 Goods ID 并点击 FETCH DATA
            </div>
        </div>""", unsafe_allow_html=True)
        return

    info   = st.session_state.goods_info
    odata  = st.session_state.orders_data

    if not odata or not odata.get("orders"):
        st.info("该页无卖单数据，请翻页或调整排序")
        return

    # ── tabs ──────────────────────────────────────────────────────────────
    t1, t2, t3 = st.tabs(["📈  市场行情", "📋  卖单列表", "🔬  市场分析"])
    with t1: tab_market(info, odata)
    with t2: tab_orders(odata)
    with t3: tab_analysis(info, odata)


main()
