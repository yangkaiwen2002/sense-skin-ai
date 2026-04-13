"""
Single-file seed script. Run via the /api/seed endpoint or directly:
  cd backend && python -m seed.seed_data
"""

import random
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.models.rental_snapshot import RentalSnapshot
from app.models.market_event import MarketEvent, EventTag
import app.models  # noqa: ensure all models registered


def random_walk(base: float, days: int, volatility: float = 0.02) -> list[float]:
    prices = [base]
    for _ in range(days - 1):
        change = random.gauss(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(round(max(new_price, base * 0.5), 2))
    return prices


def seed(db: Session) -> dict:
    if db.query(Item).count() > 0:
        return {"status": "already_seeded", "message": "Database already contains data."}

    # --- Platforms ---
    platforms_data = [
        {"name": "BUFF", "supports_rental": False, "region": "CN", "notes": "国内最大饰品交易平台"},
        {"name": "Steam", "supports_rental": False, "region": "Global", "notes": "Steam 官方市场"},
        {"name": "悠悠有品", "supports_rental": True, "region": "CN", "notes": "支持租赁服务"},
        {"name": "IGXE", "supports_rental": True, "region": "CN", "notes": "支持租赁服务"},
    ]
    platforms = []
    for pd in platforms_data:
        p = Platform(**pd)
        db.add(p)
        platforms.append(p)
    db.flush()

    buff = platforms[0]
    steam = platforms[1]
    youpin = platforms[2]
    igxe = platforms[3]

    # Platform price multipliers vs BUFF
    multipliers = {
        buff.id: 1.0,
        steam.id: 1.10,
        youpin.id: 1.03,
        igxe.id: 1.02,
    }

    # --- Items ---
    items_data = [
        {
            "item_name": "AK-47 | 红线 (久经沙场)",
            "weapon_type": "步枪",
            "skin_name": "红线",
            "rarity": "精工",
            "exterior": "久经沙场",
            "stattrak": False,
            "souvenir": False,
            "category": "步枪",
            "base_price": 350.0,
        },
        {
            "item_name": "爪子刀 | 多普勒 (崭新出厂)",
            "weapon_type": "刀",
            "skin_name": "多普勒",
            "rarity": "隐秘",
            "exterior": "崭新出厂",
            "stattrak": False,
            "souvenir": False,
            "category": "刀",
            "base_price": 8000.0,
        },
        {
            "item_name": "M4A1 消音型 | 印花集 (崭新出厂)",
            "weapon_type": "步枪",
            "skin_name": "印花集",
            "rarity": "隐秘",
            "exterior": "崭新出厂",
            "stattrak": False,
            "souvenir": False,
            "category": "步枪",
            "base_price": 1200.0,
        },
        {
            "item_name": "AWP | 龙狙 (久经沙场)",
            "weapon_type": "狙击枪",
            "skin_name": "龙狙",
            "rarity": "隐秘",
            "exterior": "久经沙场",
            "stattrak": False,
            "souvenir": False,
            "category": "狙击枪",
            "base_price": 25000.0,
        },
        {
            "item_name": "M4A4 | 嚎叫 (久经沙场)",
            "weapon_type": "步枪",
            "skin_name": "嚎叫",
            "rarity": "违禁",
            "exterior": "久经沙场",
            "stattrak": False,
            "souvenir": False,
            "category": "步枪",
            "base_price": 18000.0,
        },
        {
            "item_name": "蝴蝶刀 | 渐变之色 (崭新出厂)",
            "weapon_type": "刀",
            "skin_name": "渐变之色",
            "rarity": "隐秘",
            "exterior": "崭新出厂",
            "stattrak": False,
            "souvenir": False,
            "category": "刀",
            "base_price": 12000.0,
        },
        {
            "item_name": "沙漠之鹰 | 火焰 (崭新出厂)",
            "weapon_type": "手枪",
            "skin_name": "火焰",
            "rarity": "受限",
            "exterior": "崭新出厂",
            "stattrak": False,
            "souvenir": False,
            "category": "手枪",
            "base_price": 800.0,
        },
        {
            "item_name": "格洛克 18 型 | 渐变之色 (崭新出厂)",
            "weapon_type": "手枪",
            "skin_name": "渐变之色",
            "rarity": "保密",
            "exterior": "崭新出厂",
            "stattrak": False,
            "souvenir": False,
            "category": "手枪",
            "base_price": 450.0,
        },
    ]

    items = []
    for idx, id_data in enumerate(items_data):
        base_price = id_data.pop("base_price")
        item = Item(**id_data)
        db.add(item)
        items.append((item, base_price))
    db.flush()

    # --- Price snapshots (35 days) ---
    now = datetime.utcnow()
    days = 35

    for item, base_price in items:
        buff_prices = random_walk(base_price, days, volatility=0.025)
        # Simulate slight upward trend in last 7 days for some items
        if item.rarity in ("隐秘", "违禁"):
            for i in range(days - 7, days):
                buff_prices[i] = round(buff_prices[i] * 1.008, 2)

        for platform in platforms:
            mult = multipliers[platform.id]
            for day_idx in range(days):
                snap_time = now - timedelta(days=days - day_idx - 1)
                listing = round(buff_prices[day_idx] * mult, 2)
                buy_order = round(listing * random.uniform(0.94, 0.98), 2)
                spread = round(listing - buy_order, 2)
                volume = random.randint(5, 80) if platform == buff else random.randint(1, 20)
                depth = random.randint(10, 100)

                snap = PriceSnapshot(
                    item_id=item.id,
                    platform_id=platform.id,
                    snapshot_time=snap_time,
                    listing_price=listing,
                    buy_order_price=buy_order,
                    avg_price_24h=round((listing + buy_order) / 2, 2),
                    volume_24h=volume,
                    liquidity_depth=depth,
                    spread=spread,
                    currency="CNY",
                )
                db.add(snap)

        # --- Rental snapshots (悠悠有品 and IGXE only) ---
        for rental_platform in [youpin, igxe]:
            for day_idx in range(days):
                snap_time = now - timedelta(days=days - day_idx - 1)
                daily_rate = round(buff_prices[day_idx] * random.uniform(0.006, 0.01), 2)
                weekly_rate = round(daily_rate * 7 * 0.85, 2)
                snap = RentalSnapshot(
                    item_id=item.id,
                    platform_id=rental_platform.id,
                    snapshot_time=snap_time,
                    daily_rental_price=daily_rate,
                    weekly_rental_price=weekly_rate,
                    available_count=random.randint(2, 15),
                    deposit_required=True,
                    currency="CNY",
                )
                db.add(snap)

    db.flush()

    # --- Market events ---
    events_data = [
        {
            "event_date": now - timedelta(days=3),
            "event_type": "game_update",
            "source": "Valve",
            "title": "CS2 武器平衡更新",
            "summary": "本次更新对 M4A1-S 伤害进行了调整，同时修复了多个 bug。武器变动可能短期影响相关皮肤价格。",
            "impact_scope": "全平台",
            "region": "Global",
            "tags": ["weapon_update", "M4A1-S", "balance"],
        },
        {
            "event_date": now - timedelta(days=5),
            "event_type": "major_event",
            "source": "PGL",
            "title": "PGL Major 2025 上海站",
            "summary": "PGL Major 上海站正式开赛，预计持续两周。Major 期间饰品需求通常上升，贴纸相关饰品尤为明显。",
            "impact_scope": "全平台",
            "region": "CN",
            "tags": ["major", "PGL", "上海", "贴纸"],
        },
        {
            "event_date": now - timedelta(days=60),
            "event_type": "holiday",
            "source": "系统",
            "title": "2025 年春节",
            "summary": "春节期间国内玩家活跃度下降，但海外需求稳定。节后通常有一波补偿性需求上升。",
            "impact_scope": "国内平台",
            "region": "CN",
            "tags": ["春节", "节假日", "国内"],
        },
        {
            "event_date": now - timedelta(days=2),
            "event_type": "platform_promo",
            "source": "悠悠有品",
            "title": "悠悠有品春季租赁补贴活动",
            "summary": "悠悠有品推出春季租赁补贴，租赁费用最高减免 20%，活动持续至本月底。",
            "impact_scope": "悠悠有品",
            "region": "CN",
            "tags": ["租赁", "促销", "悠悠有品"],
        },
        {
            "event_date": now - timedelta(days=25),
            "event_type": "game_update",
            "source": "Valve",
            "title": "CS2 地图更新与 UI 优化",
            "summary": "更新了多张地图细节，优化了 UI 界面。本次更新对饰品市场影响较小。",
            "impact_scope": "全平台",
            "region": "Global",
            "tags": ["map_update", "UI"],
        },
        {
            "event_date": now + timedelta(days=8),
            "event_type": "tournament",
            "source": "HLTV",
            "title": "ESL Pro League Season 21 决赛周",
            "summary": "ESL Pro League S21 决赛周即将开始（数据来源：HLTV.org）。历史规律显示，决赛周前 1-2 周贴纸胶囊投机需求上升，相关队伍贴纸饰品价格往往提前拉升。",
            "impact_scope": "全平台",
            "region": "Global",
            "tags": ["ESL", "Pro League", "贴纸", "HLTV", "决赛"],
        },
        {
            "event_date": now - timedelta(days=10),
            "event_type": "tournament",
            "source": "HLTV",
            "title": "BLAST Premier Spring Final 2025",
            "summary": "BLAST Premier Spring Final 结束（数据来源：HLTV.org）。赛事期间 Natus Vincere 和 FaZe Clan 队伍相关贴纸饰品交易量明显上升，赛后胶囊开箱热度带动市场短暂活跃。",
            "impact_scope": "全平台",
            "region": "Global",
            "tags": ["BLAST", "Premier", "贴纸", "HLTV", "NaVi", "FaZe"],
        },
    ]

    for ed in events_data:
        tags = ed.pop("tags")
        event = MarketEvent(**ed)
        db.add(event)
        db.flush()
        for tag in tags:
            db.add(EventTag(event_id=event.id, tag=tag))

    db.commit()

    return {
        "status": "seeded",
        "items": len(items),
        "platforms": len(platforms),
        "events": len(events_data),
    }


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    result = seed(db)
    db.close()
    print(result)
