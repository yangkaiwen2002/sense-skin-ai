"""SkinSense AI — CS2 Marketplace (BUFF-style)"""
import re, math
import streamlit as st

from data_sources import steam_client as sc
from scoring import compute as score_compute
from ai_agent import ask_agent_stream
from assets.styles import FULL_CSS, C

st.set_page_config(page_title="SkinSense AI", page_icon="🎯",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(FULL_CSS, unsafe_allow_html=True)

# ── i18n ──────────────────────────────────────────────────────────────────────
I18N = {
    "中文": {
        "q_ph":"搜索饰品 例如 AK-47 Redline","q_btn":"搜索",
        "fw":"武器类型","fe":"磨损","popular":"热门饰品",
        "no_res":"未找到结果","loading":"正在加载…","back":"← 返回市场",
        "lowest":"最低价","median":"均价","volume":"日成交","listed":"总挂单",
        "ask_ph":"问我任何关于这个饰品的问题…","send":"发送","analyze":"查看分析",
        "results":"搜索结果","tm":"  市场数据  ","tl":"  挂单列表  ",
        "sv":"价值","sl":"流动性","ss":"稳定性","st2":"趋势",
        "dist":"价格分布","lt":"当前挂单","cr":"#","cp":"价格","cv":"vs均价","ct":"评级",
        "tb":"优质","tg":"良好","tn":"正常","th":"偏贵","to":"高价",
        "ai_title":"AI 分析助手",
        "ai_intro":"你好！我是 <b>SkinSense AI</b>（Claude claude-opus-4-6 驱动）。<br>可以问我：值得买吗？同价位有更好选择？价格走势如何？",
        "no_data":"暂无数据",
    },
    "English": {
        "q_ph":"Search skins e.g. AK-47 Redline","q_btn":"Search",
        "fw":"Weapon","fe":"Wear","popular":"Popular Skins",
        "no_res":"No results found","loading":"Loading…","back":"← Back",
        "lowest":"Lowest","median":"Median","volume":"Vol/day","listed":"Listed",
        "ask_ph":"Ask me anything about this skin…","send":"Send","analyze":"Analyze",
        "results":"Results","tm":"  Market  ","tl":"  Listings  ",
        "sv":"Value","sl":"Liquidity","ss":"Stability","st2":"Trend",
        "dist":"Price Distribution","lt":"Current Listings","cr":"#","cp":"Price","cv":"vs Med","ct":"Tag",
        "tb":"Best","tg":"Good","tn":"Normal","th":"High","to":"Over",
        "ai_title":"AI Analysis",
        "ai_intro":"Hi! I'm <b>SkinSense AI</b> (Claude claude-opus-4-6).<br>Ask: Worth buying? Better alternatives? Price outlook?",
        "no_data":"No data",
    },
}
LANGS = list(I18N.keys())
def T(k): return I18N[st.session_state.get("lang", LANGS[0])][k]

# ── session state ──────────────────────────────────────────────────────────────
for k, v in {
    "view":"market","hash_name":"","overview":None,"listings":None,
    "scores":None,"icon_url":None,"search_results":[],"popular_items":[],
    "popular_loaded":False,"chat_history":[],"lang":LANGS[0],
    "query":"","data_cache":{},
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── helpers ────────────────────────────────────────────────────────────────────
def _md(html):
    st.markdown(re.sub(r"\n[ \t]*\n","\n",html).strip(), unsafe_allow_html=True)

def _cdn(icon_url, size=200):
    if not icon_url: return ""
    return f"https://steamcommunity-a.akamaihd.net/economy/image/{icon_url}/{size}fx{size}f"

def _wear(name):
    n = name.lower()
    if "factory new"    in n: return "FN","fn"
    if "minimal wear"   in n: return "MW","mw"
    if "field-tested"   in n: return "FT","ft"
    if "well-worn"      in n: return "WW","ww"
    if "battle-scarred" in n: return "BS","bs"
    return "","fn"

def _split(h):
    if "|" in h:
        w,s = h.split("|",1)
        return w.strip(), s.strip()
    return "", h

def _scls(s): return "hi" if s>=75 else ("mid" if s>=55 else "lo")
def _scol(s): return C["shi"] if s>=75 else (C["smid"] if s>=55 else C["slo"])

def _ring(score, color, label, size=118):
    h=size//2; r=int(h*0.76)
    circ=2*math.pi*r; off=circ*(1-score/100)
    uid=f"rg{score}"
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><filter id="{uid}"><feGaussianBlur stdDeviation="2.5" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        f'<circle cx="{h}" cy="{h}" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>'
        f'<circle cx="{h}" cy="{h}" r="{r}" fill="none" stroke="{color}" stroke-width="8"'
        f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 {h} {h})" filter="url(#{uid})"/>'
        f'<text x="{h}" y="{h-4}" text-anchor="middle" font-size="24" font-weight="900"'
        f' fill="{color}" font-family="Inter,sans-serif">{score}</text>'
        f'<text x="{h}" y="{h+10}" text-anchor="middle" font-size="8.5" fill="{C["text3"]}"'
        f' font-family="Inter,sans-serif">/ 100</text>'
        f'<text x="{h}" y="{h+23}" text-anchor="middle" font-size="8.5" font-weight="700"'
        f' fill="{color}" font-family="Inter,sans-serif">{label}</text>'
        f'</svg>'
    )

# ── data loading ───────────────────────────────────────────────────────────────
def _ensure_popular():
    if st.session_state.popular_loaded: return
    out = []
    for q in ["AK-47","AWP","Karambit"]:
        res = sc.search_items(q, count=4)
        if res.get("ok"):
            for it in res.get("items",[]):
                if it.get("icon_url"):
                    out.append({"hash_name":it["hash_name"],"icon_url":it["icon_url"],
                                "sell_price":it.get("sell_price"),"sell_listings":it.get("sell_listings")})
    st.session_state.popular_items  = out
    st.session_state.popular_loaded = True

def _load(hn):
    if hn in st.session_state.data_cache:
        d = st.session_state.data_cache[hn]
        for k in ("overview","listings","scores","icon_url"): st.session_state[k]=d[k]
        st.session_state.hash_name = hn; return
    with st.spinner(T("loading")):
        ov = sc.fetch_price_overview(hn)
        li = sc.fetch_listings(hn)
    icon = li.get("icon_url") if li.get("ok") else None
    lp = li.get("lowest_price") or (ov.get("lowest_price") if ov.get("ok") else None)
    mp = li.get("median_price")  or (ov.get("median_price") if ov.get("ok") else None)
    vol= ov.get("volume")  if ov.get("ok") else None
    tot= li.get("total")   if li.get("ok") else None
    px = [l["price"] for l in (li.get("listings") or [])]
    sc2= score_compute(lowest_price=lp,median_price=mp,volume=vol,total_listings=tot,listing_prices=px)
    d  = {"overview":ov,"listings":li,"scores":sc2,"icon_url":icon}
    for k,v in d.items(): st.session_state[k]=v
    st.session_state.hash_name=hn
    st.session_state.data_cache[hn]=d

def _goto(hn, icon=None):
    if icon and hn not in st.session_state.data_cache: st.session_state.icon_url=icon
    _load(hn)
    st.session_state.chat_history=[]
    st.session_state.view="detail"
    st.rerun()

# ── sidebar ────────────────────────────────────────────────────────────────────
def _sidebar():
    with st.sidebar:
        _md('<div class="sb-logo">'
            '<div class="sb-logo-text">Skin<em>Sense</em> AI</div>'
            '<div class="sb-logo-sub">CS2 MARKET INTELLIGENCE</div>'
            '</div>')

        idx = LANGS.index(st.session_state.lang)
        ch  = st.selectbox("lang", LANGS, index=idx, label_visibility="collapsed")
        if ch != st.session_state.lang:
            st.session_state.lang=ch; st.rerun()

        q = st.text_input("q", value=st.session_state.query,
                           placeholder=T("q_ph"), label_visibility="collapsed")
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button(T("q_btn"), use_container_width=True):
            if q.strip():
                st.session_state.query=q.strip()
                with st.spinner(T("loading")):
                    res=sc.search_items(q.strip(),count=20)
                st.session_state.search_results = res.get("items",[]) if res.get("ok") else []
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

        # Weapon chips
        _md(f'<div class="filter-label">{T("fw")}</div>')
        _md('<div class="chip-row">'
            +''.join(f'<span class="wear-chip fn">{w}</span>'
                     for w in ["全部","AK-47","AWP","M4A4","USP","刀"])
            +'</div>')
        _md(f'<div class="filter-label">{T("fe")}</div>')
        _md('<div class="chip-row">'
            '<span class="wear-chip fn">FN</span>'
            '<span class="wear-chip mw">MW</span>'
            '<span class="wear-chip ft">FT</span>'
            '<span class="wear-chip ww">WW</span>'
            '<span class="wear-chip bs">BS</span>'
            '</div>')

        # Search results
        results = st.session_state.search_results
        if results:
            st.divider()
            _md(f'<div class="filter-label">{T("results")} ({len(results)})</div>')
            for it in results:
                hn   = it.get("hash_name","")
                name = it.get("name",hn)
                px   = it.get("sell_price")
                icon = it.get("icon_url","")
                img  = _cdn(icon,64)
                ps   = f"¥{px:.2f}" if px else "—"
                _md(f'<div class="sb-result">'
                    +(f'<img src="{img}" alt="">' if img else "")
                    +f'<div><div class="sb-result-name">{name}</div>'
                    +f'<div class="sb-result-price">{ps}</div></div>'
                    +f'</div>')
                if st.button(T("analyze"), key=f"sb_{hn}", use_container_width=True):
                    _goto(hn, icon)
        elif st.session_state.query:
            st.caption(T("no_res"))

        if st.session_state.view == "detail":
            st.divider()
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button(T("back"), use_container_width=True):
                st.session_state.view="market"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ── card HTML ──────────────────────────────────────────────────────────────────
def _card(hn, icon_url, price, volume, score):
    weapon, skin = _split(hn)
    wear, wcls   = _wear(hn)
    img_url      = _cdn(icon_url, 200) if icon_url else ""
    price_str    = f"¥{price:.2f}" if price else "—"

    # rarity edge colour — infer from weapon name (rough heuristic)
    name_l = hn.lower()
    if any(x in name_l for x in ["karambit","butterfly","bayonet","★"]):
        edge_cls = "covert"
    elif "howl" in name_l or "fire serpent" in name_l:
        edge_cls = "contraband"
    elif any(x in name_l for x in ["fade","doppler","marble"]):
        edge_cls = "covert"
    elif "dragon lore" in name_l or "medusa" in name_l:
        edge_cls = "covert"
    else:
        edge_cls = "default"

    img_tag  = (f'<img src="{img_url}" alt="" onerror="this.parentElement.innerHTML=\'<div class=card-no-img>🔫</div>\'">'
                if img_url else '<div class="card-no-img">🔫</div>')
    wear_tag = f'<span class="wear-tag {wcls}">{wear}</span>' if wear else ""
    scr_tag  = (f'<span class="score-tag {_scls(score)}">{score}</span>'
                if score is not None else "")
    vol_tag  = f'<div class="card-vol">{volume}/天</div>' if volume else ""

    sc_inline = ""
    if score is not None:
        sc_inline = (f'<span class="card-score-inline" '
                     f'style="color:{_scol(score)};background:{_scol(score)}18">{score}分</span>')

    return (
        f'<div class="buff-card">'
        f'<div class="rarity-edge {edge_cls}"></div>'
        f'<div class="card-img-zone">{scr_tag}{wear_tag}{img_tag}</div>'
        f'<div class="card-body">'
        f'<div class="card-weapon">{weapon or "CS2"}</div>'
        f'<div class="card-name" title="{skin}">{skin}</div>'
        f'<div class="card-price-row">'
        f'<span class="card-price">{price_str}</span>'
        f'{sc_inline}'
        f'</div>'
        f'{vol_tag}'
        f'</div>'
        f'</div>'
    )

# ── market grid ────────────────────────────────────────────────────────────────
def _market():
    results = st.session_state.search_results
    if not results:
        if not st.session_state.popular_loaded:
            with st.spinner(T("loading")):
                _ensure_popular()
        items = st.session_state.popular_items
        label = T("popular")
    else:
        items = [{"hash_name":it["hash_name"],"icon_url":it.get("icon_url"),
                  "sell_price":it.get("sell_price"),"sell_listings":it.get("sell_listings")}
                 for it in results]
        label = f'{T("results")} ({len(items)})'

    _md(f'<div class="section-hd">{label}</div>')
    if not items:
        st.info("搜索饰品以开始浏览 / Search to get started"); return

    N = 4
    for row_items in [items[i:i+N] for i in range(0,len(items),N)]:
        cols = st.columns(N, gap="small")
        for col, item in zip(cols, row_items):
            hn    = item.get("hash_name","")
            icon  = item.get("icon_url")
            price = item.get("sell_price") or item.get("lowest_price")
            vol   = item.get("sell_listings") or item.get("volume")
            cached= st.session_state.data_cache.get(hn)
            s_val = cached["scores"].overall if cached and cached.get("scores") else None
            with col:
                _md(_card(hn, icon, price, vol, s_val))
                st.markdown('<div class="card-action">', unsafe_allow_html=True)
                if st.button(T("analyze"), key=f"c_{hn}", use_container_width=True):
                    _goto(hn, icon)
                st.markdown('</div>', unsafe_allow_html=True)

# ── detail hero ────────────────────────────────────────────────────────────────
def _hero():
    hn  = st.session_state.hash_name
    ico = st.session_state.icon_url
    ov  = st.session_state.overview or {}
    li  = st.session_state.listings or {}
    scd = st.session_state.scores

    weapon, skin = _split(hn)
    wear, wcls   = _wear(hn)
    img_url      = _cdn(ico, 360) if ico else ""

    lp  = li.get("lowest_price") or ov.get("lowest_price")
    mp  = li.get("median_price")  or ov.get("median_price")
    vol = ov.get("volume")
    tot = li.get("total")

    lp_s = f"¥{lp:.2f}" if lp else "—"
    mp_s = f"¥{mp:.2f}" if mp else "—"
    vs   = f"{vol:,}" if vol else "—"
    ts   = f"{tot:,}" if tot else "—"

    delta_html = ""
    if lp and mp and mp > 0:
        d   = (lp-mp)/mp*100
        cls = "pos" if d<=0 else "neg"
        arr = "▼" if d<=0 else "▲"
        delta_html = f'<span class="hero-delta {cls}">{arr} {abs(d):.1f}%</span>'

    score_badge = ""
    if scd:
        col2 = _scol(scd.overall)
        score_badge = (f'<span class="hero-badge" style="color:{col2};border-color:{col2}44;background:{col2}10">'
                       f'综合 {scd.overall} · {scd.overall_label}</span>')

    img_tag = (f'<img src="{img_url}" alt="{skin}">' if img_url
               else '<div style="font-size:72px;opacity:.25">🔫</div>')
    wear_badge = f'<span class="hero-badge {wcls}">{wear}</span>' if wear else ""

    _md(
        f'<div class="detail-hero">'
        f'<div class="hero-img-panel">{img_tag}</div>'
        f'<div class="hero-sep"></div>'
        f'<div class="hero-info">'
        f'<div class="hero-weapon">{weapon or "CS2 SKIN"}</div>'
        f'<div class="hero-name">{skin}</div>'
        f'<div class="hero-price-row"><span class="hero-price">{lp_s}</span>{delta_html}</div>'
        f'<div class="hero-median">市场均价 {mp_s}</div>'
        f'<div class="hero-badges">{wear_badge}{score_badge}'
        f'<span class="hero-badge">成交 {vs}/天</span>'
        f'<span class="hero-badge">挂单 {ts}</span>'
        f'</div>'
        f'<div class="hero-stat-row">'
        f'<div class="hero-stat"><div class="hero-stat-lbl">最低价</div>'
        f'<div class="hero-stat-val" style="color:{C["price"]}">{lp_s}</div></div>'
        f'<div class="hero-stat"><div class="hero-stat-lbl">均价</div>'
        f'<div class="hero-stat-val" style="color:{C["accent"]}">{mp_s}</div></div>'
        f'<div class="hero-stat"><div class="hero-stat-lbl">日成交</div>'
        f'<div class="hero-stat-val" style="color:{C["text"]}">{vs}</div></div>'
        f'<div class="hero-stat"><div class="hero-stat-lbl">总挂单</div>'
        f'<div class="hero-stat-val" style="color:{C["text"]}">{ts}</div></div>'
        f'</div>'
        f'</div></div>'
    )

# ── score panel ────────────────────────────────────────────────────────────────
def _score_panel():
    scd = st.session_state.scores
    if not scd: return
    col  = _scol(scd.overall)
    ring = _ring(scd.overall, col, scd.overall_label)

    def bar(lbl, val, note):
        c = _scol(val)
        return (
            f'<div class="sbar-row">'
            f'<span class="sbar-label">{lbl}</span>'
            f'<div class="sbar-track"><div class="sbar-fill" style="width:{val}%;background:{c}"></div></div>'
            f'<span class="sbar-val" style="color:{c}">{val}</span>'
            f'</div>'
            f'<div class="sbar-note">{note}</div>'
        )

    _md(
        '<div class="score-panel">'
        '<div class="score-lbl">综合评分</div>'
        '<div class="score-layout">'
        f'<div>{ring}</div>'
        '<div class="score-bars">'
        + bar(T("sv"), scd.value,     scd.value_note)
        + bar(T("sl"), scd.liquidity, scd.liquidity_note)
        + bar(T("ss"), scd.stability, scd.stability_note)
        + bar(T("st2"),scd.trend,     scd.trend_note)
        + '</div></div></div>'
    )

# ── market tab ─────────────────────────────────────────────────────────────────
def _market_tab():
    import numpy as np
    li = st.session_state.listings or {}
    ov = st.session_state.overview or {}
    prices = [l["price"] for l in li.get("listings",[])]
    mp = li.get("median_price") or ov.get("median_price")
    if not prices: st.info(T("no_data")); return

    mn,mx  = min(prices),max(prices)
    avg    = sum(prices)/len(prices)
    std    = float(np.std(prices))
    mp_v   = mp if mp else avg

    # Stat tiles
    _md(
        '<div class="stat-tiles">'
        + "".join(
            f'<div class="stat-tile">'
            f'<div class="stat-tile-lbl">{lbl}</div>'
            f'<div class="stat-tile-val" style="color:{col}">{val}</div>'
            f'</div>'
            for lbl,val,col in [
                ("最低价",f"¥{mn:.2f}",C["price"]),
                ("均价",  f"¥{mp_v:.2f}",C["accent"]),
                ("均值",  f"¥{avg:.2f}",C["text"]),
                ("标准差",f"¥{std:.2f}",C["text2"]),
            ]
        )
        + '</div>'
    )

    # Histogram
    nb  = min(20,len(prices))
    bw  = (mx-mn)/nb if mx>mn else 1
    bins= [0]*nb
    for p in prices: bins[min(int((p-mn)/bw),nb-1)]+=1
    mb  = max(bins) or 1
    bars= ""
    for i,cnt in enumerate(bins):
        t   = i/max(nb-1,1)
        col = C["green"] if t<0.33 else (C["yellow"] if t<0.66 else C["red"])
        h   = max(3,int(cnt/mb*68))
        lo  = mn+i*bw
        bars+= f'<div class="hist-bar" style="height:{h}px;background:{col}" title="¥{lo:.1f}–{lo+bw:.1f} ({cnt}件)"></div>'

    _md(
        f'<div class="hist-wrap">'
        f'<div class="section-hd" style="margin-bottom:10px">{T("dist")}</div>'
        f'<div class="hist-bars">{bars}</div>'
        f'<div class="hist-axis"><span>¥{mn:.1f}</span><span>¥{mx:.1f}</span></div>'
        f'</div>'
    )

# ── listings tab ───────────────────────────────────────────────────────────────
def _listings_tab():
    li = st.session_state.listings or {}
    ov = st.session_state.overview or {}
    items = li.get("listings",[])
    mp = li.get("median_price") or ov.get("median_price") or 0
    if not items: st.info(T("no_data")); return

    _md(f'<div class="section-hd">{T("lt")} ({len(items)})</div>')
    rows=""
    for i,item in enumerate(items[:60]):
        p = item["price"]
        d = (p-mp)/mp*100 if mp else 0
        if   d<=-5: rc,dc,tag="r-best", C["green"], T("tb")
        elif d<=0:  rc,dc,tag="r-good", C["accent"],T("tg")
        elif d<=5:  rc,dc,tag="r-normal",C["text2"], T("tn")
        elif d<=15: rc,dc,tag="r-high", C["yellow"],T("th")
        else:       rc,dc,tag="r-over", C["red"],   T("to")
        rows+=(f'<tr class="{rc}">'
               f'<td style="color:{C["text3"]};font-size:11px">{i+1}</td>'
               f'<td style="color:{C["price"]};font-weight:700">¥{p:.2f}</td>'
               f'<td style="color:{dc};font-size:11px">{d:+.1f}%</td>'
               f'<td><span class="rank-tag" style="color:{dc};background:{dc}18">{tag}</span></td>'
               f'</tr>')

    _md(
        '<div class="listings-wrap">'
        '<table class="listings-table">'
        f'<thead><tr><th>{T("cr")}</th><th>{T("cp")}</th><th>{T("cv")}</th><th>{T("ct")}</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )

# ── ai chat ────────────────────────────────────────────────────────────────────
def _chat():
    hn  = st.session_state.hash_name
    scd = st.session_state.scores
    if not scd: return

    history = st.session_state.chat_history
    msgs_html = ""
    if not history:
        msgs_html = f'<div class="chat-welcome">{T("ai_intro")}</div>'
    else:
        for m in history:
            cls = "user" if m["role"]=="user" else "ai"
            txt = m["content"].replace("\n","<br>")
            msgs_html += f'<div class="chat-msg {cls}">{txt}</div>'

    _md(
        '<div class="chat-panel">'
        f'<div class="chat-panel-title">{T("ai_title")}</div>'
        f'<div class="chat-messages">{msgs_html}</div>'
        '</div>'
    )

    # Input row
    c1, c2 = st.columns([6,1])
    with c1:
        question = st.text_input("ask", placeholder=T("ask_ph"),
                                 label_visibility="collapsed", key="chat_input")
    with c2:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        send = st.button(T("send"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if send and question.strip():
        q = question.strip()
        # Stream response into a styled bubble (fixes the "full screen" bug)
        box = st.empty()
        full = ""
        try:
            for chunk in ask_agent_stream(
                    question=q, hash_name=hn, sc=scd,
                    listings=st.session_state.listings or {},
                    overview=st.session_state.overview or {},
                    history=history):
                full += chunk
                box.markdown(
                    f'<div class="chat-msg ai">{full}▌</div>',
                    unsafe_allow_html=True)
            box.markdown(
                f'<div class="chat-msg ai">{full}</div>',
                unsafe_allow_html=True)
        except Exception as e:
            full = f"⚠️ 暂时不可用：{e}"
            box.error(full)

        st.session_state.chat_history.append({"role":"user",      "content":q})
        st.session_state.chat_history.append({"role":"assistant", "content":full})
        st.rerun()

# ── detail view ────────────────────────────────────────────────────────────────
def _detail():
    if not st.session_state.hash_name:
        st.info(T("no_data")); return

    _hero()

    left, right = st.columns([5,7], gap="large")
    with left:
        _score_panel()
        _chat()
    with right:
        t1, t2 = st.tabs([T("tm"), T("tl")])
        with t1: _market_tab()
        with t2: _listings_tab()

# ── entry ──────────────────────────────────────────────────────────────────────
_sidebar()

_md(
    f'<div class="buff-topbar">'
    f'<div class="buff-logo">Skin<em>Sense</em> AI'
    f'<span class="buff-logo-pill">CS2</span></div>'
    f'<div class="buff-topbar-right">数据源：Steam Community Market</div>'
    f'</div>'
)

if st.session_state.view == "market":
    _market()
else:
    _detail()
