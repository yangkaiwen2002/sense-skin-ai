"""Behavioral regressions for ingestion, quote selection and decision inputs."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Item, Platform, PriceSnapshot, RentalSnapshot
from app.models.source_news import SourceNews
from app.schema_updates import ensure_price_provenance
from app.services.market_data import summarize_snapshots, best_quote
from app.services.analytics_service import get_item_overview, get_price_history
from app.services.comparison_service import get_comparison
from app.services.scoring import score_item
from app.services.rental_service import rent_vs_buy, rental_cost
from app.schemas.rental import RentVsBuyRequest
from app.services import price_fetcher, news_ingestion


@pytest.fixture
def market():
    engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Item(id=2, item_name='AK-47 | 火蛇 (崭新出厂)', rarity='隐秘'),
                    Item(id=99, item_name='unknown'),
                    Platform(id=1, name='BUFF'), Platform(id=2, name='Steam'),
                    Platform(id=3, name='Rental', supports_rental=True)])
        db.commit()
        yield db
    engine.dispose()


def quote(db, price, platform=1, time=None, **kwargs):
    row = PriceSnapshot(item_id=2, platform_id=platform, snapshot_time=time or datetime.utcnow(),
                        listing_price=price, currency='CNY', **kwargs)
    db.add(row)
    db.flush()
    return row


def test_daily_metrics_ignore_polling_density_and_require_full_week(market):
    now = datetime.utcnow().replace(hour=23, minute=59)
    rows = [quote(market, 100, time=now-timedelta(days=7)),
            quote(market, 105, time=now-timedelta(days=1))]
    rows += [quote(market, 110, time=now-timedelta(minutes=i)) for i in range(60)]
    metrics = summarize_snapshots(rows, now)
    assert metrics['avg_7d'] == 107.5
    assert metrics['return_7d'] == 0.1
    assert metrics['observed_days_30d'] == 3
    assert summarize_snapshots(rows[2:], now)['return_7d'] is None


def test_observed_history_does_not_inherit_demo_prices(market):
    quote(market, 1, time=datetime.utcnow()-timedelta(days=7), source='seed', price_kind='demo')
    quote(market, 100, source='buff_market', price_kind='observed')
    overview = get_item_overview(market, 2).platforms[0]
    assert overview.avg_30d == 100
    assert overview.return_7d is None
    assert overview.observed_days_30d == 1
    assert len(get_price_history(market, 2, 'BUFF')) == 1


def test_latest_per_platform_then_minimum_not_old_minimum(market):
    quote(market, 1, time=datetime.utcnow()-timedelta(days=1))
    quote(market, 120)
    quote(market, 110, platform=2)
    assert best_quote(market, 2).listing_price == 110
    assert get_item_overview(market, 2).platforms[0].platform == 'Steam'
    assert get_comparison(market, 2).best_platform == 'Steam'
    assert get_price_history(market, 2, 'misspelled') == []
    quote(market, None, platform=2)
    assert best_quote(market, 2).listing_price == 120


def test_real_quote_takes_precedence_over_cheaper_demo(market):
    quote(market, 1, source='seed', price_kind='demo')
    quote(market, 110, platform=2, source='steam_market', price_kind='observed')
    assert best_quote(market, 2).platform_id == 2
    assert [p.platform for p in get_item_overview(market, 2).platforms] == ['Steam']


def test_scoring_uses_available_platform_and_preserves_zero_liquidity(market):
    quote(market, 100, platform=2, volume_24h=0, liquidity_depth=0, spread=20)
    score = score_item(market, 2)
    assert score is not None
    assert score.subscores.liquidity == 0
    assert score.subscores.trend == 50


def test_stale_quote_does_not_generate_a_buy_signal(market):
    quote(market, 100, time=datetime.utcnow()-timedelta(days=2))
    assert score_item(market, 2) is None
    assert get_item_overview(market, 2).platforms[0].is_stale


def test_rental_missing_quotes_is_not_buy_recommendation(market):
    result = rent_vs_buy(market, 2, RentVsBuyRequest())
    assert result.recommendation == 'insufficient_data'


def test_budget_and_period_loss_are_used(market):
    quote(market, 1000)
    result = rent_vs_buy(market, 2, RentVsBuyRequest(days=365, budget=500))
    assert result.recommendation == 'over_budget'
    assert result.buy_resale_loss == 40
    assert not result.buy_affordable


def test_weekly_rental_does_not_assume_fractional_billing():
    weekly_only = SimpleNamespace(daily_rental_price=None, weekly_rental_price=70)
    assert rental_cost(weekly_only, 8) == 140
    assert rental_cost(SimpleNamespace(daily_rental_price=12, weekly_rental_price=70), 8) == 82


def test_deposit_is_not_treated_as_zero(market):
    market.add(RentalSnapshot(item_id=2, platform_id=3, snapshot_time=datetime.utcnow(),
                             daily_rental_price=1, deposit_required=True, available_count=2))
    market.flush()
    result = rent_vs_buy(market, 2, RentVsBuyRequest(budget=10))
    assert result.recommendation == 'budget_unverified'
    assert result.rent_affordable is None


def test_empty_rental_stock_is_not_available(market):
    market.add(RentalSnapshot(item_id=2, platform_id=3, snapshot_time=datetime.utcnow(),
                             daily_rental_price=1, available_count=0))
    market.flush()
    assert not rent_vs_buy(market, 2, RentVsBuyRequest()).rent_available


@pytest.mark.parametrize('body', [{'days': -1}, {'days': 366}, {'budget': -1}, {'expected_resale_loss_pct': 2}])
def test_rental_api_rejects_invalid_inputs(market, body):
    app.dependency_overrides[get_db] = lambda: market
    try:
        assert TestClient(app).post('/api/items/2/rent-vs-buy', json=body).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_price_ingestion_uses_identity_not_id_and_does_not_invent_platforms(market, monkeypatch):
    names = []
    async def fetch(client, item_id, hash_name):
        names.append(hash_name)
        return {'price': 123, 'volume': 7, 'median': 120}
    async def no_sleep(seconds):
        pass
    monkeypatch.setattr(price_fetcher, '_fetch_one', fetch)
    monkeypatch.setattr(price_fetcher.asyncio, 'sleep', no_sleep)
    monkeypatch.setattr(price_fetcher.settings, 'BUFF_COOKIE', '')
    result = asyncio.run(price_fetcher.refresh_all_prices(market))
    assert names == ['AK-47 | Fire Serpent (Factory New)']
    assert result['skipped'] == 1
    row = market.query(PriceSnapshot).one()
    assert row.platform.name == 'Steam'
    assert row.price_kind == 'observed'
    assert row.buy_order_price is None and row.avg_price_24h is None


def test_buff_identity_mismatch_cannot_write_quote(market, monkeypatch):
    async def fetch(*args):
        return None
    async def no_sleep(seconds):
        pass
    monkeypatch.setattr(price_fetcher, '_fetch_one', fetch)
    monkeypatch.setattr(price_fetcher.asyncio, 'sleep', no_sleep)
    monkeypatch.setattr(price_fetcher.settings, 'BUFF_COOKIE', 'test')
    monkeypatch.setattr(price_fetcher.settings, 'BUFF_GOODS_IDS', {'AK-47 | Fire Serpent (Factory New)': 123})
    monkeypatch.setattr(price_fetcher, 'fetch_buff_goods_info', lambda _: {'ok': True, 'name': 'wrong item', 'sell_min_price': 5})
    result = asyncio.run(price_fetcher.refresh_all_prices(market))
    assert result['status'] == 'error'
    assert market.query(PriceSnapshot).count() == 0


def news_payload():
    return {'gid': '123', 'title': 'Update', 'contents': '<b>Changes</b>',
            'date': int(datetime.now(timezone.utc).timestamp())-60,
            'feedname': 'steam_community_announcements',
            'url': 'https://store.steampowered.com/news/app/730/view/123'}


def test_news_rejects_external_feed_and_unsafe_source():
    now = datetime.utcnow()
    assert news_ingestion.normalize_news(news_payload(), now)['summary'] == 'Changes'
    cdn_url = 'https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/123'
    assert news_ingestion.normalize_news({**news_payload(), 'url': cdn_url}, now)['source_url'] == cdn_url
    assert news_ingestion.normalize_news({**news_payload(), 'feedname': 'external'}, now) is None
    assert news_ingestion.normalize_news({**news_payload(), 'url': 'javascript:alert(1)'}, now) is None


def test_news_ingestion_idempotence_and_failure_preserves_data(market, monkeypatch):
    class Client:
        fail = False
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, **kwargs):
            if self.fail:
                raise httpx.ConnectError('offline')
            return httpx.Response(200, request=httpx.Request('GET', url), json={
                'appnews': {'appid': 730, 'newsitems': [news_payload(), news_payload()]}})
    monkeypatch.setattr(news_ingestion.httpx, 'AsyncClient', Client)
    assert asyncio.run(news_ingestion.refresh_news(market))['status'] == 'success'
    assert asyncio.run(news_ingestion.refresh_news(market))['status'] == 'success'
    assert market.query(SourceNews).count() == 1
    Client.fail = True
    assert asyncio.run(news_ingestion.refresh_news(market))['status'] == 'error'
    assert len(news_ingestion.get_news(market)) == 1


def test_additive_upgrade_keeps_legacy_history_and_is_repeatable():
    engine = create_engine('sqlite://')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE price_snapshots (id INTEGER PRIMARY KEY, listing_price FLOAT)'))
        conn.execute(text('INSERT INTO price_snapshots VALUES (1, 123)'))
    ensure_price_provenance(engine)
    ensure_price_provenance(engine)
    with engine.connect() as conn:
        row = conn.execute(text('SELECT listing_price, price_kind, source FROM price_snapshots')).one()
        assert tuple(row) == (123, 'legacy_unknown', 'unknown')
    engine.dispose()


def test_stale_price_cannot_win_comparison_or_rental(market):
    quote(market, 1, time=datetime.utcnow()-timedelta(days=2))
    quote(market, 100, platform=2)
    assert get_comparison(market, 2).best_platform == 'Steam'
    assert best_quote(market, 2).platform_id == 2
    assert rent_vs_buy(market, 2, RentVsBuyRequest(budget=10)).recommendation == 'over_budget'


def test_opportunity_reference_does_not_use_demo_buff_price(market):
    from app.services.opportunity_detector import _get_current_price
    quote(market, 1, price_kind='demo', source='seed')
    quote(market, 100, platform=2, price_kind='observed', source='steam_market')
    assert _get_current_price(market, 2, 1) == 100
