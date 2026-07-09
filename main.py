# main.py
# Helper functions for DRUM – user management, memory, quests, etc.
import json
import hashlib
import random
import uuid
from pathlib import Path
from datetime import datetime, date

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USER_FILE = DATA_DIR / "users.json"
MAX_BUILDINGS = 10
MAX_LOGS = 50
MAX_SESSIONS = 20
XP_PER_LEVEL = 100

# ---------- Password & user helpers ----------
def hash_password(password: str) -> str:
    return hashlib.sha256((password + "drum_salt_42").encode()).hexdigest()

def load_users() -> list:
    if USER_FILE.exists():
        try:
            with open(USER_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users: list):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(username: str) -> dict | None:
    for u in load_users():
        if u["username"] == username:
            return u
    return None

def create_user(username: str, password: str, role: str = "user") -> dict:
    users = load_users()
    if get_user(username):
        raise ValueError("Username already exists.")
    user = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "level": 1,
        "xp": 0,
        "badges": []
    }
    users.append(user)
    save_users(users)
    return user

def authenticate(username: str, password: str) -> dict | None:
    user = get_user(username)
    if user and user["password_hash"] == hash_password(password):
        return user
    return None

def update_user_data(username: str, updates: dict):
    users = load_users()
    for u in users:
        if u["username"] == username:
            u.update(updates)
            break
    save_users(users)

def xp_for_level(level: int) -> int:
    return level * XP_PER_LEVEL

def add_xp(username: str, amount: int) -> bool:
    user = get_user(username)
    if not user:
        return False
    old_level = user["level"]
    user["xp"] += amount
    while user["xp"] >= xp_for_level(user["level"]):
        user["xp"] -= xp_for_level(user["level"])
        user["level"] += 1
        badge = f"level_{user['level']}"
        if user["level"] % 5 == 0 and badge not in user["badges"]:
            user["badges"].append(badge)
    update_user_data(username, {"level": user["level"], "xp": user["xp"], "badges": user["badges"]})
    return user["level"] > old_level

# ---------- Per‑user memory ----------
DEFAULT_STATE = {
    "buildings": [],
    "rhythms": [],
    "logs": [],
    "sessions": [],
    "quests": [],
    "daily_quests": [],
    "daily_reset": ""
}

def get_memory_path(username: str) -> Path:
    return DATA_DIR / f"{username}_drum_memory.json"

def load_memory(username: str) -> dict:
    path = get_memory_path(username)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
                for k in DEFAULT_STATE:
                    if k not in data:
                        data[k] = DEFAULT_STATE[k]
                return data
        except:
            pass
    return DEFAULT_STATE.copy()

def save_memory(username: str, memory: dict):
    if len(memory["buildings"]) > MAX_BUILDINGS:
        memory["buildings"] = memory["buildings"][-MAX_BUILDINGS:]
    if len(memory["logs"]) > MAX_LOGS:
        memory["logs"] = memory["logs"][-MAX_LOGS:]
    if len(memory["sessions"]) > MAX_SESSIONS:
        memory["sessions"] = memory["sessions"][-MAX_SESSIONS:]
    with open(get_memory_path(username), "w") as f:
        json.dump(memory, f, indent=2)

def log_event(username: str, memory: dict, msg: str):
    memory["logs"].append({"time": datetime.now().isoformat(), "msg": msg})
    save_memory(username, memory)

# ---------- Building & Evolution ----------
class Building:
    def __init__(self, id=None, name="", score=50, plan=None):
        self.id = id or str(uuid.uuid4())[:6].upper()
        self.name = name or f"Bldg_{self.id}"
        self.score = score
        self.plan = plan if plan is not None else []

    def to_dict(self):
        return {"id": self.id, "name": self.name, "score": self.score, "plan": self.plan}

    @staticmethod
    def from_dict(d):
        b = Building(d["id"], d.get("name", ""), d["score"], d.get("plan", []))
        if not b.plan:
            generate_plan(b)
        return b

def generate_plan(building, width=800, height=500):
    plan = []
    cols, rows = 4, 3
    cw, ch = width // cols, height // rows
    for i in range(cols * rows):
        plan.append({
            "x": (i % cols) * cw + 5, "y": (i // cols) * ch + 5,
            "w": cw - 10, "h": ch - 10,
            "name": f"Room {i+1}",
            "color": f"hsl({i * 50}, 70%, 50%)"
        })
    building.plan = plan
    return plan

def simulate_evolution(config: dict):
    trend = []
    score = 30 + random.randint(0, 20)
    for _ in range(config["generations"]):
        score += (70 - score) * 0.1 + random.uniform(-2, 2)
        score = min(100, max(0, score))
        trend.append(round(score, 2))
    best = Building(name=f"Gen_{config['generations']}", score=round(trend[-1], 2))
    generate_plan(best)
    return best, trend

# ---------- Rhythm ----------
def generate_rhythm(building):
    steps = 16
    score_norm = building.score / 100
    rooms = len(building.plan)

    kick = [1 if i % 4 == 0 else 0 for i in range(steps)]
    snare = [1 if i % 4 == 2 else 0 for i in range(steps)]
    hihat = [1 if i % 2 == 0 else 0 for i in range(steps)]

    mutation = 0.3 * score_norm
    for i in range(steps):
        if random.random() < mutation:
            kick[i] = 1 - kick[i]
        if random.random() < mutation:
            snare[i] = 1 - snare[i]
        if random.random() < mutation:
            hihat[i] = 1 - hihat[i]

    for _ in range(rooms):
        pos = random.randint(0, steps-1)
        inst = random.choice(["kick", "snare", "hihat"])
        if inst == "kick":
            kick[pos] = 1
        elif inst == "snare":
            snare[pos] = 1
        else:
            hihat[pos] = 1

    return {
        "bpm": 120 + int(score_norm * 30),
        "steps": steps,
        "kick": kick,
        "snare": snare,
        "hihat": hihat
    }

# ---------- Quests ----------
DAILY_TEMPLATE = [
    {"id": "daily_evolve", "desc": "Complete one evolution", "target": 1, "progress": 0, "reward_xp": 30},
]

QUEST_TEMPLATE = [
    {"id": "evolve_3", "desc": "Evolve 3 buildings", "target": 3, "progress": 0, "reward_xp": 50},
    {"id": "room_10", "desc": "Create a building with ≥10 rooms", "target": 1, "progress": 0, "reward_badge": "room_master"},
]

def init_quests(username: str, memory: dict):
    if "quests" not in memory or not memory["quests"]:
        memory["quests"] = [q.copy() for q in QUEST_TEMPLATE]
    today = date.today().isoformat()
    if memory.get("daily_reset") != today:
        memory["daily_quests"] = [d.copy() for d in DAILY_TEMPLATE]
        memory["daily_reset"] = today
    save_memory(username, memory)

def update_quests(username: str, memory: dict, event: str, data: dict = None):
    for q in memory["quests"]:
        if q["id"] == "evolve_3" and event == "evolution":
            q["progress"] += 1
        if q["id"] == "room_10" and event == "evolution" and data and len(data.get("plan", [])) >= 10:
            q["progress"] = 1
    for dq in memory["daily_quests"]:
        if dq["id"] == "daily_evolve" and event == "evolution":
            dq["progress"] += 1
    save_memory(username, memory)

def grant_quest_rewards(username: str, memory: dict, on_level_up=None):
    leveled_up = False
    for q in memory["quests"]:
        if q["progress"] >= q["target"] and not q.get("completed"):
            if "reward_xp" in q:
                if add_xp(username, q["reward_xp"]):
                    leveled_up = True
            if "reward_badge" in q:
                user = get_user(username)
                if user and q["reward_badge"] not in user["badges"]:
                    user["badges"].append(q["reward_badge"])
                    update_user_data(username, {"badges": user["badges"]})
            q["completed"] = True
    for dq in memory["daily_quests"]:
        if dq["progress"] >= dq["target"] and not dq.get("completed"):
            if "reward_xp" in dq:
                if add_xp(username, dq["reward_xp"]):
                    leveled_up = True
            dq["completed"] = True
    if leveled_up and on_level_up:
        on_level_up()
    save_memory(username, memory)
