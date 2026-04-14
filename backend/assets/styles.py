"""
SkinSense AI — Visual Design System
Near-replica of BUFF163 / 悠悠有品 CS2 marketplace aesthetic.
"""

# ── BUFF-accurate color palette ───────────────────────────────────────────────
C = {
    # Page backgrounds  (matches BUFF's #12161f family)
    "page":         "#0f1319",
    "nav":          "#0d1017",
    "sidebar":      "#0b0e16",
    "card":         "#161c2c",
    "card_dark":    "#111624",
    "card_hover":   "#1c2438",
    "panel":        "#141a28",
    # Borders
    "border":       "rgba(255,255,255,0.06)",
    "border_hover": "rgba(74,142,245,0.35)",
    "divider":      "#1e2640",
    # Accent (BUFF blue)
    "accent":       "#4a8ef5",
    "accent_dim":   "rgba(74,142,245,0.15)",
    # Text
    "text":         "#e2e8f2",
    "text2":        "#7a8ba6",
    "text3":        "#3a4a60",
    # Price (BUFF amber)
    "price":        "#f5a623",
    "price_glow":   "rgba(245,166,35,0.15)",
    # Status
    "green":        "#3dd68c",
    "red":          "#ff5252",
    "yellow":       "#f5b731",
    # Wear tier
    "fn":  "#4a8ef5",
    "mw":  "#3dd68c",
    "ft":  "#f5b731",
    "ww":  "#f07040",
    "bs":  "#e04040",
    # Score tiers
    "shi": "#3dd68c",   # high  ≥75
    "smid":"#f5b731",   # mid   55-74
    "slo": "#ff5252",   # low   <55
    # Rarity (CS2 standard)
    "r_consumer":    "#b0c3d9",
    "r_industrial":  "#5e98d9",
    "r_milspec":     "#4b69ff",
    "r_restricted":  "#8847ff",
    "r_classified":  "#d32ce6",
    "r_covert":      "#eb4b4b",
    "r_contraband":  "#e4ae39",
}

FULL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stApp"],
[data-testid="stAppViewContainer"] {{
    background: {C['page']} !important;
    color: {C['text']};
    font-family: 'Inter', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
    font-size: 14px;
    line-height: 1.5;
}}

/* Kill all Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="manage-app-button"] {{
    display: none !important;
    visibility: hidden !important;
}}

/* Main content area */
[data-testid="stAppViewContainer"] > .main {{
    background: {C['page']} !important;
}}
[data-testid="stAppViewContainer"] > .main > .block-container {{
    max-width: 100% !important;
    padding: 0 20px 60px 20px !important;
    background: transparent !important;
    position: relative;
}}

/* scrollbar */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: {C['nav']}; }}
::-webkit-scrollbar-thumb {{ background: #2a3650; border-radius: 2px; }}

/* ═══════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: {C['sidebar']} !important;
    border-right: 1px solid {C['divider']} !important;
    min-width: 240px !important;
    max-width: 240px !important;
}}
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {{
    background: {C['sidebar']} !important;
    padding: 16px 14px !important;
}}
[data-testid="stSidebarCollapseButton"] svg {{
    fill: {C['text3']} !important;
}}

/* ═══════════════════════════════════════════════
   INPUTS & SELECTS
═══════════════════════════════════════════════ */
div[data-testid="stTextInput"] > div > div {{
    background: #0d1119 !important;
    border: 1px solid {C['divider']} !important;
    border-radius: 6px !important;
}}
div[data-testid="stTextInput"] input {{
    background: transparent !important;
    color: {C['text']} !important;
    font-size: 13px !important;
}}
div[data-testid="stTextInput"] input::placeholder {{
    color: {C['text3']} !important;
}}
div[data-testid="stTextInput"] > div > div:focus-within {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 0 2px rgba(74,142,245,0.2) !important;
}}
div[data-testid="stSelectbox"] > div {{
    background: #0d1119 !important;
    border: 1px solid {C['divider']} !important;
    border-radius: 6px !important;
    color: {C['text']} !important;
}}

/* ═══════════════════════════════════════════════
   BUTTONS — global
═══════════════════════════════════════════════ */
.stButton > button {{
    background: #1a2035 !important;
    border: 1px solid {C['divider']} !important;
    color: {C['text2']} !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.2px !important;
    transition: all 0.15s !important;
    height: 34px !important;
}}
.stButton > button:hover {{
    background: #1f2845 !important;
    border-color: {C['accent']} !important;
    color: {C['accent']} !important;
}}

/* Card "查看分析" footer button */
div.card-action .stButton > button {{
    border-radius: 0 0 6px 6px !important;
    border-top: 1px solid {C['divider']} !important;
    border-left: 1px solid rgba(255,255,255,0.06) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    background: rgba(20,26,40,0.95) !important;
    color: {C['text3']} !important;
    font-size: 11px !important;
    height: 32px !important;
    margin-top: -1px !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
}}
div.card-action .stButton > button:hover {{
    background: {C['accent_dim']} !important;
    border-color: rgba(74,142,245,0.3) !important;
    color: {C['accent']} !important;
}}

/* Search / send button */
div.primary-btn .stButton > button {{
    background: {C['accent']} !important;
    border-color: {C['accent']} !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-radius: 6px !important;
}}
div.primary-btn .stButton > button:hover {{
    background: #5a9ef8 !important;
    border-color: #5a9ef8 !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(74,142,245,0.4) !important;
}}

/* Back button */
div.ghost-btn .stButton > button {{
    background: transparent !important;
    border: 1px solid {C['divider']} !important;
    color: {C['text2']} !important;
}}
div.ghost-btn .stButton > button:hover {{
    border-color: {C['accent']} !important;
    color: {C['accent']} !important;
    background: {C['accent_dim']} !important;
}}

/* ═══════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════ */
div[data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid {C['divider']} !important;
    gap: 0 !important;
}}
div[data-baseweb="tab"] {{
    background: transparent !important;
    color: {C['text3']} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    border-bottom: 2px solid transparent !important;
}}
div[data-baseweb="tab"]:hover {{ color: {C['text2']} !important; }}
div[aria-selected="true"][data-baseweb="tab"] {{
    color: {C['accent']} !important;
    border-bottom-color: {C['accent']} !important;
}}
div[data-testid="stTabPanel"] {{ padding: 14px 0 0 !important; }}

/* ═══════════════════════════════════════════════
   COLUMN SPACING
═══════════════════════════════════════════════ */
div[data-testid="stHorizontalBlock"] {{
    gap: 10px !important;
    align-items: stretch !important;
}}
div[data-testid="column"] {{
    padding: 0 !important;
    min-width: 0 !important;
}}
/* Remove default spacing between markdown and next element */
div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] {{
    margin-bottom: 0 !important;
}}

/* ═══════════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════════ */
hr {{
    border: none !important;
    border-top: 1px solid {C['divider']} !important;
    margin: 10px 0 !important;
}}

/* ═══════════════════════════════════════════════
   ── BUFF CARD  (the core UI element) ──
═══════════════════════════════════════════════ */
.buff-card {{
    position: relative;
    background: linear-gradient(160deg, {C['card']} 0%, {C['card_dark']} 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px 6px 0 0;
    overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
    cursor: pointer;
    user-select: none;
}}
.buff-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(74,142,245,0.3);
    border-color: rgba(74,142,245,0.2);
}}

/* Rarity top edge */
.buff-card .rarity-edge {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    z-index: 3;
}}
.buff-card .rarity-edge.covert     {{ background: linear-gradient(90deg, transparent, #eb4b4b, transparent); }}
.buff-card .rarity-edge.classified {{ background: linear-gradient(90deg, transparent, #d32ce6, transparent); }}
.buff-card .rarity-edge.restricted {{ background: linear-gradient(90deg, transparent, #8847ff, transparent); }}
.buff-card .rarity-edge.milspec    {{ background: linear-gradient(90deg, transparent, #4b69ff, transparent); }}
.buff-card .rarity-edge.industrial {{ background: linear-gradient(90deg, transparent, #5e98d9, transparent); }}
.buff-card .rarity-edge.default    {{ background: linear-gradient(90deg, transparent, {C['accent']}, transparent); }}

/* Image area */
.buff-card .card-img-zone {{
    position: relative;
    padding: 22px 14px 14px;
    min-height: 148px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(ellipse 90% 75% at 50% 60%,
        rgba(22,35,65,0.9) 0%,
        rgba(10,13,22,0.3) 100%);
}}
.buff-card .card-img-zone img {{
    max-width: 100%;
    max-height: 110px;
    object-fit: contain;
    filter: drop-shadow(0 6px 18px rgba(0,0,0,0.85));
    transition: transform 0.2s;
    display: block;
    position: relative;
    z-index: 1;
}}
.buff-card:hover .card-img-zone img {{
    transform: scale(1.04) translateY(-3px);
}}
.buff-card .card-no-img {{
    font-size: 52px;
    opacity: 0.25;
    line-height: 1;
}}

/* Wear badge (top-right) */
.buff-card .wear-tag {{
    position: absolute;
    top: 8px; right: 8px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid currentColor;
    background: rgba(10,13,22,0.75);
    backdrop-filter: blur(4px);
    z-index: 4;
    line-height: 1.4;
}}
.buff-card .wear-tag.fn {{ color: {C['fn']}; }}
.buff-card .wear-tag.mw {{ color: {C['mw']}; }}
.buff-card .wear-tag.ft {{ color: {C['ft']}; }}
.buff-card .wear-tag.ww {{ color: {C['ww']}; }}
.buff-card .wear-tag.bs {{ color: {C['bs']}; }}

/* Score badge (top-left) */
.buff-card .score-tag {{
    position: absolute;
    top: 8px; left: 8px;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid currentColor;
    background: rgba(10,13,22,0.75);
    backdrop-filter: blur(4px);
    z-index: 4;
    line-height: 1.4;
}}
.buff-card .score-tag.hi  {{ color: {C['shi']}; }}
.buff-card .score-tag.mid {{ color: {C['smid']}; }}
.buff-card .score-tag.lo  {{ color: {C['slo']}; }}

/* Info section */
.buff-card .card-body {{
    padding: 9px 12px 11px;
    border-top: 1px solid rgba(255,255,255,0.05);
    background: rgba(12,15,25,0.5);
}}
.buff-card .card-weapon {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin-bottom: 2px;
    line-height: 1.2;
}}
.buff-card .card-name {{
    font-size: 12px;
    font-weight: 600;
    color: {C['text']};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
    margin-bottom: 6px;
}}
.buff-card .card-price-row {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
}}
.buff-card .card-price {{
    font-size: 18px;
    font-weight: 800;
    color: {C['price']};
    letter-spacing: -0.5px;
    line-height: 1;
}}
.buff-card .card-score-inline {{
    font-size: 10px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    line-height: 1.4;
}}
.buff-card .card-vol {{
    font-size: 10px;
    color: {C['text3']};
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}}
.buff-card .card-vol::before {{
    content: '';
    display: inline-block;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: {C['price']};
    opacity: 0.7;
}}

/* ═══════════════════════════════════════════════
   PAGE SECTIONS
═══════════════════════════════════════════════ */
.buff-topbar {{
    display: flex;
    align-items: center;
    padding: 0 20px;
    height: 52px;
    background: {C['nav']};
    border-bottom: 1px solid {C['divider']};
    margin: 0 -20px 18px -20px;
    position: sticky;
    top: 0;
    z-index: 999;
}}
.buff-logo {{
    font-size: 17px;
    font-weight: 900;
    letter-spacing: -0.5px;
    color: {C['text']};
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.buff-logo em {{
    font-style: normal;
    color: {C['accent']};
}}
.buff-logo-pill {{
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 1px;
    color: {C['text3']};
    border: 1px solid {C['divider']};
    border-radius: 3px;
    padding: 1px 5px;
    text-transform: uppercase;
}}
.buff-topbar-right {{
    margin-left: auto;
    font-size: 11px;
    color: {C['text3']};
}}

/* sidebar logo area */
.sb-logo {{
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid {C['divider']};
}}
.sb-logo-text {{
    font-size: 16px;
    font-weight: 900;
    color: {C['text']};
    letter-spacing: -0.3px;
}}
.sb-logo-text em {{
    font-style: normal;
    color: {C['accent']};
}}
.sb-logo-sub {{
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin-top: 3px;
}}

/* filter section label */
.filter-label {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin: 12px 0 6px;
}}
/* wear chips */
.chip-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}}
.wear-chip {{
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 3px;
    border: 1px solid currentColor;
    opacity: 0.75;
    cursor: default;
}}
.wear-chip.fn {{ color: {C['fn']}; background: rgba(74,142,245,0.08); }}
.wear-chip.mw {{ color: {C['mw']}; background: rgba(61,214,140,0.08); }}
.wear-chip.ft {{ color: {C['ft']}; background: rgba(245,183,49,0.08); }}
.wear-chip.ww {{ color: {C['ww']}; background: rgba(240,112,64,0.08); }}
.wear-chip.bs {{ color: {C['bs']}; background: rgba(224,64,64,0.08); }}

/* search result item */
.sb-result {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 8px;
    border-radius: 5px;
    background: rgba(20,26,40,0.8);
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 5px;
}}
.sb-result img {{
    width: 44px;
    height: 32px;
    object-fit: contain;
    flex-shrink: 0;
}}
.sb-result-name {{
    font-size: 11px;
    font-weight: 500;
    color: {C['text']};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
}}
.sb-result-price {{
    font-size: 13px;
    font-weight: 700;
    color: {C['price']};
}}

/* section heading */
.section-hd {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-hd::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, {C['divider']}, transparent);
}}

/* ═══════════════════════════════════════════════
   DETAIL — HERO
═══════════════════════════════════════════════ */
.detail-hero {{
    display: flex;
    background: linear-gradient(135deg, #161c2c 0%, #0f1219 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 16px;
}}
.hero-img-panel {{
    width: 260px;
    min-width: 200px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(ellipse 100% 80% at 50% 58%,
        rgba(22,35,65,0.95) 0%, transparent 80%);
    padding: 28px 20px;
}}
.hero-img-panel img {{
    max-width: 230px;
    max-height: 165px;
    object-fit: contain;
    filter: drop-shadow(0 10px 30px rgba(0,0,0,0.9));
}}
.hero-sep {{
    width: 1px;
    background: linear-gradient(180deg, transparent 5%, {C['divider']} 30%, {C['divider']} 70%, transparent 95%);
    flex-shrink: 0;
}}
.hero-info {{
    flex: 1;
    padding: 22px 24px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
}}
.hero-weapon {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {C['text3']};
}}
.hero-name {{
    font-size: 22px;
    font-weight: 800;
    color: {C['text']};
    letter-spacing: -0.3px;
    line-height: 1.2;
}}
.hero-price-row {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin: 4px 0;
}}
.hero-price {{
    font-size: 34px;
    font-weight: 900;
    color: {C['price']};
    letter-spacing: -1.5px;
    line-height: 1;
}}
.hero-delta {{
    font-size: 12px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
}}
.hero-delta.pos {{ color: {C['green']}; background: rgba(61,214,140,0.1); }}
.hero-delta.neg {{ color: {C['red']};   background: rgba(255,82,82,0.1); }}
.hero-median {{
    font-size: 12px;
    color: {C['text3']};
}}
.hero-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
}}
.hero-badge {{
    font-size: 10px;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    color: {C['text2']};
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.hero-badge.fn {{ color: {C['fn']}; border-color: rgba(74,142,245,0.3); background: rgba(74,142,245,0.08); }}
.hero-badge.mw {{ color: {C['mw']}; border-color: rgba(61,214,140,0.3); background: rgba(61,214,140,0.08); }}
.hero-badge.ft {{ color: {C['ft']}; border-color: rgba(245,183,49,0.3);  background: rgba(245,183,49,0.08); }}
.hero-badge.ww {{ color: {C['ww']}; border-color: rgba(240,112,64,0.3);  background: rgba(240,112,64,0.08); }}
.hero-badge.bs {{ color: {C['bs']}; border-color: rgba(224,64,64,0.3);   background: rgba(224,64,64,0.08); }}
.hero-stat-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 10px;
}}
.hero-stat {{
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
}}
.hero-stat-lbl {{ font-size: 9px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: {C['text3']}; margin-bottom: 4px; }}
.hero-stat-val {{ font-size: 14px; font-weight: 700; line-height: 1; }}

/* ═══════════════════════════════════════════════
   SCORE PANEL
═══════════════════════════════════════════════ */
.score-panel {{
    background: {C['panel']};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 16px;
}}
.score-lbl {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin-bottom: 12px;
}}
.score-layout {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
}}
.score-bars {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 7px;
}}
.sbar-row {{
    display: grid;
    grid-template-columns: 48px 1fr 26px;
    align-items: center;
    gap: 7px;
    line-height: 1;
}}
.sbar-label {{ font-size: 10px; color: {C['text2']}; font-weight: 500; text-align: right; }}
.sbar-track {{
    height: 4px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
}}
.sbar-fill {{ height: 100%; border-radius: 2px; }}
.sbar-val {{ font-size: 10px; font-weight: 700; text-align: right; }}
.sbar-note {{
    font-size: 9.5px;
    color: {C['text3']};
    grid-column: 1/-1;
    padding-left: 55px;
    line-height: 1.4;
    margin-top: -3px;
}}

/* ═══════════════════════════════════════════════
   MARKET CHART
═══════════════════════════════════════════════ */
.hist-wrap {{
    background: {C['panel']};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}}
.hist-bars {{
    display: flex;
    align-items: flex-end;
    height: 72px;
    gap: 2px;
}}
.hist-bar {{
    flex: 1;
    border-radius: 2px 2px 0 0;
    min-height: 3px;
    opacity: 0.75;
    transition: opacity 0.15s;
    cursor: default;
}}
.hist-bar:hover {{ opacity: 1; filter: brightness(1.2); }}
.hist-axis {{
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    color: {C['text3']};
    margin-top: 5px;
}}
.stat-tiles {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 7px;
    margin-bottom: 12px;
}}
.stat-tile {{
    background: {C['panel']};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
}}
.stat-tile-lbl {{ font-size: 9px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: {C['text3']}; margin-bottom: 4px; }}
.stat-tile-val {{ font-size: 14px; font-weight: 700; line-height: 1; }}

/* ═══════════════════════════════════════════════
   LISTINGS TABLE
═══════════════════════════════════════════════ */
.listings-wrap {{
    background: {C['panel']};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    overflow: hidden;
}}
.listings-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.listings-table th {{
    padding: 8px 12px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: {C['text3']};
    border-bottom: 1px solid {C['divider']};
    background: rgba(0,0,0,0.25);
    text-align: left;
}}
.listings-table td {{ padding: 6px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }}
.listings-table tr:last-child td {{ border-bottom: none; }}
.listings-table tr.r-best   {{ background: rgba(61,214,140,0.06); }}
.listings-table tr.r-good   {{ background: rgba(74,142,245,0.05); }}
.listings-table tr.r-normal {{ background: transparent; }}
.listings-table tr.r-high   {{ background: rgba(245,183,49,0.05); }}
.listings-table tr.r-over   {{ background: rgba(255,82,82,0.05); }}
.rank-tag {{
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    display: inline-block;
}}

/* ═══════════════════════════════════════════════
   AI CHAT
═══════════════════════════════════════════════ */
.chat-panel {{
    background: {C['panel']};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 14px;
    margin-top: 12px;
}}
.chat-panel-title {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {C['text3']};
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.chat-panel-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, {C['divider']}, transparent);
}}
.chat-messages {{
    display: flex;
    flex-direction: column;
    gap: 7px;
    max-height: 340px;
    overflow-y: auto;
    margin-bottom: 10px;
    padding-right: 2px;
}}
.chat-msg {{
    font-size: 12px;
    line-height: 1.55;
    padding: 8px 11px;
    border-radius: 6px;
    max-width: 95%;
    word-break: break-word;
}}
.chat-msg.user {{
    background: rgba(74,142,245,0.12);
    border: 1px solid rgba(74,142,245,0.2);
    color: {C['text']};
    align-self: flex-end;
    margin-left: auto;
    border-radius: 6px 2px 6px 6px;
}}
.chat-msg.ai {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    color: {C['text']};
    border-radius: 2px 6px 6px 6px;
}}
.chat-msg.ai b, .chat-msg.ai strong {{ color: {C['accent']}; font-weight: 600; }}
.chat-welcome {{
    font-size: 11px;
    color: {C['text2']};
    line-height: 1.6;
    padding: 8px 11px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px;
    margin-bottom: 10px;
}}
.chat-welcome b {{ color: {C['accent']}; font-weight: 600; }}
</style>
"""
