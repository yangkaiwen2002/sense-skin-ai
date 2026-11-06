"""Durable research behavior; upstream fakes are limited to tests."""
import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.config import settings
from app.limiter import limiter
from app.models import Item, Platform, PriceSnapshot, ResearchSession, ResearchRun
from app.routers.research import router
from app.services import research_service as service, research_model, price_fetcher
from app.rag.retriever import HybridRetriever


@pytest.fixture
def research(tmp_path, monkeypatch, sample_kb_path):
    engine = create_engine(f'sqlite:///{tmp_path}/research.db', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Item(id=1, item_name='AK-47 | 红线 (久经沙场)'),
                    Item(id=2, item_name='AK-47 | 火蛇 (崭新出厂)'),
                    Platform(id=1, name='Steam')])
        db.add(PriceSnapshot(item_id=1, platform_id=1, listing_price=100, source='steam_market',
                            price_kind='observed', snapshot_time=datetime.utcnow()))
        db.commit()
    def dependency():
        with Session(engine) as db:
            yield db
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(router, prefix='/api')
    app.dependency_overrides[get_db] = dependency
    monkeypatch.setattr(limiter, 'enabled', False)
    monkeypatch.setattr(settings, 'AI_API_KEY', '')
    monkeypatch.setattr(settings, 'CLAUDE_API_KEY', '')
    monkeypatch.setattr(settings, 'AI_MODEL', '')
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    monkeypatch.setattr(service, 'get_retriever', lambda: retriever)
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def start(client, session_id=None, **overrides):
    if session_id is None:
        session_id = client.post('/api/research/sessions', json={}).json()['id']
    body = dict(request_id=str(uuid4()), question='红线流动性和租赁风险是什么？', item_ids=[1], refresh=False)
    body.update(overrides)
    return session_id, body, client.post(f'/api/research/sessions/{session_id}/runs', json=body)


def events(response):
    assert response.status_code == 200, response.text
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ') and line != 'data: [DONE]']


def test_sources_persist_reopen_export_and_idempotent_replay(research):
    client, engine = research
    sid, body, response = start(client)
    run = events(response)[-1]['run']
    assert run['status'] == 'completed' and run['answer_mode'] == 'evidence_only'
    assert '尚未调用模型' in run['answer']
    assert run['sources'][0]['data']['overview']['platforms'][0]['price_kind'] == 'observed'
    assert any(s['kind'] == 'knowledge' for s in run['sources'])
    restored = client.get(f'/api/research/sessions/{sid}').json()
    assert restored['active_run_id'] is None
    assert restored['runs'][0] == run
    assert run['parameters'] == {'mode': 'market', 'refresh': False, 'days': 7, 'budget': 1000}
    artifact = client.get(f"/api/research/runs/{run['id']}/artifact")
    assert artifact.status_code == 200 and '未调用模型' in artifact.text and '[S1]' in artifact.text
    replay = events(client.post(f'/api/research/sessions/{sid}/runs', json=body))
    assert len(replay) == 1 and replay[0]['run'] == run
    with Session(engine) as db:
        assert db.query(ResearchRun).count() == 1


def test_validation_and_active_run_conflict(research):
    client, engine = research
    sid = client.post('/api/research/sessions', json={}).json()['id']
    for data in ({'item_ids': []}, {'item_ids': [999]}, {'item_ids': [1, 2, 3, 4]}, {'question': '  '}, {'days': 0}):
        assert start(client, sid, **data)[2].status_code == 422
    with Session(engine) as db:
        db.get(ResearchSession, sid).active_run_id = str(uuid4())
        db.commit()
    assert start(client, sid)[2].status_code == 409


def test_short_followup_keeps_item_context_for_retrieval(research, monkeypatch):
    client, _ = research
    queries = []
    class Recorder:
        def search(self, query, top_k):
            queries.append(query)
            return {'results': []}
    monkeypatch.setattr(service, 'get_retriever', Recorder)
    _, _, response = start(client, question='能买吗？')
    assert events(response)[-1]['run']['status'] == 'completed'
    assert queries == ['能买吗？ AK-47 | 红线 (久经沙场)']


def test_knowledge_needs_no_item_and_tool_failure_keeps_other_evidence(research, monkeypatch):
    client, _ = research
    monkeypatch.setattr(service, 'get_news', lambda db: (_ for _ in ()).throw(RuntimeError('upstream unavailable')))
    _, _, response = start(client, item_ids=[], mode='knowledge')
    run = events(response)[-1]['run']
    assert run['status'] == 'completed'
    assert run['steps'][0]['status'] == 'error'
    assert run['sources'] and all(s['kind'] == 'knowledge' for s in run['sources'])
    assert all(s['status'] != 'running' for s in run['steps'])


def test_selected_refresh_cache_and_rental_calculation(research, monkeypatch):
    client, _ = research
    calls = []
    async def refresh(db, ids):
        calls.append(ids)
        return {'status': 'error', 'failed': len(ids)}
    async def news(db):
        return {'status': 'success'}
    monkeypatch.setattr(service, 'refresh_item_prices', refresh)
    monkeypatch.setattr(service, 'refresh_news', news)
    _, _, response = start(client, item_ids=[1, 2], refresh=True, mode='rental', days=7, budget=50)
    run = events(response)[-1]['run']
    assert calls == [[2]]  # item 1 has a five-minute observed snapshot
    assert run['steps'][0]['status'] == 'warning'
    rental = next(s for s in run['sources'] if s['kind'] == 'rental')
    assert rental['data']['buy_price'] == 100 and rental['data']['buy_affordable'] is False
    assert rental['data']['budget'] == 50


def test_model_receives_current_evidence_and_history_but_failure_is_not_report(research, monkeypatch):
    client, _ = research
    sid, _, first = start(client)
    previous = events(first)[-1]['run']
    monkeypatch.setattr(research_model, 'model_status', lambda: {'configured': True})
    calls = []
    async def model(question, sources, history):
        calls.append((question, sources, history))
        yield '价格为 100 元 [S1]。'
    monkeypatch.setattr(research_model, 'stream_answer', model)
    _, _, response = start(client, sid, question='接着核对最新来源')
    run = events(response)[-1]['run']
    assert run['answer_mode'] == 'generated' and run['status'] == 'completed'
    assert calls[0][2][-1]['content'] == previous['answer']
    assert calls[0][1][0]['id'] == 'S1'
    async def broken(*args):
        yield '尚未完成的内容'
        raise RuntimeError('secret upstream error must not be sent')
    monkeypatch.setattr(research_model, 'stream_answer', broken)
    _, _, response = start(client, sid)
    failed = events(response)[-1]['run']
    assert failed['status'] == 'failed' and failed['artifact'] is None
    assert failed['answer'] == '尚未完成的内容' and 'secret' not in response.text
    assert failed['steps'][-1]['status'] == 'failed'
    assert client.get(f'/api/research/sessions/{sid}').json()['active_run_id'] is None
    assert client.get(f"/api/research/runs/{failed['id']}/artifact").status_code == 404


def test_disconnect_persists_partial_run_and_releases_lease(research):
    _, engine = research
    sid, rid = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        db.add(ResearchSession(id=sid, title='cancel', item_ids=[1], active_run_id=rid))
        db.add(ResearchRun(id=rid, session_id=sid, request_id=str(uuid4()), question='流动性', item_ids=[1], steps=[], sources=[]))
        db.commit()
    async def disconnect():
        stream = service.execute_run(engine, rid, dict(refresh=False, mode='market', days=7, budget=100))
        async for chunk in stream:
            event = json.loads(chunk[6:])
            if event['type'] == 'sources':
                break
        await stream.aclose()
    asyncio.run(disconnect())
    with Session(engine) as db:
        run = db.get(ResearchRun, rid)
        assert run.status == 'cancelled' and run.sources
        assert run.artifact is None
        assert db.get(ResearchSession, sid).active_run_id is None


def test_abandoned_lease_recovers(research):
    client, engine = research
    sid, rid = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        db.add(ResearchSession(id=sid, title='interrupted', item_ids=[], active_run_id=rid, updated_at=datetime.utcnow()-timedelta(minutes=11)))
        db.add(ResearchRun(id=rid, session_id=sid, request_id=str(uuid4()), question='Q', item_ids=[]))
        db.commit()
    data = client.get(f'/api/research/sessions/{sid}').json()
    assert data['active_run_id'] is None and data['runs'][0]['status'] == 'interrupted'


def test_price_ingestion_scope_does_not_refresh_catalog(research, monkeypatch):
    _, engine = research
    calls = []
    async def fetch(client, item_id, name):
        calls.append(item_id)
        return dict(price=120, volume=10, median=119)
    async def no_sleep(*args):
        pass
    monkeypatch.setattr(price_fetcher, '_fetch_one', fetch)
    monkeypatch.setattr(price_fetcher.asyncio, 'sleep', no_sleep)
    monkeypatch.setattr(settings, 'BUFF_COOKIE', '')
    with Session(engine) as db:
        result = asyncio.run(price_fetcher.refresh_item_prices(db, [2]))
        assert calls == [2] and result['fetched'] == 1
        assert db.query(PriceSnapshot).filter_by(item_id=2).one().listing_price == 120
        assert db.query(PriceSnapshot).filter_by(item_id=1).count() == 1


@pytest.mark.parametrize('ending,success', [('stop', True), ('length', False), (None, False)])
def test_openai_adapter_requires_complete_stream_and_keeps_key_server_side(research, monkeypatch, ending, success):
    client, _ = research
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'openai')
    monkeypatch.setattr(settings, 'AI_API_KEY', 'test-secret')
    monkeypatch.setattr(settings, 'AI_MODEL', 'test-model')
    monkeypatch.setattr(settings, 'AI_BASE_URL', 'https://model.invalid/v1')
    status = client.get('/api/research/status')
    assert status.json()['model']['configured'] and 'test-secret' not in status.text
    def upstream(request):
        assert str(request.url) == 'https://model.invalid/v1/chat/completions'
        payload = json.loads(request.content)
        assert 'S1' in payload['messages'][-1]['content']
        chunks = [{'choices': [{'delta': {'content': '中文内容 [S1]'}, 'finish_reason': None}]}]
        if ending:
            chunks.append({'choices': [{'delta': {}, 'finish_reason': ending}]})
        body = ''.join('data: '+json.dumps(c)+'\r\n\r\n' for c in chunks)+'data: [DONE]\n\n'
        return httpx.Response(200, text=body)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(research_model.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(upstream), **kw))
    async def collect():
        return ''.join([c async for c in research_model.stream_answer('问题', [{'id': 'S1'}], [])])
    if success:
        assert asyncio.run(collect()) == '中文内容 [S1]'
    else:
        with pytest.raises(RuntimeError):
            asyncio.run(collect())


@pytest.mark.parametrize('stop_reason,success', [('end_turn', True), ('max_tokens', False)])
def test_anthropic_adapter_checks_sdk_stream_completion(research, monkeypatch, stop_reason, success):
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'anthropic')
    monkeypatch.setattr(settings, 'AI_API_KEY', 'test-secret')
    monkeypatch.setattr(settings, 'AI_MODEL', 'test-model')
    monkeypatch.setattr(settings, 'AI_BASE_URL', 'https://model.invalid')
    def upstream(request):
        assert request.url.path == '/v1/messages'
        payload = json.loads(request.content)
        assert payload['stream'] and 'S1' in payload['messages'][-1]['content']
        chunks = [
            {'type': 'message_start', 'message': {'id': 'msg_test', 'type': 'message', 'role': 'assistant',
             'model': 'test-model', 'content': [], 'stop_reason': None, 'stop_sequence': None,
             'usage': {'input_tokens': 10, 'output_tokens': 0}}},
            {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}},
            {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': '证据 [S1]'}},
            {'type': 'content_block_stop', 'index': 0},
            {'type': 'message_delta', 'delta': {'stop_reason': stop_reason, 'stop_sequence': None}, 'usage': {'output_tokens': 5}},
            {'type': 'message_stop'},
        ]
        body = ''.join('event: '+c['type']+'\ndata: '+json.dumps(c)+'\n\n' for c in chunks)
        return httpx.Response(200, headers={'content-type': 'text/event-stream'}, text=body)
    real_sdk = research_model.anthropic.AsyncAnthropic
    monkeypatch.setattr(research_model.anthropic, 'AsyncAnthropic', lambda **kw: real_sdk(
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(upstream)), **kw))
    async def collect():
        return ''.join([s async for s in research_model.stream_answer('问题', [{'id': 'S1'}], [])])
    if success:
        assert asyncio.run(collect()) == '证据 [S1]'
    else:
        with pytest.raises(RuntimeError):
            asyncio.run(collect())
