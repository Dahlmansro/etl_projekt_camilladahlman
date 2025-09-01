import os, yaml, requests

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config("config.yaml")

base_url = cfg["api"]["base_url"]
params = cfg["api"]["params"]

# Om hourly är lista i framtiden: gör om till kommaseparerad sträng
if isinstance(params.get("hourly"), list):
    params["hourly"] = ",".join(params["hourly"])

print("Kallar:", base_url)
print("Med params:", params)

r = requests.get(base_url, params=params, headers={"User-Agent": "ETL-Flow/1.0"}, timeout=15)
r.raise_for_status()
data = r.json()

# Visa lite nycklar + några första tidsstämplar om de finns
print("Nycklar:", list(data.keys())[:10])
hourly = data.get("hourly", {})
print("Antal timmar:", len(hourly.get("time", [])))
print("Första 3 tider:", hourly.get("time", [])[:3])
