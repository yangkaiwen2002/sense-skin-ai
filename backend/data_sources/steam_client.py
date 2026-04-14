"""
Steam Community Market public API — no login required.
CNY prices (currency=23).
"""

import re
import time
import random
import requests
from urllib.parse import quote

_BASE = "https://steamcommunity.com/market"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def _sleep():
    time.sleep(random.uniform(1.2, 1.8))


def _parse_price(s: str | None) -> float | None:
    if not s:
        return None
    try:
        return float(re.sub(r"[^\d.]", "", s.replace(",", "")))
    except ValueError:
        return None


def _get(url: str, params: dict) -> dict | None:
    try:
        r = requests.get(url, params=params, headers=_HEADERS, timeout=14)
        if r.status_code == 429:
            return {"_err": "rate_limited"}
        if r.status_code != 200:
            return {"_err": f"http_{r.status_code}"}
        return r.json()
    except requests.exceptions.Timeout:
        return {"_err": "timeout"}
    except Exception as e:
        return {"_err": str(e)}


# ── public API ───────────────────────────────────────────────────────────────

def fetch_price_overview(hash_name: str) -> dict:
    """
    Fast overview: lowest price, median, volume.
    Returns:
        { ok, hash_name, lowest_price, median_price, volume }
    """
    data = _get(f"{_BASE}/priceoverview/", {
        "country": "CN", "currency": "23", "appid": "730",
        "market_hash_name": hash_name,
    })
    _sleep()

    if not data or "_err" in data:
        return {"ok": False, "error": (data or {}).get("_err", "no_response")}
    if not data.get("success"):
        return {"ok": False, "error": "api_returned_failure"}

    volume_raw = data.get("volume", "")
    try:
        volume = int(volume_raw.replace(",", "")) if volume_raw else None
    except ValueError:
        volume = None

    return {
        "ok":           True,
        "hash_name":    hash_name,
        "lowest_price": _parse_price(data.get("lowest_price")),
        "median_price": _parse_price(data.get("median_price")),
        "volume":       volume,
    }


def fetch_listings(hash_name: str, start: int = 0, count: int = 100) -> dict:
    """
    Fetch sell listings with individual prices.
    Prices come back in fen (0.01 CNY) — we convert to CNY.

    Returns:
        { ok, hash_name, total, listings: [{price, listing_id}] }
    """
    encoded = quote(hash_name)
    data = _get(f"{_BASE}/listings/730/{encoded}/render/", {
        "query": "", "start": start, "count": count,
        "country": "CN", "language": "schinese", "currency": "23",
    })
    _sleep()

    if not data or "_err" in data:
        return {"ok": False, "error": (data or {}).get("_err"), "listings": []}
    if not data.get("success"):
        return {"ok": False, "error": "api_failure", "listings": []}

    raw = data.get("listinginfo", {})
    # Steam sometimes returns [] instead of {} when no listings exist
    if not isinstance(raw, dict):
        raw = {}

    listings = []
    for lid, info in raw.items():
        # converted_price + converted_fee = buyer pays (in fen)
        price_fen = info.get("converted_price", 0) + info.get("converted_fee", 0)
        if price_fen > 0:
            listings.append({"listing_id": lid, "price": round(price_fen / 100, 2)})

    listings.sort(key=lambda x: x["price"])
    prices = [l["price"] for l in listings]

    # Extract skin image URL from assets block
    icon_url = None
    assets = data.get("assets", {})
    if isinstance(assets, dict):
        for app_assets in assets.values():
            if not isinstance(app_assets, dict):
                continue
            for ctx_assets in app_assets.values():
                if not isinstance(ctx_assets, dict):
                    continue
                for asset in ctx_assets.values():
                    if isinstance(asset, dict) and asset.get("icon_url"):
                        icon_url = asset["icon_url"]
                        break
                if icon_url:
                    break
            if icon_url:
                break

    return {
        "ok":           True,
        "hash_name":    hash_name,
        "total":        data.get("total_count", 0),
        "listings":     listings,
        "lowest_price": prices[0]              if prices else None,
        "median_price": prices[len(prices)//2] if prices else None,
        "icon_url":     icon_url,
    }


def search_items(query: str, count: int = 15) -> dict:
    """
    Search Steam Market for CS2 items.
    Returns:
        { ok, items: [{hash_name, name, sell_listings, sell_price}] }
    """
    data = _get(f"{_BASE}/search/render/", {
        "query": query, "appid": "730", "norender": "1",
        "start": "0", "count": count,
        "country": "CN", "currency": "23", "language": "schinese",
    })
    _sleep()

    if not data or "_err" in data:
        return {"ok": False, "error": (data or {}).get("_err"), "items": []}
    if not data.get("success"):
        return {"ok": False, "error": "api_failure", "items": []}

    items = []
    for r in data.get("results", []):
        price_fen = r.get("sell_price", 0)
        icon_url = r.get("asset_description", {}).get("icon_url", "")
        items.append({
            "hash_name":     r.get("hash_name", ""),
            "name":          r.get("name", ""),
            "sell_listings": r.get("sell_listings", 0),
            "sell_price":    round(price_fen / 100, 2) if price_fen else None,
            "icon_url":      icon_url,
        })
    return {"ok": True, "items": items}
