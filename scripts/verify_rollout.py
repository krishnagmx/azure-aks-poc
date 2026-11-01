import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

base = sys.argv[1].rstrip('/')
subprocess.run(['kubectl', 'rollout', 'restart', 'deployment/app', '-n', 'poc-app'], check=True, stdout=subprocess.DEVNULL)
rollout = subprocess.Popen(['kubectl', 'rollout', 'status', 'deployment/app', '-n', 'poc-app', '--timeout=180s'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
checks, failures = 0, []
started = time.monotonic()
while rollout.poll() is None or time.monotonic() - started < 20:
    checks += 1
    try:
        with urllib.request.urlopen(base + '/api/health', timeout=10) as response:
            assert json.load(response)['status'] == 'ok'
    except Exception as error:
        failures.append(str(error))
    time.sleep(0.2)
    if time.monotonic() - started > 210:
        raise RuntimeError('Rollout exceeded test window')
output = rollout.communicate()[0]
print(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'health_checks_during_rollout': checks, 'failures': failures, 'rollout_status': output.strip()}, indent=2))
assert rollout.returncode == 0 and not failures
