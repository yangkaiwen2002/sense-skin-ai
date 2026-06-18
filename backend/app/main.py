from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, Base, SessionLocal
import app.models  # noqa: register all models

from app.limiter import limiter
from app.routers import items, analytics, compare, rental, reports, buff, chat, rag, scoring
from app.services.price_fetcher import refresh_all_prices

_scheduler = AsyncIOScheduler()


async def _scheduled_refresh():
    db: Session = SessionLocal()
    try:
        await refresh_all_prices(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _scheduler.add_job(_scheduled_refresh, "interval", minutes=15, id="price_refresh")
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


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


@app.get("/")
def root():
    return {"status": "ok", "service": "SkinSense AI"}


@app.post("/api/refresh-prices")
async def refresh_prices_endpoint(db: Session = Depends(get_db)):
    """Fetch real-time prices from Steam Market and store as new snapshots."""
    return await refresh_all_prices(db)


@app.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    from seed.seed_data import seed
    return seed(db)
