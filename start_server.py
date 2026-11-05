#!/usr/bin/env python3
"""Démarre le serveur TeamAI API."""
import subprocess
import sys
import time

env = dict(__import__('os').environ)
env['TEAMAI_TOKENS'] = 'tok_123,dev-token'

cmd = [
    '/opt/hermes/.venv/bin/python3',
    '-m', 'engine.http',
    '--host', '0.0.0.0',
    '--port', '8081',
    '--db', 'data/teamai.db'
]

log_file = open('/opt/projects/teamai/data/server.log', 'w')

proc = subprocess.Popen(
    cmd, stdout=log_file, stderr=subprocess.STDOUT, env=env, cwd='/opt/projects/teamai'
)

print(f'Server PID: {proc.pid}')
time.sleep(2)

if proc.poll() is None:
    import urllib.request
    try:
        with urllib.request.urlopen('http://localhost:8081/health', timeout=5) as r:
            print('Health:', r.read().decode())
    except Exception as e:
        print('Error:', e)
else:
    print(f'Server exited: {proc.returncode}')

# Keep the script alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    proc.terminate()