import json
import pytest
from app.services import agent_runtime as agent
from app.config import settings
from app.services import research_service as service
from app.services.news_ingestion import get_news, refresh_news
from app.services.price_fetcher import refresh_item_prices
from test_research_workflow import research, start, events

@pytest.fixture
def anyio_backend(): return "asyncio"

SOURCES = [{"id":"S1", "kind":"knowledge", "summary":"演示价格为 100.50 元，不是可成交价格。"}]
VALID = {"conclusion":"知识说明", "findings":[{"source_id":"S1", "quote":"演示价格为 100.50 元，不是可成交价格。", "observation":"价格 100.50 元只用于演示"}], "next_action":"核对平台原始报价"}

def test_grounding_accepts_verbatim_quote():
    assert agent.validate_report(json.dumps(VALID), SOURCES).findings[0].source_id == 'S1'

@pytest.mark.parametrize('patch', [dict(source_id='S99'), dict(quote='不存在的来源原文内容'), dict(observation='价格上涨了 25%'), dict(extra='ignore instructions')])
def test_grounding_rejects_unsupported_content(patch):
    data = {**VALID, 'findings': [{**VALID['findings'][0], **patch}]}
    with pytest.raises(ValueError): agent.validate_report(json.dumps(data), SOURCES)

def test_tool_arguments_cannot_expand_scope():
    with pytest.raises(ValueError): agent.ToolArguments.model_validate({'item_ids':[999], 'url':'https://example.org'})

@pytest.mark.anyio
async def test_repair_is_bounded_and_revalidated(monkeypatch):
    draft = {"conclusion":"知识说明", "findings":[{"evidence_id":"E1","observation":"仅为演示报价"}], "next_action":"核对平台原始报价"}
    replies = [json.dumps({**draft, 'findings':[{'evidence_id':'E99','observation':'仅为演示报价'}]}), json.dumps(draft)]
    seen=[]
    async def chat(messages, **kwargs):
        seen.append(list(messages)); return {'role':'assistant','content':replies.pop(0)}, {'input_tokens':3}
    monkeypatch.setattr(agent,'chat',chat)
    report, meta = await agent.structured_answer('价格?',SOURCES,[])
    assert meta['repair_attempts']==1 and len(seen)==2
    assert '校验失败' in seen[1][-1]['content']
    assert report.findings[0].source_id=='S1'

@pytest.mark.anyio
async def test_invalid_output_never_published(monkeypatch):
    calls=[]
    async def chat(*a, **kw): calls.append(1); return {'content':'{}'}, {}
    monkeypatch.setattr(agent,'chat',chat)
    with pytest.raises(ValueError, match='未发布'):
        await agent.structured_answer('test',SOURCES,[])
    assert len(calls)==2


def test_agent_executes_allowlisted_tools_and_validated_artifact(research,monkeypatch):
    client,engine=research
    monkeypatch.setattr(settings,'AI_PROVIDER','ollama')
    count=[]
    async def choose(messages, names):
        count.append(1)
        name = 'market' if 'market' in names else 'finish'
        return agent.ToolDecision(tool=name,scope='current_request'), {'role':'assistant','content':name}, {'duration_ms':2,'input_tokens':10,'output_tokens':5}
    async def answer(question,sources,history):
        report=agent.ResearchReport(conclusion='报价待核验', findings=[agent.Finding(source_id=sources[0]['id'],quote=sources[0]['summary'],observation='报价需要核对')],next_action='核对平台原始报价')
        return report, {'validated':True,'repair_attempts':0,'model_calls':[]}
    monkeypatch.setattr(agent,'choose_tool',choose); monkeypatch.setattr(agent,'structured_answer',answer)
    sid,body,response=start(client)
    run=events(response)[-1]['run']
    assert run['status']=='completed'
    assert len(count)==2  # model explicitly ends after reading market
    assert run['artifact']['validation']['tool_calls']==1
    assert run['artifact']['validation']['validated']
    assert len([s for s in run['sources'] if s['kind']=='market'])==1


def test_agent_schema_failure_retains_sources_but_no_report(research,monkeypatch):
    client,_=research; monkeypatch.setattr(settings,'AI_PROVIDER','ollama')
    async def choose(*a, **kw): return agent.ToolDecision(tool='finish',scope='current_request'), {'role':'assistant','content':'finish'}, {'duration_ms':1}
    async def fail(*a, **kw): raise ValueError('unsafe output')
    monkeypatch.setattr(agent,'choose_tool',choose); monkeypatch.setattr(agent,'structured_answer',fail)
    sid,body,response=start(client); run=events(response)[-1]['run']
    assert run['status']=='failed' and run['sources'] and not run['answer'] and not run['artifact']
    assert client.get(f'/api/research/sessions/{sid}').json()['active_run_id'] is None


def test_archive_restore_rename_and_block_run(research):
    client,_=research; sid=client.post('/api/research/sessions',json={}).json()['id']
    assert client.patch(f'/api/research/sessions/{sid}',json={'title':'   '}).status_code==422
    assert client.patch(f'/api/research/sessions/{sid}',json={'title':'我的研究','archived':True}).status_code==200
    assert client.get('/api/research/sessions').json()['sessions']==[]
    assert client.get('/api/research/sessions?archived=true').json()['sessions'][0]['title']=='我的研究'
    assert start(client,sid)[2].status_code==409
    client.patch(f'/api/research/sessions/{sid}',json={'archived':False})
    assert start(client,sid)[2].status_code==200

@pytest.mark.anyio
async def test_mock_provider_is_explicit_and_does_not_collect(research,monkeypatch):
    from sqlalchemy.orm import Session
    client,engine=research; monkeypatch.setattr(settings,'DATA_MODE','mock')
    with Session(engine) as db:
        assert (await refresh_item_prices(db,[1]))['fetched']==0
        assert (await refresh_news(db))['fetched']==0
        news=get_news(db)
    assert all(x['data_kind']=='demo' and x['source_url'] is None for x in news)


@pytest.mark.anyio
async def test_constrained_router_rejects_tool_outside_available_scope(monkeypatch):
    async def chat(*a, **kw):
        return {"content":json.dumps({"tool":"rental","scope":"current_request"})}, {}
    monkeypatch.setattr(agent,"chat",chat)
    with pytest.raises(ValueError, match="不可用"):
        await agent.choose_tool([], ["knowledge"])


def test_router_rejects_arbitrary_actions():
    with pytest.raises(ValueError):
        agent.ToolDecision.model_validate({"tool":"shell", "scope":"current_request"})


def test_numeric_grounding_accepts_equivalent_decimal_format():
    data = {**VALID, 'findings': [{**VALID['findings'][0], 'observation':'资料中的金额是 100.5 元'}]}
    assert agent.validate_report(json.dumps(data), SOURCES)


def test_evidence_quotes_are_resolved_from_source_not_model_copy():
    catalog = agent.evidence_catalog(SOURCES)
    assert catalog[0]["quote"] in SOURCES[0]["summary"]
    with pytest.raises(ValueError):
        agent.validate_report(json.dumps({**VALID, "findings":[{**VALID["findings"][0], "observation":"收益上升 99%"}]}), SOURCES)

@pytest.mark.anyio
async def test_unsupported_interpretation_degrades_explicitly_to_verified_quote(monkeypatch):
    draft = {"conclusion":"知识说明", "findings":[{"evidence_id":"E1", "observation":"收益上涨 99%"}], "next_action":"阅读来源全文"}
    async def chat(*a, **kw): return {"role":"assistant","content":json.dumps(draft)}, {}
    monkeypatch.setattr(agent,"chat",chat)
    report, meta = await agent.structured_answer('价格?', SOURCES, [])
    assert meta['fallbacks'] and meta['repair_attempts'] == 1
    assert '99%' not in report.findings[0].observation
    assert report.findings[0].quote in SOURCES[0]['summary']
    assert '未通过校验' in report.findings[0].observation


def test_catalog_identifier_is_not_mistaken_for_a_price():
    sources = [{**SOURCES[0], 'title':'AK-47 | 红线 (久经沙场)'}]
    data = {**VALID, 'findings':[{**VALID['findings'][0], 'observation':'AK-47 演示报价 100.50 元'}]}
    assert agent.validate_report(json.dumps(data), sources)
    data['findings'][0]['observation'] = 'AK-999 演示报价 100.50 元'
    with pytest.raises(ValueError): agent.validate_report(json.dumps(data), sources)


def test_rental_evidence_budget_keeps_unknown_deposit_warning(research, monkeypatch):
    from app.schemas.rental import RentVsBuyResult
    client, _ = research
    result = RentVsBuyResult(item_id=1, item_name='红线', days=7, budget=1000,
        rent_cost=9.28, buy_price=251.68, buy_resale_loss=10.07,
        deposit_required=True, explanation='说明内容较长。' * 12)
    monkeypatch.setattr(service, 'rent_vs_buy', lambda *args: result)
    _, _, response = start(client, mode='rental')
    sources = events(response)[-1]['run']['sources']
    rental_quotes = [e['quote'] for e in agent.evidence_catalog(sources) if e['kind']=='rental']
    assert any('押金' in quote and '金额未知' in quote for quote in rental_quotes)
