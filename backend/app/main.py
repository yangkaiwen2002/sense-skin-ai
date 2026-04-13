from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, Base
import app.models  # noqa: register all models

from app.routers import items, analytics, compare, rental, reports

app = FastAPI(title="SkinSense AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
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


@app.get("/")
def root():
    return {"status": "ok", "service": "SkinSense AI"}


@app.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    from seed.seed_data import seed
    return seed(db)
