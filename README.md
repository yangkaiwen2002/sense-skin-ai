# SenseSkin AI

**CS2 皮肤市场智能决策系统**

A market intelligence and decision-support system for CS2 skin trading. The core value is not chat — it's **identifying opportunities, explaining risks, and supporting buy/hold/avoid decisions** using a structured AI pipeline grounded in real market signals.

---

## What This Is

SenseSkin is built around one principle: **AI as a system component, not the whole product.**

The system continuously scores every item across 7 independent dimensions, maps active market events to per-item relevance, runs a transparent decision engine, and surfaces the results as actionable intelligence — not just chat responses.

```
Market Events  ──────────────────────┐
Price History  → 7-Dim Scoring   → Decision Engine → BUY / WATCH / HOLD / AVOID
Item Attributes → Event Mapper   → Evidence Chain  → Explainable Rationale
Knowledge Base → TF-IDF Retrieval → RAG Layer      → Grounded AI Answers
```

---

## Core Features

### 1. Opportunity Scanner
Scans every item with full event context and surfaces investment opportunities ranked by the decision engine. Each card shows:
- Decision signal: **BUY / WATCH / HOLD / AVOID**
- Confidence score (0–100%)
- Driving rationale from the evidence chain
- Active market event (if one is influencing the score)

### 2. 7-Dimensional Scoring Engine
Every item is scored across 7 independently computed dimensions:

| Dimension | Weight | Signal |
|-----------|--------|--------|
| Rarity | 18% | Scarcity and collector demand |
| Exterior | 12% | Float / condition quality |
| Liquidity | 18% | Market depth and tradability |
| Trend | 14% | 7-day price momentum |
| Valuation | 14% | Current price vs 30-day average |
| Demand | 12% | Weapon category × rarity × StatTrak |
| Event Signal | 12% | Active market event impact |

Scores are transparent — every subscores is shown in the UI and traced to its input data.

### 3. Decision Engine
An evidence-accumulation engine that turns scoring signals into a single recommendation with a full audit trail.

**Evidence sources (max contribution):**
- Valuation (low vs 30d avg): ±2.0 pts
- 7-day trend momentum: ±1.5 pts
- Active event impact: ±2.0 pts
- Liquidity: ±1.0 pt
- Overall score tier: ±2.0 pts
- Risk label penalties: −0.5 each

**Decision thresholds:**
```
net ≥ +3.0  AND  total ≥ 62  →  BUY
net ≥ +1.0  AND  total ≥ 52  →  WATCH
net ≥ -1.0  AND  total ≥ 42  →  HOLD
else                          →  AVOID
```

Every recommendation is reproducible by inspecting the `supporting_signals` array.

### 4. Event-Driven Signal Pipeline
Market events (tournaments, patches, seasonal events) are modeled as structured signals and mapped to each item with a relevance score:

```
relevance = category_match × recency_weight × impact_strength × confidence
```

**Category matching:** specific item name (1.0) > weapon type (0.92) > high-tier rarity (0.82) > "all" (0.80) > StatTrak (0.78)

**Recency windows (tournament example):**
- 7–14 days before: 1.00 (prime pre-event window)
- 0–7 days before: 0.90 (imminent speculation)
- 0–7 days after: 0.95 (post-event peak)

The `event_signal` dimension feeds directly into the weighted score, and the decision engine receives the raw `event_impact_score` (−1.0 to +1.0) for its evidence accumulation.

### 5. RAG-Based Market Knowledge
A TF-IDF retrieval layer over a curated knowledge base covering:
- Rarity tiers and pricing dynamics
- Exterior grades and float value impact
- Tournament effects on skin demand
- Platform differences (BUFF vs Steam vs 悠悠有品)
- Rent vs buy decision framework
- StatTrak premium logic

When Claude answers a question in item chat, its system prompt is grounded with the full decision output, event context, and scoring breakdown — not just raw price data.

---

## Architecture

```
backend/
├── app/
│   ├── routers/
│   │   ├── scoring.py          # /score, /decision, /opportunities, /market/events
│   │   ├── chat.py             # Streaming AI chat (grounded in decision context)
│   │   └── rag.py              # RAG query endpoint
│   ├── services/
│   │   ├── scoring.py          # 7-dimensional scoring engine
│   │   ├── decision_engine.py  # BUY/WATCH/HOLD/AVOID with evidence trail
│   │   ├── event_ingestion.py  # Load events.json with 5-min TTL cache
│   │   ├── event_mapper.py     # Per-item relevance scoring
│   │   └── opportunity_detector.py  # Full-pipeline opportunity scan
│   ├── rag/
│   │   └── retriever.py        # TF-IDF retriever (scikit-learn, no API needed)
│   └── utils/
│       └── metrics.py          # compute_avg, compute_return, compute_volatility, compute_liquidity_score
├── data/
│   ├── events.json             # 22 structured market signals (tournaments, patches, seasonal)
│   └── knowledge.json          # RAG knowledge base (20+ articles)
└── seed/
    └── seed_data.py            # 31 real items with BUFF market prices
```

```
frontend/src/
├── pages/
│   ├── Home.jsx          # Market intelligence dashboard
│   └── ItemDetail.jsx    # Decision-support view per item
├── components/
│   ├── DecisionPanel.jsx    # BUY/WATCH/HOLD/AVOID + evidence chain + 7-dim scores
│   ├── OpportunityPanel.jsx # Event-aware opportunity cards with decision badges
│   └── TrendChart.jsx       # Price history visualization
└── services/
    └── api.js               # All API calls including getItemDecision, getMarketEvents
```

---

## API Reference

| Endpoint | Description |
|----------|-------------|
| `GET /api/items/{id}/decision` | Full pipeline: events → scoring → decision engine |
| `GET /api/items/{id}/score` | 7-dim score breakdown only |
| `GET /api/opportunities?limit=8` | Top opportunities with decision signals |
| `GET /api/market/events` | Active market events with timing labels |
| `GET /api/market-summary` | Market mood, buy signals, avg score |
| `POST /api/items/{id}/chat` | Streaming AI chat grounded in decision context |
| `POST /api/rag/query` | RAG query over knowledge base |

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env          # add CLAUDE_API_KEY
uvicorn app.main:app --reload --port 8000

# Seed the database
curl -X POST http://localhost:8000/api/seed

# Frontend
cd frontend
npm install
npm run dev
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| AI | Claude claude-opus-4-6 (Anthropic SDK, streaming) |
| Retrieval | scikit-learn TF-IDF (char_wb n-grams, mixed CJK/EN) |
| Frontend | React 18, Vite 5, Tailwind CSS |
| Scoring | Pure Python — deterministic, no LLM in scoring loop |

**The scoring and decision engines are fully deterministic.** No LLM is involved in computing scores or recommendations — Claude is only used for generating natural-language explanations after the structured analysis is complete.

---

## Design Principles

- **Structured signals first.** Every recommendation traces back to numeric evidence, not an opaque LLM answer.
- **Events drive scoring.** A static score without market context is incomplete. Event signal is a first-class scoring dimension.
- **Explainability by default.** The `supporting_signals` array in every decision response is a complete audit trail — every point is attributed to a specific signal with a direction and magnitude.
- **AI as synthesis layer.** Claude receives structured decision output as grounded context. It explains and elaborates; it does not compute.
- **Performance-conscious.** Events load once per scan with a 5-minute TTL cache. `map_events_to_item` is pure Python with no I/O.
