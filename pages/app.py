# pages/app.py (fixed – KeyError proof)
# =============================
# GENERAL STREAMLIT DASHBOARD
# Replace the placeholder functions with your own logic.
# =============================

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import uuid
import random

st.set_page_config(page_title="General Studio", page_icon="⚙️", layout="wide",
                   initial_sidebar_state="expanded")

MEMORY_FILE = Path("app_memory.json")
MAX_HISTORY = 10

DEFAULT_STATE = {
    "projects": [],
    "designs": [],
    "logs": [],
    "evolution": [],
    "config_presets": {}
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

# ---------- Placeholder Domain Logic ----------
class Design:
    def __init__(self, id=None, score=50, parameters=None, plan=None):
        self.id = id or str(uuid.uuid4())[:6].upper()
        self.score = score
        self.parameters = parameters or {"param1": 0, "param2": 0}
        self.plan = plan or []

    def to_dict(self):
        return {
            "id": self.id,
            "score": self.score,
            "parameters": self.parameters,
            "plan": self.plan
        }

    @staticmethod
    def from_dict(d):
        return Design(d["id"], d["score"], d.get("parameters", {}), d.get("plan", []))

def generate_plan(design, width=800, height=500):
    plan = []
    cols, rows = 4, 3
    cell_w = width // cols
    cell_h = height // rows
    for i in range(cols * rows):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        plan.append({
            "x": x + 5, "y": y + 5,
            "w": cell_w - 10, "h": cell_h - 10,
            "name": f"Element {i+1}",
            "color": f"hsl({i * 50}, 70%, 50%)"
        })
    design.plan = plan
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

def run_evolutionary_loop(typology, generations, pop_size, config):
    trend = []
    score = 30 + random.randint(0, 20)
    for gen in range(generations):
        score += (70 - score) * 0.1 + random.uniform(-2, 2)
        score = min(100, max(0, score))
        trend.append(round(score, 2))
    best = Design(score=round(trend[-1], 2),
                  parameters={"dim": random.randint(10, 100), "density": round(random.random(), 2)})
    return best, trend

def run_review(design, config):
    msgs = []
    if design.score < 40:
        msgs.append(("danger", "Score critically low."))
    else:
        msgs.append(("success", "Design meets thresholds."))
    return msgs

def calculate_metrics(design):
    return [
        {"Metric": "Score", "Value": design.score},
        {"Metric": "Parameter 1", "Value": design.parameters.get("dim", 0)},
        {"Metric": "Parameter 2", "Value": design.parameters.get("density", 0)},
    ]

# ---------- Memory & Session ----------
def load_memory():
    """Load memory file and ensure ALL default keys exist."""
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
    except Exception:
        data = {}

    # Guarantee that every default key is present
    for key, default_value in DEFAULT_STATE.items():
        if key not in data:
            data[key] = default_value
    return data

def save_memory():
    try:
        # Ensure all expected keys exist before saving
        mem = st.session_state.memory
        for key in DEFAULT_STATE:
            if key not in mem:
                mem[key] = DEFAULT_STATE[key]
        if len(mem["designs"]) > MAX_HISTORY:
            mem["designs"] = mem["designs"][-MAX_HISTORY:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except Exception:
        pass

def log_event(msg):
    mem = st.session_state.memory
    # defensive: ensure logs list exists
    if "logs" not in mem:
        mem["logs"] = []
    mem["logs"].append({
        "time": datetime.now().isoformat(),
        "msg": msg
    })
    save_memory()

# ---------- Initialise session state ----------
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()
else:
    # Ensure current memory has all default keys (e.g., after a crash)
    for key, default_value in DEFAULT_STATE.items():
        if key not in st.session_state.memory:
            st.session_state.memory[key] = default_value

if "active_design" not in st.session_state:
    st.session_state.active_design = None
if "active_history" not in st.session_state:
    st.session_state.active_history = []
if "config" not in st.session_state:
    st.session_state.config = {
        "project_name": "Unnamed",
        "population_size": 10,
        "generations": 5,
        "mutation_rate": 0.2
    }

mem = st.session_state.memory

# ---------- Sidebar ----------
st.sidebar.title("⚙️ General Studio")
page = st.sidebar.radio("Workspace",
                        ["Dashboard", "Design Lab", "Memory"],
                        index=1)

with st.sidebar.expander("Project", expanded=True):
    st.session_state.config["project_name"] = st.text_input(
        "Project Name", value=st.session_state.config.get("project_name", "Unnamed"))
    typologies = ["Type A", "Type B", "Type C"]
    input_type = st.selectbox("Design Typology", typologies)

with st.sidebar.expander("Algorithm Tuning", expanded=False):
    st.session_state.config["mutation_rate"] = st.slider("Mutation Rate", 0.0, 1.0,
                                                         st.session_state.config.get("mutation_rate", 0.2), 0.05)

with st.sidebar.expander("Evolution Control", expanded=False):
    input_generations = st.slider("Generations", 2, 20,
                                  st.session_state.config.get("generations", 5))
    input_pop = st.slider("Population Size", 4, 30,
                          st.session_state.config.get("population_size", 10))

# ---------- Design History (defensive check) ----------
with st.sidebar.expander("History", expanded=False):
    # *** FIX: use .get() to avoid KeyError ***
    designs = mem.get("designs", [])
    if designs:
        ids = [d["id"] for d in designs]
        selected = st.selectbox("Load design", ["None"] + ids)
        if selected != "None" and st.button("Restore"):
            design_dict = next(d for d in designs if d["id"] == selected)
            design = Design.from_dict(design_dict)
            if not design.plan:
                design.plan = generate_plan(design)
            st.session_state.active_design = design
            st.session_state.active_history = []
            st.rerun()
    else:
        st.caption("No designs yet.")

# ---------- Dashboard Page ----------
if page == "Dashboard":
    st.title("📊 Dashboard")
    col1, col2 = st.columns(2)
    col1.metric("Designs stored", len(mem.get("designs", [])))
    col2.metric("Evolutions run", len(mem.get("evolution", [])))
    st.subheader("Recent logs")
    for log in reversed(mem.get("logs", [])[-5:]):
        st.caption(f"{log['time'][11:19]} – {log['msg']}")

# ---------- Design Lab Page ----------
elif page == "Design Lab":
    st.title("🧪 Design Lab")
    if st.button("▶ Run Optimisation", use_container_width=True, type="primary"):
        with st.spinner("Running..."):
            best, trend = run_evolutionary_loop(
                input_type, input_generations, input_pop, st.session_state.config
            )
            best.plan = generate_plan(best)
            # defensive: ensure designs list exists
            if "designs" not in mem:
                mem["designs"] = []
            mem["designs"].append(best.to_dict())
            if "evolution" not in mem:
                mem["evolution"] = []
            mem["evolution"].append({
                "id": str(uuid.uuid4())[:6].upper(),
                "best_id": best.id,
                "score": best.score,
                "timestamp": datetime.now().isoformat()
            })
            st.session_state.active_design = best
            st.session_state.active_history = trend
            log_event(f"Optimised design #{best.id}")
            save_memory()

    if st.session_state.active_design is not None:
        design = st.session_state.active_design
        trend = st.session_state.active_history
        st.subheader(f"Design #{design.id}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", design.score)
        col2.metric("Param 1", design.parameters.get("dim", "?"))
        col3.metric("Param 2", design.parameters.get("density", "?"))

        tab1, tab2, tab3 = st.tabs(["Plan", "Metrics", "Convergence"])
        with tab1:
            if design.plan:
                svg = render_svg_plan(design.plan)
                st.markdown(f'<div style="background:#0f172a; border-radius:12px; padding:8px;">{svg}</div>',
                            unsafe_allow_html=True)
            else:
                st.info("No plan to display.")
        with tab2:
            for level, msg in run_review(design, st.session_state.config):
                color_map = {"danger": "#ef4444", "warning": "#eab308", "info": "#3b82f6", "success": "#22c55e"}
                st.markdown(
                    f'<div style="border-left:4px solid {color_map.get(level, "#fff")}; padding:0.5rem; margin:0.2rem 0; background:rgba(255,255,255,0.03);">{msg}</div>',
                    unsafe_allow_html=True)
            st.table(calculate_metrics(design))
        with tab3:
            if trend:
                st.line_chart(trend)
    else:
        st.info("Run an optimisation to see results.")

# ---------- Memory Page ----------
else:
    st.title("🧠 Memory")
    st.json(mem)
    if st.button("Clear all data"):
        st.session_state.memory = DEFAULT_STATE.copy()
        st.session_state.active_design = None
        st.session_state.active_history = []
        save_memory()
        st.rerun()

if __name__ == "__main__":
    pass
