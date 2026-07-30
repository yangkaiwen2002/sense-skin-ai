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

### 5. RAG-Based Market Knowledge (Hybrid Retrieval)
A hybrid retrieval layer over a curated knowledge base (32 entries as of this writing) covering:
- Rarity tiers and pricing dynamics
- Exterior grades and float value impact
- Tournament effects on skin demand
- Platform differences (BUFF vs Steam vs 悠悠有品)
- Rent vs buy decision framework
- StatTrak premium logic

Retrieval combines three independent engines, implemented in `backend/app/rag/`:

| Engine | Library | Role |
|---|---|---|
| FAISS (`IndexFlatIP`, cosine similarity) | `faiss-cpu` + `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim) | Semantic recall — finds relevant entries even when the query shares no literal words with the document (paraphrases, synonyms) |
| BM25 (`BM25Okapi`) | `rank-bm25` | Keyword / term overlap — a custom mixed CN/EN tokenizer (`app/rag/tokenization.py`) lowercases English tokens and splits Chinese runs into overlapping character bigrams, since whitespace tokenization doesn't work for Chinese |
| TF-IDF (`char_wb`, 2–4 grams) | `scikit-learn` | Exact character-level matching — strong on abbreviations, item names, and precise CN/EN substrings |

The three ranked lists are combined with weighted **Reciprocal Rank Fusion** (`app/rag/fusion.py`), not by summing raw scores directly (their scales aren't comparable — BM25's unbounded term-weight sum vs. two different cosine-similarity ranges):

```
RRF_score(d) = w_faiss / (k + rank_faiss) + w_bm25 / (k + rank_bm25) + w_tfidf / (k + rank_tfidf)
```
with `k = 60` and default weights `FAISS = 0.45, BM25 = 0.35, TF-IDF = 0.20` (`FusionWeights` in `fusion.py`).

**Degrade path**: FAISS is a soft dependency. If the embedding model can't be loaded (no network, no local model cache, `faiss-cpu`/`sentence-transformers` missing) the retriever logs a warning, excludes `faiss` from `active_retrievers`, and automatically renormalizes the BM25/TF-IDF weights to sum to 1 — the `/api/rag/query` endpoint keeps working on BM25 + TF-IDF only, it never raises because of a FAISS failure.

Each result carries `fused_score` (kept as `score` too, for backward compatibility) plus a `retrieval_details` breakdown (`faiss_rank`/`faiss_score`, `bm25_rank`/`bm25_score`, `tfidf_rank`/`tfidf_score`, `active_retrievers`) so the fusion is auditable.

**Known limitations**: the knowledge base is small (32 hand-written entries) and has not undergone large-scale retrieval evaluation — no Precision/Recall/MRR numbers exist for this system. Manual spot-checks show the fusion sometimes ranks a tangentially related document above the most on-topic one when a shorter document has a higher BM25 term weight. Weights (`0.45/0.35/0.20`) are a reasonable starting point, not a tuned/validated configuration.

When Claude answers a question (RAG or item chat), its system prompt is grounded with the retrieved context (RAG) or the full decision output, event context, and scoring breakdown (item chat) — not just raw price data. If hybrid retrieval finds nothing for a question, the prompt explicitly tells Claude to say so rather than imply the answer came from the knowledge base.

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
│   │   ├── retriever.py        # HybridRetriever: orchestrates TF-IDF + BM25 + FAISS, RRF fusion
│   │   ├── tokenization.py     # Mixed CN/EN tokenizer shared by the BM25 engine
│   │   ├── embeddings.py       # sentence-transformers embedder + FAISS IndexFlatIP wrapper
│   │   ├── fusion.py           # Reciprocal Rank Fusion (RRF) + FusionWeights
│   │   └── models.py           # KnowledgeEntry / RetrievalResult / RetrievalDetail dataclasses
│   └── utils/
│       └── metrics.py          # compute_avg, compute_return, compute_volatility, compute_liquidity_score
├── data/
│   ├── events.json             # 22 structured market signals (tournaments, patches, seasonal)
│   └── knowledge.json          # RAG knowledge base (32 articles)
├── tests/                      # pytest suite for the hybrid retriever + RRF + API validation
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
| `POST /api/rag/query` | RAG query over knowledge base (hybrid FAISS+BM25+TF-IDF retrieval) |

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

# Backend tests (no network required; FAISS-dependent cases use a fake
# embedder — see backend/tests/conftest.py)
cd backend
pytest tests/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| AI | Claude claude-opus-4-6 (Anthropic SDK, streaming) |
| Retrieval | Hybrid: FAISS (`faiss-cpu` + `sentence-transformers`, semantic) + BM25 (`rank-bm25`, keyword) + scikit-learn TF-IDF (char_wb n-grams, exact CN/EN substrings), fused with weighted RRF |
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
