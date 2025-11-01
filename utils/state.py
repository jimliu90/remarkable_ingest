import json, os, threading
_LOCK = threading.Lock()
_STATE_PATH = os.path.expanduser("~/remarkable-ingest/state.json")


def _load():
    if not os.path.exists(_STATE_PATH): return {"seen": []}
    with open(_STATE_PATH, "r") as f: return json.load(f)


def _save(s):
    os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
    with open(_STATE_PATH, "w") as f: json.dump(s, f)


def seen(key: str) -> bool:
    with _LOCK:
        s = _load()
        return key in s["seen"]


def remember(key: str):
    with _LOCK:
        s = _load()
        s["seen"].append(key)
        if len(s["seen"]) > 50000:
            s["seen"] = s["seen"][-30000:]
        _save(s)

