import anthropic
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.models.item import Item
from app.schemas.report import AIReportResponse
from app.services.analytics_service import get_item_overview
from app.services.event_service import get_event_aware_analysis
from app.services.rental_service import rent_vs_buy
from app.schemas.rental import RentVsBuyRequest
from app.models.ai_report import AIReport

SYSTEM_PROMPT = """你是一位专业的 CS2 饰品市场分析师，服务于中国 CS2 玩家社区。

你的任务是根据提供的市场数据，用简洁易懂的中文撰写一份市场分析报告。

报告应包含：
1. 短期价格趋势概述（近 7 天）
2. 价格波动是否可能由事件驱动（游戏更新、赛事/锦标赛、节假日、平台活动等）
3. 当前风险等级评估
4. 短期用户的租赁 vs 购买建议

关于赛事影响的背景知识：
- CS2 锦标赛（尤其是 Major 和 ESL/BLAST 联赛）通常在开赛前 1-2 周开始推动贴纸/纪念品相关饰品价格上涨
- 赛事数据来源为 HLTV.org，是 CS2 职业赛事最权威的信息平台
- 锦标赛结束后，贴纸胶囊开放期间往往有短暂价格波动

语言要求：
- 使用普通玩家能理解的语言，避免过于专业的金融术语
- 客观、专业，不要过于乐观或悲观
- 控制在 200-300 字以内
- 不要预测具体价格数字"""


def generate_ai_report(db: Session, item_id: int) -> AIReportResponse | None:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    overview = get_item_overview(db, item_id)
    event_analysis = get_event_aware_analysis(db, item_id)

    rent_result = None
    try:
        rent_result = rent_vs_buy(db, item_id, RentVsBuyRequest(days=7, budget=1000))
    except Exception:
        pass

    if not overview or not overview.platforms:
        return AIReportResponse(
            item_id=item_id,
            item_name=item.item_name,
            report_text="暂无足够数据生成分析报告。",
            generated_at=datetime.utcnow().isoformat(),
        )

    best_platform = overview.platforms[0]

    event_context = []
    if event_analysis.is_post_update_window:
        event_context.append("游戏更新后窗口期（近 3 天内有版本更新）")
    if event_analysis.is_major_window:
        event_context.append("Major 赛事窗口期（赛事进行中或临近）")
    if event_analysis.is_tournament_window:
        event_context.append("锦标赛窗口期（数据来源：HLTV.org，赛前投机或赛后胶囊释放阶段）")
    if event_analysis.is_holiday_window:
        event_context.append("节假日需求窗口期")
    if event_analysis.has_platform_promo:
        event_context.append("平台促销活动进行中")
    if event_analysis.is_weekend:
        event_context.append("当前为周末")
    if not event_context:
        event_context.append("当前无明显事件影响")

    return_7d_pct = (
        round(best_platform.return_7d * 100, 2)
        if best_platform.return_7d is not None
        else 0
    )

    rental_cost_7d = rent_result.rent_cost if rent_result and rent_result.rent_cost else "不可用"
    resale_loss = (
        round(best_platform.current_price * 0.04, 2)
        if best_platform.current_price
        else "不可用"
    )

    user_prompt = f"""请为以下 CS2 饰品生成市场分析报告：

饰品信息：
- 名称：{item.item_name}
- 稀有度：{item.rarity or "未知"}
- 磨损：{item.exterior or "未知"}
- StatTrak：{"是" if item.stattrak else "否"}

价格数据（{best_platform.platform} 平台）：
- 当前价格：¥{best_platform.current_price or "N/A"}
- 7日均价：¥{best_platform.avg_7d or "N/A"}
- 30日均价：¥{best_platform.avg_30d or "N/A"}
- 7日涨跌幅：{return_7d_pct}%
- 波动率：{best_platform.volatility_7d or "N/A"}
- 买卖价差：¥{best_platform.spread or "N/A"}
- 流动性评分：{best_platform.liquidity_score or "N/A"}/100
- 风险标签：{", ".join(best_platform.risk_labels) if best_platform.risk_labels else "无"}

事件背景：
{chr(10).join(f"- {e}" for e in event_context)}
- 近 7 天事件数量：{event_analysis.event_count_last_7d}

租赁数据：
- 7 天租赁总费用：{f"¥{rental_cost_7d}" if isinstance(rental_cost_7d, (int, float)) else rental_cost_7d}
- 购买后 7 天转卖预估损耗：{f"¥{resale_loss}" if isinstance(resale_loss, (int, float)) else resale_loss}"""

    try:
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            final_message = stream.get_final_message()

        report_text = next(
            (b.text for b in final_message.content if b.type == "text"),
            "生成报告失败，请稍后重试。",
        )

        ai_report = AIReport(
            item_id=item_id,
            report_type="market_summary",
            report_text=report_text,
        )
        db.add(ai_report)
        db.commit()

        return AIReportResponse(
            item_id=item_id,
            item_name=item.item_name,
            report_text=report_text,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        return AIReportResponse(
            item_id=item_id,
            item_name=item.item_name,
            report_text=f"AI 分析生成失败：{str(e)}",
            generated_at=datetime.utcnow().isoformat(),
        )
