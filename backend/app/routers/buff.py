from fastapi import APIRouter, HTTPException, Query

from data_sources.buff_client import (
    fetch_buff_sell_orders,
    fetch_buff_goods_info,
    fetch_buff_search,
)
from app.config import settings

router = APIRouter(prefix="/buff", tags=["buff"])


def _require_cookie():
    if not settings.BUFF_COOKIE:
        raise HTTPException(
            status_code=503,
            detail="BUFF_COOKIE not configured. Add it to backend/.env and restart.",
        )


@router.get("/sell-orders")
def buff_sell_orders(
    goods_id: int = Query(..., description="BUFF goods_id，e.g. 38211"),
    page_num: int = Query(1, ge=1),
    sort_by: str = Query("default"),
):
    _require_cookie()
    result = fetch_buff_sell_orders(goods_id, page_num=page_num, sort_by=sort_by)
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result.get("error"))
    return result


@router.get("/goods-info")
def buff_goods_info(goods_id: int = Query(...)):
    _require_cookie()
    result = fetch_buff_goods_info(goods_id)
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result.get("error"))
    return result


@router.get("/search")
def buff_search(q: str = Query(..., min_length=1), page_num: int = Query(1, ge=1)):
    _require_cookie()
    return fetch_buff_search(q, page_num=page_num)
