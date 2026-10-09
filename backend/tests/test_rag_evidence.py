import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers import rag
from app.rag.retriever import HybridRetriever
from app.rag.models import KnowledgeBaseError
from app.rag.evaluation import ranking_metrics, evaluate, regression_failures
from tests.conftest import FakeSemanticEmbedder


@pytest.fixture
def api(monkeypatch, sample_kb_path):
    retriever = HybridRetriever(sample_kb_path, enable_faiss=False)
    monkeypatch.setattr(rag, 'get_retriever', lambda: retriever)
    monkeypatch.setattr(rag.settings, 'CLAUDE_API_KEY', '')
    monkeypatch.setattr(app.state.limiter, 'enabled', False)
    return TestClient(app)


def test_search_works_without_llm_and_returns_evidence(api, monkeypatch):
    monkeypatch.setattr(rag.anthropic, 'Anthropic', lambda **kw: pytest.fail('LLM must not be called'))
    response = api.post('/api/rag/search', json={'question': '流动性'})
    assert response.status_code == 200
    data = response.json()
    assert data['results'][0]['id'] == 101
    assert 'BUFF' in data['results'][0]['content']
    assert data['meta']['active_retrievers'] == ['tfidf', 'bm25']


def test_missing_key_streams_sources_and_notice_not_fake_answer(api):
    response = api.post('/api/rag/query', json={'question': '流动性'})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: {')]
    assert response.status_code == 200
    assert events[0]['type'] == 'sources'
    assert events[0]['meta']['answer_mode'] == 'retrieval_only'
    assert events[0]['sources'][0]['content']
    assert events[1]['type'] == 'notice'
    assert all(e['type'] != 'text' for e in events)
    assert response.text.endswith('data: [DONE]\n\n')


@pytest.mark.parametrize('path', ['search', 'query'])
def test_question_length_bounded(api, path):
    assert api.post(f'/api/rag/{path}', json={'question':'a' * 2001}).status_code == 422
    assert api.post(f'/api/rag/{path}', json={'question':'  '}).status_code == 400


def test_kb_failure_hides_server_path(api, monkeypatch):
    def broken(): raise KnowledgeBaseError('/private/data/secret-path')
    monkeypatch.setattr(rag, 'get_retriever', broken)
    response = api.post('/api/rag/search', json={'question':'hello'})
    assert response.status_code == 503
    assert 'secret-path' not in response.text


def test_query_time_faiss_failure_renormalizes_without_poisoning_future_queries(sample_kb_path):
    hybrid = HybridRetriever(sample_kb_path, embedder=FakeSemanticEmbedder())
    baseline = HybridRetriever(sample_kb_path, enable_faiss=False).query('流动性')
    original = hybrid._faiss._embedder.encode
    hybrid._faiss._embedder.encode = lambda _: (_ for _ in ()).throw(RuntimeError('transient'))
    failed = hybrid.search('流动性')
    assert failed['meta']['active_retrievers'] == ['tfidf', 'bm25']
    assert failed['results'][0]['fused_score'] == baseline[0]['fused_score']
    hybrid._faiss._embedder.encode = original
    assert 'faiss' in hybrid.search('流动性')['meta']['active_retrievers']


def test_ranking_metrics_known_ranks_and_duplicates():
    result = ranking_metrics([7, 7, 2, 3], [2, 3], 3)
    assert result['recall'] == 1
    assert result['mrr'] == .5
    assert 0 < result['ndcg'] < 1
    assert ranking_metrics([8], [2], 3)['hit_rate'] == 0


def test_evaluation_keeps_misses_in_denominator(sample_kb_path):
    r = HybridRetriever(sample_kb_path, enable_faiss=False)
    result = evaluate(r, [{'id':'hit','query':'流动性','language':'zh','relevant_ids':[101]},
                         {'id':'miss','query':'zzzzzz','language':'en','relevant_ids':[101]}])
    assert result['summary']['count'] == 2
    assert result['summary']['hit_rate'] == .5
    assert result['by_language']['en']['recall'] == 0


def test_regression_gate_rejects_lower_scores_and_incompatible_data():
    import copy
    baseline = {'dataset_sha256': 'a', 'corpus_sha256': 'b', 'top_k': 3,
                'modes': {'tfidf': {'summary': dict(hit_rate=1, recall=.8, mrr=.8, ndcg=.8)}}}
    result = copy.deepcopy(baseline)
    assert regression_failures(result, baseline) == []
    result['modes']['tfidf']['summary']['mrr'] = .7
    assert len(regression_failures(result, baseline)) == 1
    result['corpus_sha256'] = 'changed'
    with pytest.raises(ValueError, match='corpus_sha256'):
        regression_failures(result, baseline)


def test_configured_stream_failure_preserves_evidence_and_hides_exception(api, monkeypatch):
    monkeypatch.setattr(rag.settings, 'CLAUDE_API_KEY', 'test-key')
    def fail(**kwargs): raise RuntimeError('private-provider-details')
    monkeypatch.setattr(rag.anthropic, 'Anthropic', fail)
    response = api.post('/api/rag/query', json={'question':'流动性'})
    assert 'sources' in response.text and 'error' in response.text
    assert 'private-provider-details' not in response.text
    assert response.text.endswith('data: [DONE]\n\n')
