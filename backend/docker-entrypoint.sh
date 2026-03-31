#!/bin/sh
set -e

echo "[entrypoint] Patching openai/_base_client.py for httpx compatibility..."
python3 - <<'PYEOF'
import re, zipfile, os

base_client_path = '/usr/local/lib/python3.11/site-packages/openai/_base_client.py'
whl_path = '/tmp/openai_pkg/openai-1.3.0-py3-none-any.whl'

# Restore original file from whl if available, otherwise use current
if os.path.exists(whl_path):
    z = zipfile.ZipFile(whl_path)
    files = [f for f in z.namelist() if f.endswith('_base_client.py')]
    if files:
        with open(base_client_path, 'wb') as f:
            f.write(z.read(files[0]))

with open(base_client_path) as f:
    content = f.read()

lines = content.split('\n')
result = []
in_httpx = False
depth = 0
for line in lines:
    if re.search(r'self\._client = http_client or httpx\.(Async)?Client\(', line):
        in_httpx = True
        depth = line.count('(') - line.count(')')
        result.append(line)
        continue
    if in_httpx:
        depth += line.count('(') - line.count(')')
        if re.match(r'\s+proxies=proxies,', line):
            continue
        if depth <= 0:
            in_httpx = False
    result.append(line)

with open(base_client_path, 'w') as f:
    f.write('\n'.join(result))
print('openai patch applied')
PYEOF

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Starting gunicorn..."
exec gunicorn -w 1 \
  --timeout 3600 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --log-level info \
  -b 0.0.0.0:5000 \
  app.app:app
