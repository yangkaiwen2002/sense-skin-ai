"""
Fetches real-time CS2 prices from Steam Community Market (public API, no auth required).
BUFF / 悠悠有品 / IGXE prices are estimated from Steam using historical ratios.
"""

import re
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot

# Steam Market hash names for seeded items (by item_id)
STEAM_HASH_NAMES: dict[int, str] = {
    1: "AK-47 | Redline (Field-Tested)",
    2: "Karambit | Doppler (Factory New)",
    3: "M4A1-S | Printstream (Factory New)",
    4: "AWP | Dragon Lore (Field-Tested)",
    5: "M4A4 | Howl (Field-Tested)",
    6: "Butterfly Knife | Fade (Factory New)",
    7: "Desert Eagle | Blaze (Factory New)",
    8: "Glock-18 | Fade (Factory New)",
}

# Multipliers relative to Steam price (Steam = 1.0)
# BUFF is typically ~9% cheaper than Steam; 悠悠有品 / IGXE sit between
PLATFORM_MULTIPLIERS: dict[str, float] = {
    "Steam":   1.00,
    "BUFF":    0.909,
    "悠悠有品": 0.936,
    "IGXE":   0.927,
}


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
    items = db.query(Item).all()
    if not items:
        return {"status": "error", "message": "数据库无饰品，请先调用 /api/seed 初始化"}

    platforms: dict[str, Platform] = {p.name: p for p in db.query(Platform).all()}
    if not platforms:
        return {"status": "error", "message": "数据库无平台数据，请先调用 /api/seed 初始化"}

    now = datetime.utcnow()
    fetched, failed, detail = 0, 0, []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for item in items:
            hash_name = STEAM_HASH_NAMES.get(item.id)
            if not hash_name:
                failed += 1
                detail.append({"id": item.id, "name": item.item_name, "status": "no_hash_name"})
                continue

            result = await _fetch_one(client, item.id, hash_name)

            if not result or not result["price"]:
                failed += 1
                detail.append({"id": item.id, "name": item.item_name, "status": "fetch_failed"})
            else:
                steam_price = result["price"]

                for pname, platform in platforms.items():
                    mult = PLATFORM_MULTIPLIERS.get(pname, 1.0)
                    listing   = round(steam_price * mult, 2)
                    buy_order = round(listing * 0.96, 2)
                    spread    = round(listing - buy_order, 2)

                    db.add(PriceSnapshot(
                        item_id=item.id,
                        platform_id=platform.id,
                        snapshot_time=now,
                        listing_price=listing,
                        buy_order_price=buy_order,
                        avg_price_24h=round((listing + buy_order) / 2, 2),
                        volume_24h=result["volume"] if pname == "Steam" else None,
                        liquidity_depth=None,
                        spread=spread,
                        currency="CNY",
                    ))

                fetched += 1
                detail.append({
                    "id": item.id,
                    "name": item.item_name,
                    "status": "ok",
                    "steam_price": steam_price,
                })

            # Steam rate-limit: max ~20 req/min → 1 req per 1.5s
            await asyncio.sleep(1.5)

    db.commit()
    return {
        "status": "success",
        "fetched": fetched,
        "failed": failed,
        "source": "Steam Community Market (CNY)",
        "items": detail,
    }
