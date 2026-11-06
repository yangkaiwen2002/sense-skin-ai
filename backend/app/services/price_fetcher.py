"""
Fetches real-time CS2 prices from Steam Community Market (public API, no auth required).
Only observed quotes are stored. BUFF requires a configured cookie and exact goods mapping.
"""

import re
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot

from app.config import settings
from data_sources.item_catalog import MARKET_NAMES
from data_sources.buff_client import fetch_buff_goods_info
from app.services.market_data import valid_price

_refresh_lock = asyncio.Lock()


def _parse_price(s: str | None) -> float | None:
    """'¥ 1,234.56'  →  1234.56"""
    if not s:
        return None
    cleaned = re.sub(r"[^\d.]", "", s.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_volume(s: str | None) -> int | None:
    if not s:
        return None
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return None


async def _fetch_one(client: httpx.AsyncClient, item_id: int, hash_name: str) -> dict | None:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            if attempt:
                await asyncio.sleep(2 ** attempt)
            r = await client.get(
                "https://steamcommunity.com/market/priceoverview/",
                params={
                    "country": "CN",
                    "currency": "23",   # CNY
                    "appid": "730",     # CS2
                    "market_hash_name": hash_name,
                },
                timeout=12.0,
            )
            if r.status_code in (401, 403, 429):
                return None
            if r.status_code != 200:
                continue
            data = r.json()
            if not data.get("success"):
                continue
            price = _parse_price(data.get("lowest_price"))
            if price is None or price <= 0:
                continue
            return {
                "item_id": item_id,
                "price":   price,
                "median":  _parse_price(data.get("median_price")),
                "volume":  _parse_volume(data.get("volume")),
            }
        except Exception as e:
            last_exc = e
    return None


async def refresh_all_prices(db: Session) -> dict:
    if _refresh_lock.locked():
        return {"status": "busy", "message": "行情刷新已在进行中"}
    async with _refresh_lock:
        try:
            return await _refresh(db)
        except Exception:
            db.rollback()
            raise


async def refresh_item_prices(db: Session, item_ids: list[int]) -> dict:
    """Reuse verified ingestion for an explicitly selected research scope."""
    if _refresh_lock.locked():
        return {"status": "busy", "message": "行情刷新已在进行中"}
    async with _refresh_lock:
        try:
            return await _refresh(db, item_ids)
        except BaseException:
            db.rollback()
            raise


async def _refresh(db: Session, item_ids: list[int] | None = None) -> dict:
    query = db.query(Item)
    if item_ids is not None:
        query = query.filter(Item.id.in_(item_ids))
    items = query.all()
    if not items:
        return {"status": "error", "message": "数据库无饰品，请先初始化示例目录"}
    platforms = {p.name: p for p in db.query(Platform).all()}
    for name in ("Steam", "BUFF"):
        if name not in platforms:
            platform = Platform(name=name, supports_rental=False)
            db.add(platform)
            db.flush()
            platforms[name] = platform
    fetched, failed, skipped, details = 0, 0, 0, []
    async with httpx.AsyncClient(follow_redirects=False) as client:
        for item in items:
            hash_name = MARKET_NAMES.get(item.item_name)
            if not hash_name:
                skipped += 1
                details.append({"id": item.id, "source": "catalog", "status": "unmapped_identity"})
                continue
            result = await _fetch_one(client, item.id, hash_name)
            if result:
                db.add(PriceSnapshot(
                    item_id=item.id, platform_id=platforms["Steam"].id,
                    snapshot_time=datetime.utcnow(), listing_price=result["price"],
                    volume_24h=result["volume"], currency="CNY",
                    source="steam_market", price_kind="observed", source_item_id=hash_name,
                    # priceoverview provides neither buy orders nor a 24h mean.
                ))
                fetched += 1
                details.append({"id": item.id, "source": "Steam", "status": "ok"})
            else:
                failed += 1
                details.append({"id": item.id, "source": "Steam", "status": "fetch_failed"})
            goods_id = settings.BUFF_GOODS_IDS.get(hash_name)
            if settings.BUFF_COOKIE and goods_id:
                try:
                    buff = await asyncio.to_thread(fetch_buff_goods_info, goods_id)
                except Exception:
                    buff = {"ok": False}
                price = buff.get("sell_min_price")
                if buff.get("ok") and buff.get("name") == hash_name and valid_price(price):
                    bid = buff.get("buy_max_price")
                    bid = bid if valid_price(bid) else None
                    db.add(PriceSnapshot(
                        item_id=item.id, platform_id=platforms["BUFF"].id,
                        snapshot_time=datetime.utcnow(), listing_price=price,
                        buy_order_price=bid, spread=round(price - bid, 2) if bid is not None else None,
                        liquidity_depth=buff.get("sell_num"), currency="CNY",
                        source="buff_market", price_kind="observed", source_item_id=str(goods_id),
                    ))
                    fetched += 1
                    details.append({"id": item.id, "source": "BUFF", "status": "ok"})
                else:
                    failed += 1
                    details.append({"id": item.id, "source": "BUFF", "status": "fetch_failed_or_identity_mismatch"})
            await asyncio.sleep(3)
    db.commit()
    return {
        "status": "success" if fetched and not failed else "partial" if fetched else "error",
        "fetched": fetched, "failed": failed, "skipped": skipped,
        "source": "Observed Steam / configured BUFF quotes (CNY)",
        "buff_status": "configured" if settings.BUFF_COOKIE and settings.BUFF_GOODS_IDS else "not_configured",
        "items": details,
    }
