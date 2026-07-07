# streamlit_app.py
# =============================
# DRUM – Design & Rhythm Utility Machine
# Main entry point. Replace placeholder functions with your own logic.
# =============================

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import uuid
import random

st.set_page_config(page_title="DRUM Studio", page_icon="🥁", layout="wide",
                   initial_sidebar_state="expanded")

MEMORY_FILE = Path("drum_memory.json")
MAX_HISTORY = 10

DEFAULT_STATE = {
    "buildings": [],
    "rhythms": [],
    "logs": [],
    "sessions": []
}

CUSTOM_CSS = """
<style>
    html, body, [data-testid="stSidebarNav"], .stApp {
        font-family: 'Inter', sans-serif;
        background: #0b0f19; color: #e2e8f0;
    }
    h1, h2, h3 { color: #f1f5f9; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(145deg, rgba(15,23,42,0.95), rgba(12,18,30,0.98));
        backdrop-filter: blur(20px);
    }
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;
        border: none; border-radius: 10px; padding: 0.6rem 1.8rem; font-weight: 600;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03); border: 1px solid #334155;
        border-radius: 12px; padding: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================
# DOMAIN LOGIC (replace later)
# =============================
class Building:
    """Simulated building / design entity."""
    def __init__(self, id=None, name="", score=50, plan=None):
        self.id = id or str(uuid.uuid4())[:6].upper()
        self.name = name or f"Bldg_{self.id}"
        self.score = score
        self.plan = plan or []

    def to_dict(self):
        return {"id": self.id, "name": self.name, "score": self.score, "plan": self.plan}

    @staticmethod
    def from_dict(d):
        b = Building(d["id"], d.get("name", ""), d["score"], d.get("plan", []))
        return b

def generate_building_plan(building, width=800, height=500):
    """Create a placeholder plan (grid of boxes) for a building."""
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

# FIXED: show_building defined BEFORE any call.
def show_building(building, label):
    """Display building details and an SVG plan."""
    st.subheader(f"Building {label} — {building.name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", building.score)
    col2.metric("ID", building.id)
    col3.metric("Rooms", len(building.plan))

    if building.plan:
        svg = render_svg_plan(building.plan)
        st.markdown(
            f'<div style="background:#0f172a; border-radius:12px; padding:8px;">{svg}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No plan available.")

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
    """Simulated optimisation loop. Returns (best_building, trend)."""
    trend = []
    score = 30 + random.randint(0, 20)
    for _ in range(config["generations"]):
        score += (70 - score) * 0.1 + random.uniform(-2, 2)
        score = min(100, max(0, score))
        trend.append(round(score, 2))
    best = Building(name=f"Gen_{config['generations']}", score=round(trend[-1], 2))
    return best, trend

# =============================
# MEMORY & SESSION
# =============================
def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                for k in DEFAULT_STATE:
                    if k not in data:
                        data[k] = DEFAULT_STATE[k]
                return data
        except:
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

def save_memory():
    try:
        if len(st.session_state.memory["buildings"]) > MAX_HISTORY:
            st.session_state.memory["buildings"] = st.session_state.memory["buildings"][-MAX_HISTORY:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(st.session_state.memory, f, indent=2)
    except:
        pass

def log_event(msg):
    st.session_state.memory["logs"].append({"time": datetime.now().isoformat(), "msg": msg})
    save_memory()

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()
if "active_building" not in st.session_state:
    st.session_state.active_building = None
if "config" not in st.session_state:
    st.session_state.config = {"generations": 5, "style": "minimal"}

mem = st.session_state.memory

# =============================
# UI
# =============================
st.sidebar.title("🥁 DRUM Studio")
page = st.sidebar.radio("Navigate", ["Dashboard", "Design Lab", "Memory"], index=1)

with st.sidebar.expander("Settings"):
    st.session_state.config["generations"] = st.slider("Generations", 2, 20, st.session_state.config["generations"])
    st.session_state.config["style"] = st.selectbox("Style", ["minimal", "bold", "organic"])

# --- Main call: now show_building is definitely defined ---
# Example: if an active building exists, display it
if st.session_state.active_building:
    show_building(st.session_state.active_building, "Active")
else:
    # Still fine because show_building is already defined.
    # We'll create a demo building to avoid errors but not overwrite anything.
    demo = Building(name="Demo", score=85)
    generate_building_plan(demo)
    show_building(demo, "Demo")  # line 476 would have crashed before; now it's safe

# =============================
# Dashboard
# =============================
if page == "Dashboard":
    st.title("📊 Dashboard")
    c1, c2 = st.columns(2)
    c1.metric("Buildings stored", len(mem["buildings"]))
    c2.metric("Sessions", len(mem["sessions"]))
    st.subheader("Recent logs")
    for log in reversed(mem["logs"][-5:]):
        st.caption(f"{log['time'][11:19]} – {log['msg']}")

elif page == "Design Lab":
    st.title("🧪 Design Lab")
    if st.button("Run Optimisation", type="primary"):
        with st.spinner("Evolving..."):
            best, trend = simulate_design_evolution(st.session_state.config)
            generate_building_plan(best)
            mem["buildings"].append(best.to_dict())
            mem["sessions"].append({"id": str(uuid.uuid4())[:6], "building_id": best.id, "time": datetime.now().isoformat()})
            st.session_state.active_building = best
            log_event(f"New design: {best.name}")
            save_memory()
    if st.session_state.active_building:
        show_building(st.session_state.active_building, "Active")  # fine
    else:
        st.info("Run an optimisation to see results.")

else:  # Memory
    st.title("🧠 Memory")
    st.json(mem)
    if st.button("Clear all"):
        st.session_state.memory = DEFAULT_STATE.copy()
        st.session_state.active_building = None
        save_memory()
        st.rerun()
