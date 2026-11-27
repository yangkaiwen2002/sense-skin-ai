"""Explicit mock provider. Never writes observed quotes or contacts live feeds."""
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import PriceSnapshot


def mock_news():
    now = datetime.utcnow()
    topics = [
        ("示例：游戏更新后的供需观察", "这是一条用于演示的事件摘要，不是 Valve 官方公告。研究时应先确认更新内容、受影响饰品和真实成交历史，再讨论关联。"),
        ("示例：赛事期间的关注度变化", "演示场景：赛事可能带来关注度变化，但关注度不等于成交需求，也不构成价格上涨证据。"),
        ("示例：租赁活动的费用核对", "演示场景：对比租金时还需核对押金、手续费、违约规则与商品可用性。本项目暂无真实租赁报价。"),
    ]
    return [{"id": f"mock:{i}", "title": title, "summary": summary, "event_type": "demo_news",
             "event_date": (now - timedelta(days=i)).isoformat()+"Z", "fetched_at": now.isoformat()+"Z",
             "source": "Mock 场景库", "source_url": None, "data_kind": "demo", "tags": ["演示事件", "非真实公告"]}
            for i, (title, summary) in enumerate(topics)]


def refresh_mock(db, item_ids=None):
    # No new synthetic timestamp is assigned to a quote. Refresh only confirms
    # the local fixture is available; the original fixture time remains visible.
    query = db.query(func.count(PriceSnapshot.id)).filter(PriceSnapshot.price_kind == "demo")
    if item_ids is not None: query = query.filter(PriceSnapshot.item_id.in_(item_ids))
    return {"status": "success", "fetched": 0, "available": query.scalar(), "skipped": 0,
            "data_mode": "mock", "message": "已读取本地 Mock 快照；未采集真实行情，快照时间保持不变。"}
