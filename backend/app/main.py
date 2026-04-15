from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, Base
import app.models  # noqa: register all models

from app.routers import items, analytics, compare, rental, reports, buff, chat, rag
from app.services.price_fetcher import refresh_all_prices

app = FastAPI(title="SkinSense AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(items.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(rental.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(buff.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")


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
