import urllib.request, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')

def post(url, data=None):
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

def get(url):
    req = urllib.request.urlopen(url)
    return json.loads(req.read().decode())

print("--- 1. Testing Basketball Controls on 8081 ---")
# Set quarter 2
r1 = post("http://127.0.0.1:8081/api/v1/scoreboard/period/set?period=2ND")
print("Period set:", r1)

# Set shot clock to 14s
r2 = post("http://127.0.0.1:8081/api/v1/scoreboard/shot_clock/control?action=reset_14")
print("Shot clock 14:", r2)

# Adjust timer +60s
r3 = post("http://127.0.0.1:8081/api/v1/scoreboard/timer/adjust?delta=60")
print("Timer adjust:", r3)

# Add local foul
r4 = post("http://127.0.0.1:8081/api/v1/scoreboard/fouls?team=local&delta=1")
print("Fouls:", r4)

# Decrement timeout visit
r5 = post("http://127.0.0.1:8081/api/v1/scoreboard/timeouts?team=visitante&delta=-1")
print("Timeouts:", r5)

print("\n--- 2. Testing Football Goal Trigger on 8080 ---")
r_goal = post("http://127.0.0.1:8080/api/v1/scoreboard/goal/trigger", {
    "team": "local",
    "player_name": "Cavani",
    "player_number": 10,
    "minute": "34'",
    "duration": 6
})
print("Goal trigger response:", r_goal.get('status'), "Score:", r_goal.get('state', {}).get('local_score'))

print("\n>>> ALL TESTED CONTROLS RETURNED OK! <<<")
