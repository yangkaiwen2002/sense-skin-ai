# SenseSkin AI

**CS2 皮肤市场智能决策系统**

A market intelligence and decision-support system for CS2 skin trading. The core value is not chat — it's **identifying opportunities, explaining risks, and supporting buy/hold/avoid decisions** using a structured pipeline over stored prices, curated events, and a small knowledge base. The local demo includes seeded histories and estimated prices; it is not an independently verified live trading feed.

---

## What This Is

SenseSkin is built around one principle: **AI as a system component, not the whole product.**

The system scores available items across 7 independent dimensions, maps active market events to per-item relevance, runs a transparent decision engine, and surfaces the results as actionable intelligence — not just chat responses.

```
Market Events  ──────────────────────┐
Price History  → 7-Dim Scoring   → Decision Engine → BUY / WATCH / HOLD / AVOID
Item Attributes → Event Mapper   → Evidence Chain  → Explainable Rationale
Knowledge Base → Hybrid Retrieval → RAG Layer      → Grounded AI Answers
```

---

## Core Features

### 1. Opportunity Scanner
Scans every item with full event context and surfaces investment opportunities ranked by the decision engine. Each card shows:
- Decision signal: **BUY / WATCH / HOLD / AVOID**
- Rule signal strength (0–100%; not a calibrated probability)
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

**Evaluation and limitations**: a reproducible 24-query bilingual labeled suite reports Hit@3, Recall@3, MRR@3 and nDCG@3 for TF-IDF, BM25 and lexical RRF. CI checks against the committed baseline; see [evaluation methodology and results](backend/evaluation/README.md). This small author-labeled set is not a held-out benchmark and does not establish production accuracy. The optional semantic mode refuses to report results when embeddings fall back. The 32-entry knowledge base is static and fusion weights remain untuned.

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
| `POST /api/rag/search` | Key-free JSON evidence search with source passages and retrieval diagnostics |
| `POST /api/rag/query` | RAG query over knowledge base (hybrid FAISS+BM25+TF-IDF retrieval) |

---

## Research workspace

![Marketplace preview](docs/screenshots/marketplace.jpg)

[Research workspace](docs/screenshots/research.jpg) · [Item detail](docs/screenshots/detail.jpg) · [Mobile workspace](docs/screenshots/mobile.jpg)


- A responsive marketplace with light surfaces, Steam-hosted item artwork, weapon/exterior filters, price sorting, accessible navigation, and consistent detail pages.
- Persistent browser-local watchlists: add/remove items from detail pages and revisit saved items with refreshed backend quotes.
- **Local research briefs** combine loaded platform prices, rule scores, positive/negative evidence and follow-up checks. Export a plain-text brief without an external AI call. Missing data stays explicitly missing.
- The **AI 研究** workspace unifies item research, platform comparison, rent/buy and knowledge Q&A. Conversations, tool steps, sources and exportable results persist on the backend. Without a configured model it explicitly produces evidence records only.
- A failed generation keeps its evidence visible. Request cancellation and SSE parsing handle fragmented UTF-8, premature disconnects, and stale request completion.
- Dashboard cards no longer present an unrelated approximation as the seven-dimensional backend score. Rule signal strength is explicitly not a probability of returns.
- Routes are lazy-loaded so detail-page charts do not ship with the initial market page.

## Running Locally

```bash
# Lightweight backend: no model weights or API key required
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-core.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Use **初始化示例数据** for the local market demo, or open **AI 研究 → 知识问答** to search the knowledge base without initializing items. The seed data is synthetic/illustrative, not a live performance record. Existing histories may contain legacy estimates; new refreshes store observed quotes only (see integration details below).

To enable generated answers in the research workspace, configure `AI_PROVIDER`, `AI_API_KEY` and `AI_MODEL` in the backend `.env` (see [model setup](#connect-a-model)); the existing `CLAUDE_API_KEY` remains a fallback. To enable actual semantic retrieval, install `faiss-cpu sentence-transformers` and set `RAG_ENABLE_FAISS=true`; first use can download the embedding model. Knowledge entries contain unverified historical numerical claims and must not be treated as current prices.

```bash
# Standalone evidence API; no generation cost
curl -X POST http://localhost:8000/api/rag/search \
  -H 'Content-Type: application/json' \
  -d '{"question":"如何评估皮肤流动性？","top_k":3}'

# Backend tests and retrieval regression gate, from backend/
pip install -r requirements-dev.txt
python -m pytest tests -q
python -m app.rag.evaluation --output evaluation/ci-results.json --baseline evaluation/results.json

# Frontend stream tests and production build, from frontend/
npm test
npm run build
```

GitHub Actions runs both test suites, the retrieval regression gate, and the production build on pushes and pull requests. It uploads the per-query retrieval report, including misses. Live Claude and real-embedding integration are optional and are not claimed by the offline CI suite.


---

Artwork sources and limitations: [THIRD_PARTY.md](THIRD_PARTY.md).

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

## Observed market data integration

The refresh pipeline now stores **only observed Steam quotes and explicitly configured BUFF quotes**. It no longer creates other platforms' prices, buy orders, or 24h averages from fixed multipliers. Existing histories are retained with `price_kind=legacy_unknown`; new seeds use `demo`, and live ingestions use `observed`, with source identity and collection time.

- Exact market names in `backend/data_sources/item_catalog.py` replace database-ID matching. The conservative catalog currently maps 15 of 31 seeded items. Unmapped items are reported as skipped; verify weapon, finish, exterior, StatTrak/souvenir and knife prefix before adding entries.
- Once an item has observed quotes, demo platforms are excluded from its comparison. Daily analytics also stay within one platform, source and data kind; new live data cannot borrow synthetic historical returns. Seven-day returns require both daily endpoints. Daily averages use the last quote per UTC date, not the last N polls. Missing days stay missing.
- Quotes older than 24 hours are flagged, and scoring refuses stale reference quotes. Listed prices are observations, not guaranteed executable trades. The remaining local rental history is demo data.
- The additive startup upgrade adds provenance columns to old databases without relabeling their contents. Start one backend worker during this upgrade; a versioned migration runner is still needed for multi-worker production deployments.

### Steam prices

Start the backend as above, initialize the demo catalog if empty, then click **刷新价格** or call:

```bash
curl -X POST http://localhost:8000/api/refresh-prices
```

This uses the existing public Community Market `priceoverview` route, without a key. It is not a guaranteed market-data service: availability, item coverage and throttling can prevent a quote. The response distinguishes successful, failed and unmapped records. Automatic polling is opt-in via `ENABLE_MARKET_SYNC=true`; the single-process scheduler runs every 15 minutes. The process-level refresh guard and manual endpoint rate limits do not replace a distributed job queue.

### BUFF prices

The current adapter uses BUFF's website session routes, **not a verified official price API contract**. It is implemented but requires a working user session and identity mapping; cookie expiry or changed response formats can stop it.

1. Put your own valid `BUFF_COOKIE` in the backend `.env` locally. Do not put it in frontend variables or commit it.
2. Use `GET /api/buff/search?q=...` to locate a goods ID, then `GET /api/buff/goods-info?goods_id=...` to verify the returned English `name` matches the canonical Steam hash name exactly.
3. Set `BUFF_GOODS_IDS` to a JSON object mapping that exact English name to its numeric goods ID. The template defaults to `{}` and therefore disables BUFF ingestion.
4. Restart the backend and refresh prices. A mismatched identity is rejected before any snapshot is written. Inspect `buff_status` and per-item results; configuration alone does not prove live access.

悠悠有品 and IGXE still need independently verified source adapters or an authorized data-provider contract. No live integration is claimed for either platform. Actual rental prices, deposits and availability also remain unconnected.

### Official CS2 events

The [official Steam ISteamNews API](https://partner.steamgames.com/doc/webapi/ISteamNews) documents `GetNewsForApp/v2/`; its public method does not require the publisher key used by `GetNewsForAppAuthed`.

```bash
curl -X POST http://localhost:8000/api/refresh-events
curl http://localhost:8000/api/market/news
```

The home page has a **同步官方新闻** button. The connector requests app 730's `steam_community_announcements` feed, stores announcements by stable Steam ID, and exposes publication time, collection time and the source link. Repeated syncs update existing records, and network failures preserve previously collected news. News is also visible on item event timelines, explicitly labeled as global context with impact pending evaluation.

Official announcements do **not** automatically become bullish/bearish scores. The existing curated event-scoring pipeline remains separate until item relevance, impact direction and evaluation rules are established. Automated HLTV tournament ingestion is still absent.

### Rent/buy assumptions

The comparison now honors the upfront budget and available rental stock. Unknown deposits stay unknown. Weekly rentals use whole-week blocks plus available daily pricing; fractional-week billing is not assumed. `expected_resale_loss_pct` describes a scenario for the requested holding period, not a weekly loss prediction. Platform fees and future price movements are not modeled.

## AI research workspace

Open **AI 研究** (`/research`), or carry an item into research from its detail page. The workspace follows the useful Nexus interaction patterns: persistent conversations, visible tool execution, inspectable sources, and saved output. It runs a bounded research workflow over this repository's services; it is not an autonomous agent that invents or executes arbitrary tools.

1. Select up to three items and choose market research, platform comparison, rent/buy, or knowledge Q&A.
2. Submit a question. With refresh enabled, the backend refreshes only selected items lacking an observed quote in the last five minutes, reads official announcements (15-minute cache), loads platform comparisons and optional rental calculations, and searches the local knowledge base.
3. Actual tool starts, outcomes and source records stream to the UI. Source failures preserve other evidence. A configured model receives the current evidence plus the last four completed conversation turns and generates a cited answer.
4. Each run saves its question, scope, parameters, steps, sources and answer. Reopen its session URL to continue; download a completed record as Markdown. Failed/cancelled runs retain received evidence/text and can be retried with their original scope and parameters.

### Connect a model

Copy `backend/.env.example` to `backend/.env` if it does not already exist, and set these variables on the backend only:

```dotenv
AI_PROVIDER=anthropic
AI_API_KEY=your_key
AI_MODEL=your_enabled_model_id
AI_BASE_URL=
```

For an OpenAI-compatible gateway, set `AI_PROVIDER=openai`, its enabled model ID, and `AI_BASE_URL=https://your-gateway.example/v1` (or the gateway's documented base path). The adapter appends `/chat/completions`; it requires streaming Chat Completions support. Anthropic gateways must support native Messages streaming. Keys never belong in `VITE_*` variables. Restart the backend after changing configuration. Existing `CLAUDE_API_KEY` remains a fallback for the research adapter and is still used by the legacy chat/report endpoints.

Without a key and model, the workspace explicitly runs in **证据模式** and produces a deterministic evidence record, not an AI conclusion. “模型已配置” means configuration is present, not that a paid upstream call has succeeded. Incomplete model streams fail the run and do not produce a completed report.

### Research API and operational limits

- `GET /api/research/status`: model configuration and source capabilities, without credentials.
- `GET/POST /api/research/sessions`: list/create local sessions.
- `GET /api/research/sessions/{id}`: restore context, runs and latest tool states.
- `POST /api/research/sessions/{id}/runs`: SSE (`run`, `step`, `sources`, `text`, `notice`, `error`, `completed`, then `[DONE]`). Send a UUID `request_id`; a completed duplicate is replayed rather than re-executed.
- `GET /api/research/runs/{id}/artifact`: download a completed Markdown record.

A session allows one active run, reserved atomically in the database. Runs have a 240-second deadline, selected-item limits and rate limits. Disconnect/stop cancels execution and preserves progress. This is not a background job queue: a browser refresh may interrupt the active run. A killed worker's abandoned session lease is recovered after ten minutes. SQLite tables are created additively on startup. This local prototype has no user isolation/authentication; do not publish its session API as a multi-user service without adding those controls.

Steam quote access and news access still depend on upstream availability. BUFF requires separate credentials and exact mapping; rental/deposit data is not live. FAISS is optional; the default lexical retrieval path uses BM25 and character TF-IDF. Source cards retain provenance and time, and global announcements do not imply a measured item-price impact.

### Validation

```bash
cd backend
.venv/bin/python -m pytest tests/test_market_pipeline.py tests/test_research_workflow.py -q
cd ../frontend
npm test
npm run build
```

Research regressions cover persisted replay/export, scope validation, active-run conflicts, cancellation and abandoned leases, source degradation, selected-item refresh, rental budgets, conversation history, and incomplete model streams. Model HTTP fixtures are test-only; they do not stand in for a verified live model connection.
