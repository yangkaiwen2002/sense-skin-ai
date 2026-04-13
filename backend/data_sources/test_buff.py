"""
Run from backend/ directory:
    python -m data_sources.test_buff

Or pass a goods_id:
    python -m data_sources.test_buff 38211
"""

import sys
import json
from data_sources.buff_client import (
    fetch_buff_sell_orders,
    fetch_buff_goods_info,
    fetch_buff_search,
)

GOODS_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 38211


def pp(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"Testing BUFF API — goods_id={GOODS_ID}")
    print(f"{'='*50}\n")

    # 1. goods info
    print("▶ fetch_buff_goods_info")
    info = fetch_buff_goods_info(GOODS_ID)
    pp(info)

    if not info.get("ok"):
        print("\n✗ goods_info failed — check BUFF_COOKIE in .env")
        sys.exit(1)

    # 2. sell orders (first page)
    print("\n▶ fetch_buff_sell_orders (page 1)")
    orders = fetch_buff_sell_orders(GOODS_ID, page_num=1)
    pp({**orders, "orders": orders["orders"][:3]})   # only first 3 for readability

    # 3. search
    print("\n▶ fetch_buff_search('AK-47 Redline')")
    search = fetch_buff_search("AK-47 Redline")
    pp({**search, "items": search["items"][:3]})

    print("\n✓ Done")
