#!/usr/bin/env python3
"""Real local-model smoke test. Requires a running Mock workspace; no cloud calls."""
import argparse
import json
from urllib.request import Request, urlopen
from uuid import uuid4

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', default='http://127.0.0.1:8000/api')
parser.add_argument('--require-generated', action='store_true', help='Also fail on explicitly degraded evidence extracts')
args = parser.parse_args()
base = args.base_url.rstrip('/')


def request(path, data=None):
    return urlopen(Request(base + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type': 'application/json'}), timeout=250)


with request('/workspace/status') as response:
    status = json.load(response)
if status['data_mode'] != 'mock' or status['model']['provider'] != 'ollama' or status['model']['health'] != 'ready':
    raise SystemExit('Start a Mock workspace with a ready local Ollama model first.')

cases = [
    ('market', [1], '请核对 AK-47 红线的各平台报价，说明这些数据能否用于交易。'),
    ('knowledge', [], '如何理解饰品流动性，应该核对哪些数据？'),
    ('rental', [1], '我想使用红线7天，预算1000元，比较租金、购买本金和押金缺口。'),
]
results = []
for mode, ids, question in cases:
    with request('/research/sessions', {'title': f'验收 · {mode}'}) as response:
        session = json.load(response)
    result = None
    with request(f'/research/sessions/{session["id"]}/runs', {
        'request_id': str(uuid4()), 'question': question, 'item_ids': ids,
        'mode': mode, 'refresh': False, 'days': 7, 'budget': 1000,
    }) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]':
                continue
            event = json.loads(line[6:])
            if event['type'] == 'completed':
                result = event['run']
    validation = ((result or {}).get('artifact') or {}).get('validation') or {}
    passed = bool(result and result['status'] == 'completed' and validation.get('validated')
                  and validation.get('tool_calls', 0) > 0)
    if args.require_generated:
        passed = passed and result['answer_mode'] == 'generated'
    results.append({'mode': mode, 'passed': passed, 'session_id': session['id'],
        'answer_mode': result.get('answer_mode') if result else None,
        'tool_calls': validation.get('tool_calls'), 'repairs': validation.get('repair_attempts'),
        'fallbacks': len(validation.get('fallbacks', [])), 'model': status['model']['model']})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
raise SystemExit(0 if all(r['passed'] for r in results) else 1)
