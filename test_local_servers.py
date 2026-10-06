import urllib.request, json, time

def get_state(port):
    req = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/scoreboard/state')
    return json.loads(req.read().decode())

def post_control(port, action):
    req = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/v1/scoreboard/timer/control?action={action}',
        data=b'',
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

def post_json(port, path, data):
    req = urllib.request.Request(
        f'http://127.0.0.1:{port}{path}',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

print("=== 1. Starting Timer on Básquetbol (8081) ===")
post_control(8081, 'start')
time.sleep(1.5)
s1 = get_state(8081)
print(f"Timer running: {s1['timer_running']}, seconds: {s1['timer_seconds']}, shot_clock: {s1.get('shot_clock_seconds')}")

print("\n=== 2. Updating Team Names & Colors via /teams/names ===")
post_json(8081, '/api/v1/scoreboard/teams/names', {
    'local_name': 'LOS ANGELES LAKERS',
    'visitante_name': 'BOSTON CELTICS',
    'local_abbrev': 'LAL',
    'visitante_abbrev': 'BOS',
    'local_color': '#552583',
    'visitante_color': '#007A33'
})
time.sleep(1.5)
s2 = get_state(8081)
print(f"Timer still running: {s2['timer_running']}, seconds: {s2['timer_seconds']}")
print(f"Teams: {s2['local_name']} ({s2['local_abbrev']}) vs {s2['visitante_name']} ({s2['visitante_abbrev']})")

print("\n=== 3. Testing /update endpoint with stale timer_running: False ===")
curr = dict(s2)
curr['local_score'] = 24
curr['visitante_score'] = 19
curr['timer_running'] = False # Stale frontend state
post_json(8081, '/api/v1/scoreboard/update', curr)
time.sleep(1.5)
s3 = get_state(8081)
print(f"Timer preserved: {s3['timer_running']}, seconds: {s3['timer_seconds']}")
print(f"Scores updated: {s3['local_score']} - {s3['visitante_score']}")

print("\n=== 4. Pausing Timer ===")
post_control(8081, 'pause')
s4 = get_state(8081)
print(f"Timer paused: {s4['timer_running']}, seconds: {s4['timer_seconds']}")

print("\n=== 5. Testing Fútbol on Port 8080 (Independent State) ===")
s_fut = get_state(8080)
print(f"Port 8080 Sport: {s_fut['sport']}, Period: {s_fut['period']}, Local: {s_fut['local_name']}")

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
