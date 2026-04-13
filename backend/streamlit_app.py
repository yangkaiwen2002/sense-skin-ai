"""
Standalone Streamlit demo for BUFF sell-order data.

Run from backend/ directory:
    streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
from data_sources.buff_client import (
    fetch_buff_sell_orders,
    fetch_buff_goods_info,
    fetch_buff_search,
)

st.set_page_config(page_title="BUFF 卖单分析", page_icon="🔪", layout="wide")

st.title("🔪 BUFF 卖单分析")
st.caption("数据来源：BUFF.163.com  ·  需要在 `.env` 中配置 `BUFF_COOKIE`")

# ── 搜索 ──────────────────────────────────────────────────────────────────
st.subheader("搜索饰品")
col_search, col_btn = st.columns([4, 1])
with col_search:
    keyword = st.text_input("输入饰品英文名（如 AK-47 Redline）", label_visibility="collapsed",
                            placeholder="AK-47 Redline")
with col_btn:
    do_search = st.button("搜索", use_container_width=True)

goods_id = None
if do_search and keyword:
    with st.spinner("搜索中..."):
        res = fetch_buff_search(keyword)
    if res["ok"] and res["items"]:
        df_search = pd.DataFrame(res["items"])
        df_search.columns = ["goods_id", "英文名", "中文名", "最低卖价", "在售数量"]
        st.dataframe(df_search, use_container_width=True)

        selected = st.selectbox(
            "选择饰品",
            options=res["items"],
            format_func=lambda x: f"{x['name_zh'] or x['name']}  ¥{x['sell_min_price']}",
        )
        if selected:
            goods_id = selected["goods_id"]
    else:
        st.warning("未找到结果，或 BUFF_COOKIE 失效")

# ── 直接输入 goods_id ────────────────────────────────────────────────────
st.divider()
st.subheader("直接输入 goods_id")
col_id, col_page, col_sort, col_fetch = st.columns([2, 1, 2, 1])
with col_id:
    manual_id = st.number_input("goods_id", value=goods_id or 38211, step=1,
                                 label_visibility="collapsed")
with col_page:
    page_num = st.number_input("页码", value=1, min_value=1, step=1)
with col_sort:
    sort_by = st.selectbox("排序", ["default", "price.asc", "price.desc",
                                    "paintwear.asc", "paintwear.desc"],
                            label_visibility="collapsed")
with col_fetch:
    do_fetch = st.button("拉取卖单", use_container_width=True, type="primary")

if do_fetch:
    gid = int(manual_id)

    # goods info
    with st.spinner("获取商品信息..."):
        info = fetch_buff_goods_info(gid)

    if not info.get("ok"):
        st.error(f"请求失败：{info.get('error')}  —  请检查 .env 中的 BUFF_COOKIE")
        st.stop()

    st.markdown(f"### {info.get('name_zh') or info.get('name', '—')}")
    m1, m2, m3 = st.columns(3)
    m1.metric("最低卖价",  f"¥ {info['sell_min_price']}" if info["sell_min_price"] else "—")
    m2.metric("最高求购",  f"¥ {info['buy_max_price']}"  if info["buy_max_price"]  else "—")
    m3.metric("在售数量",   info.get("sell_num", "—"))

    # sell orders
    with st.spinner(f"拉取第 {page_num} 页卖单..."):
        orders_res = fetch_buff_sell_orders(gid, page_num=page_num, sort_by=sort_by)

    if not orders_res.get("ok"):
        st.error(f"卖单请求失败：{orders_res.get('error')}")
        st.stop()

    orders = orders_res["orders"]
    st.caption(f"共 {orders_res['total']} 条卖单  ·  本页 {len(orders)} 条")

    if orders:
        df = pd.DataFrame(orders)
        df.rename(columns={
            "price": "价格 (¥)",
            "sell_num": "数量",
            "paintwear": "磨损值",
            "paintseed": "图案模板",
            "stickers": "贴纸",
            "tradable_cooldown_text": "交易冷却",
        }, inplace=True)
        df["贴纸"] = df["贴纸"].apply(lambda x: ", ".join(x) if x else "—")
        df["交易冷却"] = df["交易冷却"].fillna("可交易")

        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "价格 (¥)": st.column_config.NumberColumn(format="¥%.2f"),
                "磨损值":   st.column_config.NumberColumn(format="%.6f"),
            },
        )

        # price distribution
        prices = [o["price"] for o in orders]
        st.subheader("价格分布")
        st.bar_chart(pd.Series(prices).value_counts().sort_index())
    else:
        st.info("该页无卖单数据")
