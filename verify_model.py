import json
import urllib.request

payload = {
    'Age': 21,
    'Gender': 'Male',
    'Country': 'India',
    'Academic_Level': 'Undergraduate',
    'Most_Used_Platform': 'Instagram',
    'Purpose_Of_Use': 'Education',
    'Avg_Daily_Usage_Hours': 4.0,
    'Daily_Unlocks': 120,
    'Study_Hours': 4.5,
    'Physical_Activity_Hours': 2.2,
    'Sleep_Hours_Per_Night': 6.5,
    'Stress_Level': 'Medium',
}

req = urllib.request.Request(
    'http://127.0.0.1:2200/predict',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as resp:
    print(resp.status)
    print(resp.read().decode())
