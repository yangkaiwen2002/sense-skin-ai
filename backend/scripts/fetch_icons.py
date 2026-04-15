"""
Fetch real icon URLs from Steam Market page and update the database.
Run once: cd backend && .venv/bin/python3 scripts/fetch_icons.py
"""
import sys, time, random, re
sys.path.insert(0, '.')

import requests
from urllib.parse import quote
from app.database import SessionLocal
from app.models.item import Item

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# Mapping of DB item_name to Steam market hash name (English, as Steam stores them)
MARKET_NAMES = {
    'AK-47 | 红线 (久经沙场)':               'AK-47 | Redline (Field-Tested)',
    'AK-47 | 火蛇 (崭新出厂)':               'AK-47 | Fire Serpent (Factory New)',
    'AK-47 | 二西莫夫 (久经沙场)':            'AK-47 | Asiimov (Field-Tested)',
    'M4A4 | 嚎叫 (久经沙场)':               'M4A4 | Howl (Field-Tested)',
    'M4A1 消音型 | 印花集 (崭新出厂)':         'M4A1-S | Printstream (Factory New)',
    'M4A4 | 龙王 (崭新出厂)':               'M4A4 | Dragon King (Factory New)',
    'FAMAS | 骸骨钥匙 (崭新出厂)':            'FAMAS | Afterimage (Factory New)',
    'SG 553 | 科伦坡 (崭新出厂)':            'SG 553 | Cyrex (Factory New)',
    'AWP | 龙狙 (久经沙场)':                'AWP | Dragon Lore (Field-Tested)',
    'AWP | 二西莫夫 (久经沙场)':              'AWP | Asiimov (Field-Tested)',
    'AWP | 超导体 (崭新出厂)':               'AWP | Superconductor (Factory New)',
    'SSG 08 | 血腥运动 (崭新出厂)':           'SSG 08 | Blood in the Water (Factory New)',
    '沙漠之鹰 | 印花集 (崭新出厂)':             'Desert Eagle | Printstream (Factory New)',
    '沙漠之鹰 | 火焰 (崭新出厂)':             'Desert Eagle | Blaze (Factory New)',
    '格洛克 18 型 | 渐变之色 (崭新出厂)':        'Glock-18 | Fade (Factory New)',
    'USP 消音版 | 杀手 (久经沙场)':           'USP-S | Kill Confirmed (Field-Tested)',
    'P250 | 邪恶大笑 (略有磨损)':             'P250 | Wicked Sick (Minimal Wear)',
    '爪子刀 | 多普勒 (崭新出厂)':              '★ Karambit | Doppler (Factory New)',
    '蝴蝶刀 | 渐变之色 (崭新出厂)':             '★ Butterfly Knife | Fade (Factory New)',
    '折叠刀 | 大马士革钢 (久经沙场)':            '★ Flip Knife | Damascus Steel (Field-Tested)',
    '穿肠刀 | 虎牙 (崭新出厂)':               '★ Gut Knife | Tiger Tooth (Factory New)',
    'M9 刺刀 | 传说 (崭新出厂)':              '★ M9 Bayonet | Lore (Factory New)',
    'MP9 | 玫瑰金 (崭新出厂)':               'MP9 | Rose Iron (Factory New)',
    'MAC-10 | 霓虹骑手 (崭新出厂)':           'MAC-10 | Neon Rider (Factory New)',
    'UMP-45 | 精英制造 (略有磨损)':            'UMP-45 | Primal Saber (Minimal Wear)',
    'XM1014 | 蓝色钛 (崭新出厂)':            'XM1014 | Blue Titanium (Factory New)',
    '运动手套 | 潘多拉之盒 (久经沙场)':           '★ Sport Gloves | Pandora\'s Box (Field-Tested)',
    '驾驶手套 | 雪豹 (久经沙场)':              '★ Driver Gloves | Snow Leopard (Field-Tested)',
    'StatTrak™ AK-47 | 红线 (久经沙场)':     'StatTrak™ AK-47 | Redline (Field-Tested)',
    'StatTrak™ AWP | 二西莫夫 (久经沙场)':    'StatTrak™ AWP | Asiimov (Field-Tested)',
    'StatTrak™ 沙漠之鹰 | 印花集 (崭新出厂)':  'StatTrak™ Desert Eagle | Printstream (Factory New)',
}


def fetch_icon_from_page(market_hash: str) -> str | None:
    """Fetch the full icon hash from the Steam Market listing page HTML."""
    url = f'https://steamcommunity.com/market/listings/730/{quote(market_hash)}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        # Extract full icon hash from fastly CDN img src
        matches = re.findall(
            r'community\.fastly\.steamstatic\.com/economy/image/([A-Za-z0-9_\-]{100,})',
            r.text
        )
        if matches:
            return matches[0]  # Return just the hash part
        return None
    except Exception as e:
        print(f'    error: {e}')
        return None


def main():
    db = SessionLocal()
    items = db.query(Item).all()
    print(f'Fetching icons for {len(items)} items...\n')

    updated = 0
    for item in items:
        market_name = MARKET_NAMES.get(item.item_name)
        if not market_name:
            print(f'  --  {item.item_name[:50]} (no market name mapping)')
            continue

        icon_hash = fetch_icon_from_page(market_name)
        if icon_hash:
            item.icon_url = icon_hash
            db.commit()
            print(f'  OK  {item.item_name[:50]}')
            updated += 1
        else:
            print(f'  ??  {item.item_name[:50]} (not found on Steam)')

        time.sleep(random.uniform(1.5, 2.5))

    db.close()
    print(f'\nDone. Updated {updated}/{len(items)} items.')


if __name__ == '__main__':
    main()
