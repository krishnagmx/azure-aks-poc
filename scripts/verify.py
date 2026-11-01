import concurrent.futures
import json
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone

base = sys.argv[1].rstrip('/')

def fetch(path, method='GET'):
    started = time.perf_counter()
    req = urllib.request.Request(base + path, method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        assert response.status == 200
    return body, (time.perf_counter() - started) * 1000

assert b'Check Backend' in fetch('/')[0]
assert len(json.loads(fetch('/api/items')[0])) == 2
for _ in range(3):
    result = json.loads(fetch('/api/storage/test', 'POST')[0])
    assert result == {'status': 'ok', 'content': 'blob storage is working'}, result
started = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(lambda _: fetch('/api/health'), range(100)))
for body, _ in results:
    assert json.loads(body)['status'] == 'ok'
latencies = sorted(latency for _, latency in results)
print(json.dumps({
    'checked_at': datetime.now(timezone.utc).isoformat(),
    'url': base,
    'page': 'passed', 'items': 'passed', 'storage_round_trips': 3,
    'health_requests': len(results), 'concurrency': 10, 'failures': 0,
    'health_latency_ms': {
        'median': round(statistics.median(latencies), 1),
        'p95': round(latencies[94], 1),
        'max': round(max(latencies), 1),
    },
    'health_requests_per_second': round(len(results) / (time.perf_counter() - started), 1),
}, indent=2))
