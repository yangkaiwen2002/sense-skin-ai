"""
Single-file seed script. Run via the /api/seed endpoint or directly:
  cd backend && python -m seed.seed_data
"""

import random
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

    buff, steam, youpin, igxe = platforms

    multipliers = {
        buff.id: 1.0,
        steam.id: 1.12,
        youpin.id: 1.03,
        igxe.id: 1.02,
    }

    # --- Items (30+) ---
    # icon_url: Steam CDN hash (without full URL prefix)
    # Full URL: https://community.cloudflare.steamstatic.com/economy/image/{hash}
    items_data = [
        # ── 步枪 ──────────────────────────────────────────────────
        {
            "item_name": "AK-47 | 红线 (久经沙场)",
            "weapon_type": "步枪", "skin_name": "红线", "rarity": "精工",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 281.0, "volatility": 0.022,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot7HxfDhjxszJemkV09-5mpSYmqX2Pa7cqWdQ-sJ0xOjAot-jiQe3-hBkZWr0do-Scw42MwvT-FO5xu3vjZC_uJ_MnSMx7Cg8pSGKMg",
        },
        {
            "item_name": "AK-47 | 火蛇 (崭新出厂)",
            "weapon_type": "步枪", "skin_name": "火蛇", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 29000.0, "volatility": 0.03,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot7HxfDhjxszJemkV09i5nY6f2eT4SqzXg2Jfvpsr3iD3t4rwhSy3-RRpYW31doKVdQ46YVuB8lK9l-zq1cC5tJ7XiSxnvHRlsg",
        },
        {
            "item_name": "AK-47 | 二西莫夫 (久经沙场)",
            "weapon_type": "步枪", "skin_name": "二西莫夫", "rarity": "保密",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 450.0, "volatility": 0.02,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot7HxfDhjxszJemkV0966h8T0KPbkPajVl2pV5srAhfb--oLijhGy_0RsYjv1I4-UcVQ3YVuC_FTolbu5hpeu75sygnDYHKL2fA",
        },
        {
            "item_name": "M4A4 | 嚎叫 (久经沙场)",
            "weapon_type": "步枪", "skin_name": "嚎叫", "rarity": "违禁",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 21000.0, "volatility": 0.035,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpou6kusOJf2eT3fDxB6MqklYW0nfT7DLfYkWNFppAh3byto43mhVrk80VlYjr0IoCRdwA6M1nS_lK2wu3ohJ677sydnCY36D4g",
        },
        {
            "item_name": "M4A1 消音型 | 印花集 (崭新出厂)",
            "weapon_type": "步枪", "skin_name": "印花集", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 5393.0, "volatility": 0.028,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpou6kusOJf2eT3fDxB6MqklYW0nfT7DLfYkWNFppAi3rGZp9-g2wW3-xFsYmv2LY-SdlI5NVuC_lK-l-zn1pW66s1ib3Jn6mhx-vbZmA",
        },
        {
            "item_name": "M4A4 | 龙王 (崭新出厂)",
            "weapon_type": "步枪", "skin_name": "龙王", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 420.0, "volatility": 0.03,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpou6kusOJf2eT3fDxB6MqklYW0nfT7DLfYkWNFppAh3byto43mhVrk80VlYjr0IoCRcAZqNFuF_Fntl-q7jZK77p1lmHYr6FqiStX7",
        },
        {
            "item_name": "FAMAS | 骸骨钥匙 (崭新出厂)",
            "weapon_type": "步枪", "skin_name": "骸骨钥匙", "rarity": "受限",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 30.0, "volatility": 0.025,
            "icon_url": None,
        },
        {
            "item_name": "SG 553 | 科伦坡 (崭新出厂)",
            "weapon_type": "步枪", "skin_name": "科伦坡", "rarity": "受限",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 25.0, "volatility": 0.02,
            "icon_url": None,
        },

        # ── 狙击枪 ────────────────────────────────────────────────
        {
            "item_name": "AWP | 龙狙 (久经沙场)",
            "weapon_type": "狙击枪", "skin_name": "龙狙", "rarity": "隐秘",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 32000.0, "volatility": 0.04,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot621FAR17P7YJgJP7c-3hJSPkv_kDLfYkWNFppAh3byto43n2gfg-hU-ZWr2INSSdVA2aQzU_ge5xOzp0ZK56c7XiSw38D5iuTuL",
        },
        {
            "item_name": "AWP | 二西莫夫 (久经沙场)",
            "weapon_type": "狙击枪", "skin_name": "二西莫夫", "rarity": "保密",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 820.0, "volatility": 0.022,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot621FAR17P7YJgJP7c-3hJSPkv_kDLfYkWNFppA_3-vV9430iQ23-hZvYm6hctKQdlM_YFnX_1i6w-u608e56s7XiSw3kMGGY0A",
        },
        {
            "item_name": "AWP | 超导体 (崭新出厂)",
            "weapon_type": "狙击枪", "skin_name": "超导体", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 250.0, "volatility": 0.035,
            "icon_url": None,
        },
        {
            "item_name": "SSG 08 | 血腥运动 (崭新出厂)",
            "weapon_type": "狙击枪", "skin_name": "血腥运动", "rarity": "保密",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 380.0, "volatility": 0.02,
            "icon_url": None,
        },

        # ── 手枪 ──────────────────────────────────────────────────
        {
            "item_name": "沙漠之鹰 | 印花集 (崭新出厂)",
            "weapon_type": "手枪", "skin_name": "印花集", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 5800.0, "volatility": 0.035,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgposr-3Laan_kxW09C7hIWZnuOrYOLkI7XShGVZ681lxLCT94uj2Ae2-BM4N273LYaUdlNoMFvT_Fi6xuvqhMLt7J_MnSxn7Cg8pSGK7fY6IA",
        },
        {
            "item_name": "沙漠之鹰 | 火焰 (崭新出厂)",
            "weapon_type": "手枪", "skin_name": "火焰", "rarity": "受限",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 7044.0, "volatility": 0.025,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgposr-3Laan_kxW09C7hIWZnuOrYOLkIKvummpD7cF1h-zF9t6t2Fbj-BFvNW-hJdKUelBhY1nS_APryO_q0MG5vp6bnCZmuiJz7S-pyJQy0w",
        },
        {
            "item_name": "格洛克 18 型 | 渐变之色 (崭新出厂)",
            "weapon_type": "手枪", "skin_name": "渐变之色", "rarity": "保密",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 550.0, "volatility": 0.02,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgposbaqKAxf0Ob3djFN79eJh4SZhOj2M67cqWdQ-sJ0xOjAot-jiQe3-hBkZWr0do-Scw42MwvT-FO5xuLnxqKqW9_MnSxnvHRlsg",
        },
        {
            "item_name": "USP 消音版 | 杀手 (久经沙场)",
            "weapon_type": "手枪", "skin_name": "杀手", "rarity": "保密",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 720.0, "volatility": 0.022,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpoo6m1FBRp3_bGcjhQ09-jq5WYh8j_OrfdqWhe5sN4mOTE8bP5gVO8v1c-YmzzIYCWJlQ2MwrYrzT_FW8xe6_vcPKniMg",
        },
        {
            "item_name": "P250 | 邪恶大笑 (略有磨损)",
            "weapon_type": "手枪", "skin_name": "邪恶大笑", "rarity": "受限",
            "exterior": "略有磨损", "stattrak": False,
            "base_price": 55.0, "volatility": 0.02,
            "icon_url": None,
        },

        # ── 刀 ───────────────────────────────────────────────────
        {
            "item_name": "爪子刀 | 多普勒 (崭新出厂)",
            "weapon_type": "刀", "skin_name": "多普勒", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 11032.0, "volatility": 0.04,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpovbSsLQJf2PLacDBA5ciJl4yYh8j_OrfdqWhe5sN4mOTE8bP5gVO8-0BuZ2r3cYeQJlE_ZwvXqFW2ke7q1JS_v5nLwXtqvCItuz6K7A",
        },
        {
            "item_name": "蝴蝶刀 | 渐变之色 (崭新出厂)",
            "weapon_type": "刀", "skin_name": "渐变之色", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 14500.0, "volatility": 0.045,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpovbSsLQJf2PLacDBA5ciJl4yEhPLkIb3UqWZU7Mxkh9bN9J_y21Hm_RJsMjincIadcFFqNgrQqVS9wO3o1ZC5vs7InXZh7Cgksb-OjM2M",
        },
        {
            "item_name": "折叠刀 | 大马士革钢 (久经沙场)",
            "weapon_type": "刀", "skin_name": "大马士革钢", "rarity": "隐秘",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 1100.0, "volatility": 0.035,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpovbSsLQJf2PLacDBA5ciJl4yYh8j1Pb7Vqm5u5Mx2gufD8Y3g21Xk-BBvYDuncYfGJgU_YFmFrwXv2Lrs1ZG9vZuKn3Iis3ElpmaBWA",
        },
        {
            "item_name": "穿肠刀 | 虎牙 (崭新出厂)",
            "weapon_type": "刀", "skin_name": "虎牙", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 750.0, "volatility": 0.038,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpovbSsLQJf2PLacDBA5ciJl4yYh8j5Nr_Yg2Yf4Zx7j_v--oXygRAn_hBla2n6dteSdVE4N1uK_Vm6xO7t0Z6_ot2XmC0w7mw4bM_mkA",
        },
        {
            "item_name": "M9 刺刀 | 传说 (崭新出厂)",
            "weapon_type": "刀", "skin_name": "传说", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 7200.0, "volatility": 0.042,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpovbSsLQJf2PLacDBA5ciJl4yYh8j5Nr_Yg2Yf4Zx7j_v--Y3t2gfg-hU-ZWr2INSSdVA2aQ_Uqlm9wu271pC07ZnL",
        },

        # ── 冲锋枪 ────────────────────────────────────────────────
        {
            "item_name": "MP9 | 玫瑰金 (崭新出厂)",
            "weapon_type": "冲锋枪", "skin_name": "玫瑰金", "rarity": "保密",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 55.0, "volatility": 0.02,
            "icon_url": None,
        },
        {
            "item_name": "MAC-10 | 霓虹骑手 (崭新出厂)",
            "weapon_type": "冲锋枪", "skin_name": "霓虹骑手", "rarity": "受限",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 50.0, "volatility": 0.02,
            "icon_url": None,
        },
        {
            "item_name": "UMP-45 | 精英制造 (略有磨损)",
            "weapon_type": "冲锋枪", "skin_name": "精英制造", "rarity": "军规",
            "exterior": "略有磨损", "stattrak": False,
            "base_price": 20.0, "volatility": 0.018,
            "icon_url": None,
        },

        # ── 霰弹枪 ────────────────────────────────────────────────
        {
            "item_name": "XM1014 | 蓝色钛 (崭新出厂)",
            "weapon_type": "霰弹枪", "skin_name": "蓝色钛", "rarity": "军规",
            "exterior": "崭新出厂", "stattrak": False,
            "base_price": 20.0, "volatility": 0.015,
            "icon_url": None,
        },

        # ── 手套 ──────────────────────────────────────────────────
        {
            "item_name": "运动手套 | 潘多拉之盒 (久经沙场)",
            "weapon_type": "手套", "skin_name": "潘多拉之盒", "rarity": "违禁",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 11500.0, "volatility": 0.04,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpou7uRlFBj2OfYdTxL6tCJl4CVmsfLPr7Vn35cppEh3bzCot6n21bi_BI6am76IpSScA82ZQnRqFO3l-7p0Z-57c7N1Gs",
        },
        {
            "item_name": "驾驶手套 | 雪豹 (久经沙场)",
            "weapon_type": "手套", "skin_name": "雪豹", "rarity": "违禁",
            "exterior": "久经沙场", "stattrak": False,
            "base_price": 3200.0, "volatility": 0.038,
            "icon_url": None,
        },

        # ── StatTrak ──────────────────────────────────────────────
        {
            "item_name": "StatTrak™ AK-47 | 红线 (久经沙场)",
            "weapon_type": "步枪", "skin_name": "红线", "rarity": "精工",
            "exterior": "久经沙场", "stattrak": True,
            "base_price": 1050.0, "volatility": 0.028,
            "icon_url": "-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXH5ApeO4YmlhxYQknCRvCo04DEVlxkKgpot7HxfDhjxszJemkV09-5mpSYmqX2Pa7cqWdQ-sJ0xOjAot-jiQe3-hBkZWr0do-Scw42MwvT-FO5xu3vjZC_uJ_MnSMx7Cg8pSGKMg",
        },
        {
            "item_name": "StatTrak™ AWP | 二西莫夫 (久经沙场)",
            "weapon_type": "狙击枪", "skin_name": "二西莫夫", "rarity": "保密",
            "exterior": "久经沙场", "stattrak": True,
            "base_price": 2800.0, "volatility": 0.03,
            "icon_url": None,
        },
        {
            "item_name": "StatTrak™ 沙漠之鹰 | 印花集 (崭新出厂)",
            "weapon_type": "手枪", "skin_name": "印花集", "rarity": "隐秘",
            "exterior": "崭新出厂", "stattrak": True,
            "base_price": 28000.0, "volatility": 0.05,
            "icon_url": None,
        },
    ]

    items = []
    for id_data in items_data:
        base_price = id_data.pop("base_price")
        volatility = id_data.pop("volatility", 0.022)
        item = Item(**id_data)
        db.add(item)
        items.append((item, base_price, volatility))
    db.flush()

    # --- Price snapshots (35 days) ---
    now = datetime.utcnow()
    days = 35

    for item, base_price, volatility in items:
        buff_prices = random_walk(base_price, days, volatility=volatility)
        # Simulate upward trend in last 7 days for rare/expensive items
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
            "impact_scope": "全平台", "region": "Global",
            "tags": ["weapon_update", "M4A1-S", "balance"],
        },
        {
            "event_date": now - timedelta(days=5),
            "event_type": "major_event",
            "source": "PGL",
            "title": "PGL Major 2025 上海站",
            "summary": "PGL Major 上海站正式开赛，预计持续两周。Major 期间饰品需求通常上升，贴纸相关饰品尤为明显。",
            "impact_scope": "全平台", "region": "CN",
            "tags": ["major", "PGL", "上海", "贴纸"],
        },
        {
            "event_date": now - timedelta(days=60),
            "event_type": "holiday",
            "source": "系统",
            "title": "2025 年春节",
            "summary": "春节期间国内玩家活跃度下降，但海外需求稳定。节后通常有一波补偿性需求上升。",
            "impact_scope": "国内平台", "region": "CN",
            "tags": ["春节", "节假日", "国内"],
        },
        {
            "event_date": now - timedelta(days=2),
            "event_type": "platform_promo",
            "source": "悠悠有品",
            "title": "悠悠有品春季租赁补贴活动",
            "summary": "悠悠有品推出春季租赁补贴，租赁费用最高减免 20%，活动持续至本月底。",
            "impact_scope": "悠悠有品", "region": "CN",
            "tags": ["租赁", "促销", "悠悠有品"],
        },
        {
            "event_date": now + timedelta(days=8),
            "event_type": "tournament",
            "source": "HLTV",
            "title": "ESL Pro League Season 21 决赛周",
            "summary": "ESL Pro League S21 决赛周即将开始，历史规律显示决赛周前贴纸胶囊投机需求上升。",
            "impact_scope": "全平台", "region": "Global",
            "tags": ["ESL", "Pro League", "贴纸", "HLTV"],
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
