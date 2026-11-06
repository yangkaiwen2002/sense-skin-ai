"""Official CS2 announcements as source facts, without inferred price impact."""
import asyncio
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session
from app.models.source_news import SourceNews

NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
_lock = asyncio.Lock()


def normalize_news(raw, now):
    if not isinstance(raw, dict) or raw.get("feedname") != "steam_community_announcements":
        return None
    try:
        gid, title, url = str(raw["gid"]), str(raw["title"]).strip(), str(raw["url"])
        published = datetime.fromtimestamp(int(raw["date"]), timezone.utc).replace(tzinfo=None)
        parsed = urlparse(url)
        if not gid.isdigit() or not title or published > now + timedelta(minutes=5):
            return None
        if parsed.scheme != "https" or parsed.hostname not in {"steamcommunity.com", "store.steampowered.com", "steamstore-a.akamaihd.net"}:
            return None
        summary = unescape(re.sub(r"<[^>]*>|\[[^\]]*\]", " ", str(raw.get("contents", ""))))
        return dict(id=f"steam:{gid}", title=title[:500], summary=" ".join(summary.split())[:2000],
                    source_url=url, published_at=published, fetched_at=now)
    except (KeyError, ValueError, TypeError, OverflowError, OSError):
        return None


async def refresh_news(db: Session):
    if _lock.locked():
        return {"status": "busy", "message": "新闻刷新已在进行中"}
    async with _lock:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
                response = await client.get(NEWS_URL, params={
                    "appid": 730, "count": 30, "maxlength": 2000,
                    "feeds": "steam_community_announcements",
                })
                response.raise_for_status()
                payload = response.json()
            raw = payload["appnews"]["newsitems"]
            if not isinstance(raw, list) or payload["appnews"].get("appid") != 730:
                raise ValueError("Unexpected Steam news response")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return {"status": "error", "message": "Steam 新闻获取失败，已保留上次成功数据"}
        now, fetched, skipped = datetime.utcnow(), 0, 0
        try:
            for raw_item in raw:
                data = normalize_news(raw_item, now)
                if data is None:
                    skipped += 1
                    continue
                existing = db.get(SourceNews, data["id"])
                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                else:
                    db.add(SourceNews(**data))
                db.flush()  # duplicate IDs in a single upstream batch remain idempotent
                fetched += 1
            db.commit()
        except Exception:
            db.rollback()
            raise
        return {"status": "success" if fetched or not raw else "error", "fetched": fetched, "skipped": skipped}


def get_news(db: Session, days=90):
    now = datetime.utcnow()
    rows = db.query(SourceNews).filter(
        SourceNews.published_at >= now - timedelta(days=days), SourceNews.published_at <= now,
    ).order_by(SourceNews.published_at.desc()).limit(100).all()
    return [{"id": row.id, "event_date": row.published_at.isoformat() + "Z",
             "event_type": "official_news", "title": row.title, "summary": row.summary,
             "source": "Steam / CS2 官方公告", "source_url": row.source_url,
             "fetched_at": row.fetched_at.isoformat() + "Z", "tags": ["全局公告", "影响待评估"]}
            for row in rows]
