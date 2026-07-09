# streamlit_app.py
# =============================
# DRUM – Design & Rhythm Utility Machine
# Game‑style UI + interactive engineering analysis
# =============================

import streamlit as st
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
import uuid
import random

# ---------- Engineering module ----------
from engineering import (
    calculate_total_area,
    compute_floor_loads,
    check_structural_integrity,
    estimate_cost,
    calculate_energy_score,
    DEFAULT_COSTS,
)

# ---------- Page config (hide default Streamlit menu) ----------
st.set_page_config(
    page_title="DRUM Studio",
    page_icon="🥁",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    }
)

# ---------- File paths ----------
USER_FILE = Path("users.json")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------- Game constants ----------
XP_PER_LEVEL = 100

def xp_for_level(level):
    return level * XP_PER_LEVEL

# =============================
# PASSWORD & USER HELPERS
# =============================
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
    users = load_users()
    for u in users:
        if u["username"] == username:
            return u
    return None

def create_user(username: str, password: str, role: str = "user") -> dict:
    users = load_users()
    if get_user(username) is not None:
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

def add_xp(username: str, amount: int):
    user = get_user(username)
    if not user:
        return
    old_level = user["level"]
    user["xp"] += amount
    while user["xp"] >= xp_for_level(user["level"]):
        user["xp"] -= xp_for_level(user["level"])
        user["level"] += 1
        if user["level"] % 5 == 0 and f"level_{user['level']}" not in user["badges"]:
            user["badges"].append(f"level_{user['level']}")
    update_user_data(username, {"level": user["level"], "xp": user["xp"], "badges": user["badges"]})
    if user["level"] > old_level:
        st.balloons()

# ---------- Per‑user memory helpers ----------
def get_memory_path(username: str) -> Path:
    return DATA_DIR / f"{username}_drum_memory.json"

def load_memory(username: str) -> dict:
    path = get_memory_path(username)
    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for k in DEFAULT_STATE:
                    if k not in data:
                        data[k] = DEFAULT_STATE[k]
                return data
        except:
            pass
    return DEFAULT_STATE.copy()

def save_memory(username: str):
    mem = st.session_state.memory
    if len(mem["buildings"]) > MAX_BUILDINGS:
        mem["buildings"] = mem["buildings"][-MAX_BUILDINGS:]
    if len(mem["logs"]) > MAX_LOGS:
        mem["logs"] = mem["logs"][-MAX_LOGS:]
    if len(mem["sessions"]) > MAX_SESSIONS:
        mem["sessions"] = mem["sessions"][-MAX_SESSIONS:]
    with open(get_memory_path(username), "w") as f:
        json.dump(mem, f, indent=2)

def log_event(username: str, msg: str):
    st.session_state.memory["logs"].append({"time": datetime.now().isoformat(), "msg": msg})
    save_memory(username)

# =============================
# DOMAIN LOGIC (unchanged)
# =============================
DEFAULT_STATE = {
    "buildings": [],
    "rhythms": [],
    "logs": [],
    "sessions": []
}
MAX_BUILDINGS = 10
MAX_LOGS = 50
MAX_SESSIONS = 20

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
            generate_building_plan(b)
        return b

def generate_building_plan(building, width=800, height=500):
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

def render_svg_plan(plan, width=800, height=500):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0f172a;">'
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{item["name"]}</text>'
    svg += '</svg>'
    return svg

def simulate_design_evolution(config):
    trend = []
    score = 30 + random.randint(0, 20)
    for _ in range(config["generations"]):
        score += (70 - score) * 0.1 + random.uniform(-2, 2)
        score = min(100, max(0, score))
        trend.append(round(score, 2))
    best = Building(name=f"Gen_{config['generations']}", score=round(trend[-1], 2))
    return best, trend

# =============================
# GAME UI HELPERS (unchanged)
# =============================
def show_xp_bar(user):
    level = user["level"]
    xp = user["xp"]
    needed = xp_for_level(level)
    progress = xp / needed if needed > 0 else 1.0
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-family: 'Press Start 2P', monospace; font-size: 14px; color: #a78bfa;">LVL {level}</span>
        <div style="flex: 1; height: 10px; background: #1e293b; border-radius: 5px; overflow: hidden;">
            <div style="width: {progress*100}%; height: 100%; background: linear-gradient(90deg, #f59e0b, #fbbf24); border-radius: 5px; box-shadow: 0 0 8px #fbbf24;"></div>
        </div>
        <span style="font-family: 'Press Start 2P', monospace; font-size: 10px; color: #cbd5e1;">{xp}/{needed} XP</span>
    </div>
    """, unsafe_allow_html=True)

def show_building(building, label):
    st.subheader(f"🏗️ {label} — {building.name}")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">SCORE</div>
        <div style="font-size: 28px; font-weight: bold; color: #fbbf24;">{building.score}</div>
    </div>
    """, unsafe_allow_html=True)
    col2.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">ID</div>
        <div style="font-size: 24px; color: #f8fafc;">{building.id}</div>
    </div>
    """, unsafe_allow_html=True)
    col3.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">ROOMS</div>
        <div style="font-size: 28px; font-weight: bold; color: #f8fafc;">{len(building.plan)}</div>
    </div>
    """, unsafe_allow_html=True)

    if building.plan:
        svg = render_svg_plan(building.plan)
        st.markdown(
            f'<div style="background:#0f172a; border-radius:12px; padding:8px; border: 1px solid #334155;">{svg}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No plan available.")

# =============================
# SESSION INITIALIZATION
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.memory = DEFAULT_STATE.copy()
    st.session_state.active_building = None
    st.session_state.config = {"generations": 5, "style": "minimal"}
    # Engineering parameter defaults (will be used in Engineering Lab)
    st.session_state.eng_params = {
        "live_load": 2.5,
        "slab_thickness": 0.2,
        "additional_dead": 1.0,
        "concrete_cost": 250,
        "steel_cost": 50,
        "glass_cost": 150,
        "labor_cost": 100,
        "glazing_ratio": 0.2,
        "orientation": "south",
    }

# =============================
# CUSTOM CSS (hides Streamlit default menu & footer)
# =============================
GAME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* Hide Streamlit header/footer */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Press Start 2P', monospace;
    background: #0b0f19;
    color: #e2e8f0;
}
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
    z-index: -1;
}
@keyframes move-twink-back {
    from {background-position:0 0;}
    to {background-position:-10000px 5000px;}
}
.stApp::after {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: transparent url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Ccircle cx='10' cy='20' r='1.5' fill='%23fff' opacity='0.6'/%3E%3Ccircle cx='50' cy='80' r='1' fill='%23fff' opacity='0.4'/%3E%3Ccircle cx='90' cy='40' r='0.8' fill='%23fff' opacity='0.7'/%3E%3Ccircle cx='130' cy='120' r='1.2' fill='%23fff' opacity='0.5'/%3E%3Ccircle cx='170' cy='160' r='0.6' fill='%23fff' opacity='0.8'/%3E%3C/svg%3E") repeat;
    animation: move-twink-back 200s linear infinite;
    z-index: -1;
    opacity: 0.3;
}
h1, h2, h3 {
    color: #f1f5f9;
    text-shadow: 0 0 10px rgba(99,102,241,0.5);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(12,18,30,0.95));
    backdrop-filter: blur(20px);
    border-right: 1px solid #4338ca;
}
.stButton > button {
    font-family: 'Press Start 2P', monospace;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.8rem;
    font-weight: 600;
    text-transform: uppercase;
    box-shadow: 0 0 12px rgba(99,102,241,0.6);
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(139,92,246,0.9);
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
}
.stButton > button:active {
    transform: scale(0.98);
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem;
    font-family: 'Press Start 2P', monospace;
}
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: #1e293b;
    color: #f8fafc;
    border: 2px solid #4338ca;
    border-radius: 8px;
    padding: 8px;
}
.stSelectbox > div > div > select {
    background: #1e293b;
    color: #f8fafc;
}
div.stMarkdown p {
    font-family: 'Press Start 2P', monospace;
}
</style>
"""
st.markdown(GAME_CSS, unsafe_allow_html=True)

# =============================
# LOGIN / REGISTER PAGE
# =============================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🥁 DRUM</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-family: \"Press Start 2P\"; color: #a78bfa;'>Login or create your architect identity</p>", unsafe_allow_html=True)
        with st.form("auth_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            action = st.form_submit_button("Login")
            register_action = st.form_submit_button("Register")

            if action:
                user = authenticate(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_data = user
                    st.session_state.memory = load_memory(username)
                    mem = st.session_state.memory
                    if mem["sessions"]:
                        last = mem["sessions"][-1]
                        bid = last.get("building_id")
                        match = next((b for b in mem["buildings"] if b.get("id") == bid), None)
                        if match:
                            st.session_state.active_building = Building.from_dict(match)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

            if register_action:
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    try:
                        create_user(username, password)
                        st.success("Account created! You can now log in.")
                    except ValueError as e:
                        st.error(str(e))

        users = load_users()
        if not users:
            create_user("admin", "admin123", role="admin")
            st.info("Default admin account created: admin / admin123")

    st.stop()

# =============================
# LOGGED IN – MAIN APP
# =============================
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 15px;">
        <div style="font-size: 18px; color: #fbbf24;">👤 {username}</div>
        <div style="font-size: 12px; color: #94a3b8;">{user_data.get('role', 'user').upper()}</div>
    </div>
    """, unsafe_allow_html=True)
    show_xp_bar(user_data)
    st.markdown("---")
    page = st.radio("Navigate", ["Command Center", "Evolution Chamber", "Engineering Lab", "Archives"])

    if user_data.get("role") == "admin":
        admin_page = st.radio("Admin", ["User Management"], key="admin_nav")

    st.markdown("---")
    with st.expander("⚙️ Game Settings"):
        st.session_state.config["generations"] = st.slider("Generations", 2, 20, st.session_state.config["generations"])
        st.session_state.config["style"] = st.selectbox("Style", ["minimal", "bold", "organic"])

    if st.button("🚪 Logout"):
        save_memory(username)
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_data = None
        st.session_state.memory = DEFAULT_STATE.copy()
        st.session_state.active_building = None
        st.rerun()

# ---------- Admin Panel ----------
if user_data.get("role") == "admin" and "admin_nav" in st.session_state and st.session_state.admin_nav == "User Management":
    st.title("🛡️ Admin Panel – User Management")
    users = load_users()
    st.write("Registered users:")
    for u in users:
        cols = st.columns([3,1,1])
        cols[0].write(f"**{u['username']}**  (Role: {u['role']}, Lvl {u['level']})")
        if u["username"] != username:
            if cols[1].button("🗑️ Delete", key=f"del_{u['username']}"):
                users.remove(u)
                save_users(users)
                st.rerun()
            if cols[2].button("⭐ Make Admin", key=f"adm_{u['username']}") and u["role"] != "admin":
                u["role"] = "admin"
                save_users(users)
                st.rerun()
        else:
            cols[1].write("(you)")
    st.stop()

# ---------- Main pages ----------
if page == "Command Center":
    st.title("📊 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">BUILDINGS</div>
        <div style="font-size: 28px; font-weight: bold; color: #fbbf24;">{len(mem['buildings'])}</div>
    </div>
    """, unsafe_allow_html=True)
    col2.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">SESSIONS</div>
        <div style="font-size: 28px; font-weight: bold; color: #fbbf24;">{len(mem['sessions'])}</div>
    </div>
    """, unsafe_allow_html=True)
    col3.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #6366f1;">
        <div style="font-family: 'Press Start 2P', monospace; font-size: 12px; color: #c7d2fe;">BADGES</div>
        <div style="font-size: 24px; font-weight: bold; color: #fbbf24;">{'🏅' * len(user_data.get('badges', []))}</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📜 Recent Logs")
    for log in reversed(mem["logs"][-5:]):
        st.caption(f"`{log['time'][11:19]}` – {log['msg']}")

elif page == "Evolution Chamber":
    st.title("🧬 Evolution Chamber")
    col_btn, col_demo = st.columns([2,1])
    with col_btn:
        if st.button("🚀 EVOLVE!", type="primary"):
            with st.spinner("Mixing genes..."):
                best, trend = simulate_design_evolution(st.session_state.config)
                generate_building_plan(best)
                mem["buildings"].append(best.to_dict())
                mem["sessions"].append({
                    "id": str(uuid.uuid4())[:6],
                    "building_id": best.id,
                    "time": datetime.now().isoformat()
                })
                st.session_state.active_building = best
                log_event(username, f"New design: {best.name}")
                save_memory(username)
                add_xp(username, int(best.score * 2))
                st.session_state.user_data = get_user(username)
            st.line_chart(trend)

    with col_demo:
        if st.button("📦 Load Demo"):
            demo = Building(name="Demo", score=85)
            generate_building_plan(demo)
            st.session_state.active_building = demo
            log_event(username, "Loaded demo building")
            save_memory(username)

    if st.session_state.active_building:
        show_building(st.session_state.active_building, "Active")
    else:
        st.info("Press EVOLVE! or load a demo to create a building.")

elif page == "Engineering Lab":
    st.title("🔧 Engineering Lab – Interactive Design Check")

    if st.session_state.active_building is None:
        st.warning("No active building. Go to Evolution Chamber and create one.")
    else:
        building = st.session_state.active_building
        plan = building.plan
        show_building(building, "Current Design")

        st.markdown("---")

        # ---------- INPUT PARAMETERS (collapsible) ----------
        with st.expander("⚙️ Load & Structural Assumptions", expanded=False):
            colL1, colL2, colL3 = st.columns(3)
            with colL1:
                live_load = st.number_input("Live Load (kN/m²)", min_value=1.0, max_value=10.0,
                                           value=st.session_state.eng_params["live_load"], step=0.5)
                st.session_state.eng_params["live_load"] = live_load
            with colL2:
                slab_t = st.number_input("Slab Thickness (m)", min_value=0.1, max_value=0.5,
                                         value=st.session_state.eng_params["slab_thickness"], step=0.05)
                st.session_state.eng_params["slab_thickness"] = slab_t
            with colL3:
                add_dead = st.number_input("Additional Dead Load (kN/m²)", min_value=0.0, max_value=5.0,
                                          value=st.session_state.eng_params["additional_dead"], step=0.1)
                st.session_state.eng_params["additional_dead"] = add_dead

        with st.expander("💰 Cost Rates", expanded=False):
            colC1, colC2, colC3, colC4 = st.columns(4)
            with colC1:
                conc_cost = st.number_input("Concrete ($/m²)", min_value=50, max_value=500,
                                           value=st.session_state.eng_params["concrete_cost"], step=10)
                st.session_state.eng_params["concrete_cost"] = conc_cost
            with colC2:
                steel_cost = st.number_input("Steel ($/m)", min_value=10, max_value=200,
                                            value=st.session_state.eng_params["steel_cost"], step=5)
                st.session_state.eng_params["steel_cost"] = steel_cost
            with colC3:
                glass_cost = st.number_input("Glass ($/m²)", min_value=50, max_value=400,
                                            value=st.session_state.eng_params["glass_cost"], step=10)
                st.session_state.eng_params["glass_cost"] = glass_cost
            with colC4:
                labor_cost = st.number_input("Labor ($/m²)", min_value=20, max_value=300,
                                            value=st.session_state.eng_params["labor_cost"], step=10)
                st.session_state.eng_params["labor_cost"] = labor_cost

        with st.expander("⚡ Energy Parameters", expanded=False):
            colE1, colE2 = st.columns(2)
            with colE1:
                glazing = st.slider("Glazing Ratio", 0.05, 0.80,
                                    st.session_state.eng_params["glazing_ratio"], 0.01)
                st.session_state.eng_params["glazing_ratio"] = glazing
            with colE2:
                orient = st.selectbox("Orientation", ["north", "south", "east", "west"],
                                      index=["north","south","east","west"].index(
                                          st.session_state.eng_params["orientation"]))
                st.session_state.eng_params["orientation"] = orient

        st.markdown("---")

        # ---------- COMPUTE RESULTS using current parameters ----------
        total_area = calculate_total_area(plan)
        total_load = compute_floor_loads(
            plan,
            live_load_kN_per_m2=st.session_state.eng_params["live_load"],
            slab_thickness_m=st.session_state.eng_params["slab_thickness"],
            additional_dead_load_kN_per_m2=st.session_state.eng_params["additional_dead"]
        )
        integrity = check_structural_integrity(plan)
        costs = estimate_cost(plan, costs={
            "concrete_per_m2": st.session_state.eng_params["concrete_cost"],
            "steel_per_m": st.session_state.eng_params["steel_cost"],
            "glass_per_m2": st.session_state.eng_params["glass_cost"],
            "labor_per_m2": st.session_state.eng_params["labor_cost"],
        })
        energy = calculate_energy_score(
            plan,
            orientation=st.session_state.eng_params["orientation"],
            glazing_ratio=st.session_state.eng_params["glazing_ratio"]
        )

        # ---------- DISPLAY OUTPUT ----------
        st.subheader("📐 Structural Analysis")
        colM1, colM2 = st.columns(2)
        colM1.metric("Total Floor Area", f"{total_area:.1f} m²")
        colM2.metric("Total Floor Load (DL+LL)", f"{total_load:.1f} kN")

        colS1, colS2, colS3 = st.columns(3)
        colS1.metric("Max Span", f"{integrity['max_span_m']} m")
        colS2.metric("Suggested Beam", integrity['suggested_beam'])
        colS3.metric("Safety Factor", f"{integrity['safety_factor']:.2f}",
                     delta="Pass" if integrity['pass'] else "Fail")
        if not integrity['pass']:
            st.error("⚠️ Span too large. Add intermediate columns or reduce room sizes.")
        else:
            st.success("✅ Structural integrity check passed.")

        st.subheader("💰 Cost Estimation")
        cost_table = {
            "Item": ["Concrete", "Steel", "Glass", "Labor", "**TOTAL**"],
            "Cost (USD)": [
                f"${costs['concrete']:,.2f}",
                f"${costs['steel']:,.2f}",
                f"${costs['glass']:,.2f}",
                f"${costs['labor']:,.2f}",
                f"**${costs['total']:,.2f}**"
            ]
        }
        st.table(cost_table)

        st.subheader("⚡ Energy Efficiency")
        colEn1, colEn2 = st.columns(2)
        colEn1.metric("Energy Score", f"{energy}/100")
        colEn2.progress(energy/100)

        if st.button("📄 Log This Analysis"):
            log_event(username,
                      f"Eng: {building.name} Load {total_load:.1f}kN, Cost ${costs['total']:,.2f}, Energy {energy}/100")
            st.success("Analysis logged.")

else:  # Archives
    st.title("🗄️ Archives")
    if mem["buildings"]:
        for b_dict in reversed(mem["buildings"]):
            building = Building.from_dict(b_dict)
            with st.expander(f"{building.name} – Score {building.score}"):
                show_building(building, "Archived")
    else:
        st.info("No buildings yet. Go to the Evolution Chamber!")
