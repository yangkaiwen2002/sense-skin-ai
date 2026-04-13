"""
BUFF.163.com sell-order client.

Reads credentials from .env (never hardcoded):
    BUFF_COOKIE       — your session cookie string
    BUFF_USER_AGENT   — browser UA (optional, has default)
    BUFF_REFERER      — referer header (optional, has default)
"""

import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://buff.163.com"


def _headers() -> dict[str, str]:
    return {
        "Cookie":          os.getenv("BUFF_COOKIE", ""),
        "User-Agent":      os.getenv(
            "BUFF_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ),
        "Referer":         os.getenv("BUFF_REFERER", "https://buff.163.com/market/"),
        "X-Requested-With": "XMLHttpRequest",
        "Accept":          "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def _sleep():
    time.sleep(random.uniform(1.5, 2.0))


def _get(url: str, params: dict) -> dict | None:
    """Raw GET with error handling. Returns parsed JSON or None."""
    try:
        r = requests.get(url, params=params, headers=_headers(), timeout=12)
    except requests.exceptions.Timeout:
        return {"_err": "timeout"}
    except requests.exceptions.RequestException as e:
        return {"_err": str(e)}

    if r.status_code != 200:
        return {"_err": f"http_{r.status_code}"}

    try:
        return r.json()
    except ValueError:
        return {"_err": "json_parse_failed", "_body": r.text[:200]}


# ── public API ──────────────────────────────────────────────────────────────

def fetch_buff_sell_orders(
    goods_id: int,
    page_num: int = 1,
    sort_by: str = "default",
    allow_tradable_cooldown: int = 1,
) -> dict:
    """
    Fetch sell orders for a BUFF goods_id.

    Returns:
        {
          "ok": bool,
          "error": str | None,
          "goods_id": int,
          "page_num": int,
          "total": int,
          "lowest_price": float | None,
          "median_price": float | None,
          "orders": [
            {
              "price": float,
              "sell_num": int,
              "paintwear": float | None,
              "paintseed": int | None,
              "stickers": list[str],
              "tradable_cooldown_text": str | None,
            },
            ...
          ]
        }
    """
    data = _get(
        f"{_BASE}/api/market/goods/sell_order",
        {
            "game":                   "csgo",
            "goods_id":               goods_id,
            "page_num":               page_num,
            "sort_by":                sort_by,
            "mode":                   "",
            "allow_tradable_cooldown": allow_tradable_cooldown,
        },
    )
    _sleep()

    if not data or "_err" in data:
        return {"ok": False, "error": data.get("_err") if data else "no_response",
                "orders": [], "total": 0, "goods_id": goods_id}

    if data.get("code") != "OK":
        return {"ok": False, "error": data.get("code", "unknown"),
                "orders": [], "total": 0, "goods_id": goods_id}

    payload  = data.get("data", {})
    raw_list = payload.get("items", [])
    total    = payload.get("total_count", 0)

    orders = []
    for item in raw_list:
        asset = item.get("asset_info") or {}
        info  = asset.get("info") or {}
        stickers = [s["name"] for s in info.get("stickers", []) if s.get("name")]

        orders.append({
            "price":                   float(item.get("price", 0)),
            "sell_num":                item.get("sell_num", 1),
            "paintwear":               asset.get("paintwear"),
            "paintseed":               asset.get("paintseed"),
            "stickers":                stickers,
            "tradable_cooldown_text":  item.get("tradable_cooldown_text"),
        })

    prices = [o["price"] for o in orders]
    return {
        "ok":           True,
        "error":        None,
        "goods_id":     goods_id,
        "page_num":     page_num,
        "total":        total,
        "lowest_price": prices[0]              if prices else None,
        "median_price": prices[len(prices)//2] if prices else None,
        "orders":       orders,
    }


def fetch_buff_goods_info(goods_id: int) -> dict:
    """
    Fetch summary info (min sell price, max buy order, listing count).

    Returns:
        {
          "ok": bool,
          "goods_id": int,
          "name": str,
          "sell_min_price": float | None,
          "buy_max_price":  float | None,
          "sell_num":       int | None,
        }
    """
    data = _get(
        f"{_BASE}/api/market/goods/info",
        {"game": "csgo", "goods_id": goods_id},
    )
    _sleep()

    if not data or "_err" in data:
        return {"ok": False, "error": data.get("_err") if data else "no_response",
                "goods_id": goods_id}

    if data.get("code") != "OK":
        return {"ok": False, "error": data.get("code"), "goods_id": goods_id}

    d = data.get("data", {})
    return {
        "ok":             True,
        "goods_id":       goods_id,
        "name":           d.get("market_hash_name"),
        "name_zh":        d.get("short_name"),
        "sell_min_price": float(d["sell_min_price"]) if d.get("sell_min_price") else None,
        "buy_max_price":  float(d["buy_max_price"])  if d.get("buy_max_price")  else None,
        "sell_num":       d.get("sell_num"),
    }


def fetch_buff_search(keyword: str, page_num: int = 1) -> dict:
    """
    Search BUFF market by keyword — useful for finding goods_id from an item name.

    Returns:
        {
          "ok": bool,
          "items": [{"goods_id": int, "name": str, "sell_min_price": float}, ...]
        }
    """
    data = _get(
        f"{_BASE}/api/market/search",
        {"game": "csgo", "search": keyword, "page_num": page_num, "page_size": 20},
    )
    _sleep()

    if not data or "_err" in data or data.get("code") != "OK":
        return {"ok": False, "items": []}

    items = data.get("data", {}).get("items", [])
    return {
        "ok": True,
        "items": [
            {
                "goods_id":      i.get("id"),
                "name":          i.get("market_hash_name"),
                "name_zh":       i.get("short_name"),
                "sell_min_price": float(i["sell_min_price"]) if i.get("sell_min_price") else None,
                "sell_num":      i.get("sell_num"),
            }
            for i in items
        ],
    }
