from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, Base, SessionLocal
import app.models  # noqa: register all models

from app.limiter import limiter
from app.routers import items, analytics, compare, rental, reports, buff, chat, rag, scoring, research
from app.services.price_fetcher import refresh_all_prices
from app.services.news_ingestion import refresh_news, get_news
from app.schema_updates import ensure_price_provenance

async def _scheduled_refresh():
    db: Session = SessionLocal()
    try:
        await refresh_all_prices(db)
        await refresh_news(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_price_provenance(engine)
    scheduler = AsyncIOScheduler()
    if settings.ENABLE_MARKET_SYNC:
        scheduler.add_job(_scheduled_refresh, "interval", minutes=15, id="market_refresh", max_instances=1)
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)



app = FastAPI(title="SkinSense AI", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(rental.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(buff.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(scoring.router, prefix="/api")
app.include_router(research.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "SkinSense AI"}


@app.post("/api/refresh-prices")
@limiter.limit("2/minute")
async def refresh_prices_endpoint(request: Request, db: Session = Depends(get_db)):
    """Fetch real-time prices from Steam Market and store as new snapshots."""
    return await refresh_all_prices(db)


@app.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    from seed.seed_data import seed
    return seed(db)


@app.post("/api/refresh-events")
@limiter.limit("2/minute")
async def refresh_events_endpoint(request: Request, db: Session = Depends(get_db)):
    return await refresh_news(db)


@app.get("/api/market/news")
def market_news(days: int = Query(90, ge=1, le=365), db: Session = Depends(get_db)):
    news = get_news(db, days)
    return {"events": news, "count": len(news)}
