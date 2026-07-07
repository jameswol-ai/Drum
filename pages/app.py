# app.py
# =============================
# ARC STUDIO – STREAMLIT INTERFACE
# Uses engine.py for all logic
# =============================

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import uuid
import engine  # our core module

# ---------- Config & styling ----------
st.set_page_config(page_title="Arc Studio Engine", page_icon="📐", layout="wide",
                   initial_sidebar_state="expanded")

MEMORY_FILE = Path("arc_memory.json")
MAX_HISTORY = 10   # keep last N designs

DEFAULT_STATE = {
    "projects": [],
    "designs": [],
    "logs": [],
    "evolution": [],
    "config_presets": {}
}

# ---------- Custom Architectural Studio UI Skin – Enhanced Aesthetic ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600&family=Syne:wght@500;700;800&display=swap');

    html, body, [data-testid="stSidebarNav"], .stApp {
        font-family: 'Inter', sans-serif;
        background: #0b0f19;
        color: #e2e8f0;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f1f5f9;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(145deg, rgba(15,23,42,0.95) 0%, rgba(12,18,30,0.98) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(148, 163, 184, 0.15);
        box-shadow: 4px 0 30px rgba(0,0,0,0.5);
    }

    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] .stSelectbox label, 
    section[data-testid="stSidebar"] .stSlider label {
        color: #cbd5e1;
    }

    section[data-testid="stSidebar"] h1 {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.8rem;
        font-weight: 600;
        font-family: 'Syne', sans-serif;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.5);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        border-color: rgba(148, 163, 184, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 500;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 4px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-family: 'Syne', sans-serif;
        color: #94a3b8;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white !important;
        box-shadow: 0 2px 12px rgba(79, 70, 229, 0.4);
    }

    .floorplan-container {
        background: #0f172a;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.15);
        padding: 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        margin: 1rem 0;
        overflow: hidden;
    }
    .floorplan-svg {
        width: 100%;
        height: auto;
        display: block;
    }

    .alert {
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        backdrop-filter: blur(8px);
        border-left: 4px solid;
    }
    .alert-danger { background: rgba(239,68,68,0.1); border-left-color: #ef4444; color: #fca5a5; }
    .alert-warning { background: rgba(234,179,8,0.1); border-left-color: #eab308; color: #fef08a; }
    .alert-info { background: rgba(59,130,246,0.1); border-left-color: #3b82f6; color: #93c5fd; }
    .alert-success { background: rgba(34,197,94,0.1); border-left-color: #22c55e; color: #86efac; }

    ::-webkit-scrollbar { width: 8px; background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
""", unsafe_allow_html=True)

# ---------- Memory management ----------
def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                for key in DEFAULT_STATE:
                    if key not in data:
                        data[key] = DEFAULT_STATE[key]
                return data
        except Exception:
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

def save_memory():
    try:
        # Enforce history cap
        if len(st.session_state.memory["designs"]) > MAX_HISTORY:
            st.session_state.memory["designs"] = st.session_state.memory["designs"][-MAX_HISTORY:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(st.session_state.memory, f, indent=2)
    except Exception:
        pass

def log_event(msg):
    st.session_state.memory["logs"].append({
        "time": datetime.now().isoformat(),
        "msg": msg
    })
    save_memory()

# ---------- Session init ----------
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

if "active_design" not in st.session_state:
    st.session_state.active_design = None

if "active_history" not in st.session_state:
    st.session_state.active_history = []

if "config" not in st.session_state:
    st.session_state.config = {
        "project_name": "Unnamed Project",
        "mutation_rate": 0.5,
        "mutation_strength_col": 3,
        "mutation_strength_beam": 5,
        "elitism_frac": 0.4,
        "crossover_enabled": False,
        "ideal_beam_col_ratio": 2.1,
        "target_cost_per_sqm": 1650,
        "fitness_weights": {"structural": 1.0, "cost": 1.0, "complexity": 1.0},
        "units": "metric"
    }

mem = st.session_state.memory

# ---------- Sidebar ----------
st.sidebar.title("📐 Arc Studio")
st.sidebar.caption("v10.3 • Modular Generative Design Engine")
st.sidebar.markdown("---")

page = st.sidebar.radio("Studio Workspace",
                        ["Dashboard Control", "Design Synthesis Lab", "Memory Repositories"],
                        index=1)

st.sidebar.markdown("---")

with st.sidebar.expander("🏗️ Project & Typology", expanded=True):
    st.session_state.config["project_name"] = st.text_input("Project Name", value=st.session_state.config.get("project_name", "Unnamed Project"))
    all_typologies = [t for sub in engine.ARCH_DOMAINS.values() for t in sub]
    input_type = st.selectbox("Design Typology Target", all_typologies)
    input_bedrooms = st.slider("Target Spatial Modules (Bedrooms)", 1, 8, 3)

with st.sidebar.expander("🧬 Genetic Algorithm Tuning", expanded=False):
    st.session_state.config["mutation_rate"] = st.slider("Mutation Probability", 0.0, 1.0, st.session_state.config.get("mutation_rate", 0.5), 0.05)
    st.session_state.config["mutation_strength_col"] = st.slider("Column Mutation Range (±)", 0, 5, st.session_state.config.get("mutation_strength_col", 3))
    st.session_state.config["mutation_strength_beam"] = st.slider("Beam Mutation Range (±)", 0, 10, st.session_state.config.get("mutation_strength_beam", 5))
    st.session_state.config["elitism_frac"] = st.slider("Elitism Fraction", 0.1, 0.8, st.session_state.config.get("elitism_frac", 0.4), 0.05)
    st.session_state.config["crossover_enabled"] = st.checkbox("Enable Crossover (Recombination)", value=st.session_state.config.get("crossover_enabled", False))

with st.sidebar.expander("🏛️ Structural Constraints", expanded=False):
    st.session_state.config["ideal_beam_col_ratio"] = st.slider("Ideal Beam-Column Ratio", 1.5, 3.0, st.session_state.config.get("ideal_beam_col_ratio", 2.1), 0.1)
    st.session_state.config["target_cost_per_sqm"] = st.slider("Target Cost per m² ($)", 1000, 3000, st.session_state.config.get("target_cost_per_sqm", 1650), 50)
    st.markdown("**Fitness Weights**")
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.session_state.config["fitness_weights"]["structural"] = st.number_input("Structural", 0.0, 3.0, st.session_state.config["fitness_weights"].get("structural", 1.0), 0.1, key="fw_struct")
    with col_w2:
        st.session_state.config["fitness_weights"]["cost"] = st.number_input("Cost", 0.0, 3.0, st.session_state.config["fitness_weights"].get("cost", 1.0), 0.1, key="fw_cost")
    with col_w3:
        st.session_state.config["fitness_weights"]["complexity"] = st.number_input("Complexity", 0.0, 3.0, st.session_state.config["fitness_weights"].get("complexity", 1.0), 0.1, key="fw_comp")

with st.sidebar.expander("🎨 Display & Units", expanded=False):
    st.session_state.config["units"] = st.radio("Measurement System", ["metric", "imperial"], index=0 if st.session_state.config.get("units","metric")=="metric" else 1)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Save Current Config as Preset"):
    preset_name = f"Preset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.memory["config_presets"][preset_name] = dict(st.session_state.config)
    save_memory()
    log_event(f"Config preset '{preset_name}' saved.")
    st.sidebar.success(f"Preset '{preset_name}' saved!")

preset_names = list(st.session_state.memory.get("config_presets", {}).keys())
if preset_names:
    selected_preset = st.sidebar.selectbox("Load Preset", ["None"] + preset_names)
    if selected_preset != "None" and st.sidebar.button("Apply Preset"):
        st.session_state.config.update(st.session_state.memory["config_presets"][selected_preset])
        log_event(f"Applied preset '{selected_preset}'")
        st.rerun()

with st.sidebar.expander("⚡ Evolution Control", expanded=False):
    input_generations = st.slider("Genetic Epoch Cycles", 2, 20, 6)
    input_pop = st.slider("Population Bounds", 4, 30, 10)

# ---------- Design History Gallery ----------
with st.sidebar.expander("📚 Design History", expanded=False):
    if mem["designs"]:
        ids = [d["id"] for d in mem["designs"]]
        selected_id = st.selectbox("Load a previous design", ["None"] + ids)
        if selected_id != "None":
            if st.button("↩️ Restore Design"):
                design_dict = next(d for d in mem["designs"] if d["id"] == selected_id)
                design = engine.Design.from_dict(design_dict)
                if not design.plan:
                    design.plan = engine.generate_floor_plan_ai(design, 800, 500)
                st.session_state.active_design = design
                st.session_state.active_history = []
                st.rerun()
    else:
        st.caption("No designs yet.")

# ---------- Dashboard ----------
if page == "Dashboard Control":
    st.title("📐 Studio Control Dashboard")
    st.markdown("Systems active. Arc generative algorithms synchronized with engine hardware.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked Space Profiles", len(mem["projects"]))
    col2.metric("Evolved Blueprint Seeds", len(mem["designs"]))
    col3.metric("Total Parametric Compute Loops", len(mem["evolution"]))
    st.markdown("---")
    st.subheader("Engine Operational Telemetry Logs")
    if mem["logs"]:
        for log in reversed(mem["logs"][-6:]):
            st.caption(f"⏱️ {log['time'][11:19]} — {log['msg']}")
    else:
        st.info("System operational logs are current and empty.")

# ---------- Synthesis Lab ----------
elif page == "Design Synthesis Lab":
    st.title("🌍 Algorithmic Design Lab")
    st.markdown("Manipulate generative presets inside the sidebar config block to modify systemic architectural constraints.")

    generate_now = st.button("▶ Run Generative Architectural Evolution Pipeline",
                             type="primary", use_container_width=True)

    if generate_now:
        with st.spinner("Processing structural mutations & resolving framing constraints..."):
            best_specimen, optimization_trend = engine.run_evolutionary_loop(
                input_type, input_bedrooms, input_generations, input_pop,
                st.session_state.config
            )
            best_specimen.plan = engine.generate_floor_plan_ai(best_specimen, 800, 500)

            design_dict = best_specimen.to_dict()
            mem["designs"].append(design_dict)
            mem["evolution"].append({
                "id": str(uuid.uuid4())[:6].upper(),
                "best_id": best_specimen.id,
                "peak_score": best_specimen.score,
                "timestamp": datetime.now().isoformat()
            })
            st.session_state.active_design = best_specimen
            st.session_state.active_history = optimization_trend
            log_event(f"Evolved Optimized Blueprint Specimen Archetype #{best_specimen.id}")
            save_memory()
        st.markdown("---")

    if st.session_state.active_design is not None:
        design = st.session_state.active_design
        trend = st.session_state.active_history

        st.subheader(f"⚡ Synthesis Output Profile: Archetype Specimen #{design.id}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Algorithmic Optimization Score", f"{design.score} / 100")
        m2.metric("Gross Built Footprint Area", f"{design.area_sqm} m²")
        m3.metric("Project Budget Takeoff Forecast", f"${design.cost:,}")

        tab_space, tab_metrics, tab_analytics = st.tabs(
            ["🗺️ Spatial Layout Blueprint", "📊 Structural Takeoffs", "📈 Convergence Analytics"]
        )

        with tab_space:
            st.markdown("### 🧠 AI-Generated Floor Plan (Binary Space Partitioning)")
            svg_content = render_floor_plan_svg(design.plan, 800, 500)
            st.markdown(f'<div class="floorplan-container">{svg_content}</div>', unsafe_allow_html=True)
            st.caption("Adjacency‑optimised layout. Rooms are grouped intelligently.")

            col_ctrl1, col_ctrl2 = st.columns(2)
            with col_ctrl1:
                if st.button("🎲 Regenerate Layout (same rooms)"):
                    design.plan = engine.generate_floor_plan_ai(design, 800, 500)
                    for i, d in enumerate(mem["designs"]):
                        if d["id"] == design.id:
                            mem["designs"][i] = design.to_dict()
                            break
                    save_memory()
                    st.rerun()
            with col_ctrl2:
                st.download_button("⬇️ Download SVG", data=svg_content,
                                   file_name=f"floorplan_{design.id}.svg", mime="image/svg+xml")
                json_plan = json.dumps(design.plan, indent=2)
                st.download_button("📋 Download Room Data (JSON)", data=json_plan,
                                   file_name=f"rooms_{design.id}.json", mime="application/json")

        with tab_metrics:
            st.subheader("AI Structural Diagnostics")
            for level, msg in engine.run_structural_review(design, st.session_state.config):
                st.markdown(f'<div class="alert alert-{level}">{msg}</div>', unsafe_allow_html=True)
            st.markdown("---")
            st.subheader("Material Quantum Requirements")
            st.table(engine.calculate_material_takeoffs(design))

        with tab_analytics:
            st.subheader("Genetic Algorithm Fitness Convergence Wave")
            st.line_chart(trend)

    else:
        st.info("No active production layout model loaded. Configure settings and run the generator engine.")

# ---------- Memory Repositories ----------
elif page == "Memory Repositories":
    st.title("🧠 Engine Serialized Memory Cache")
    st.markdown("Review system variables and system architectural metadata arrays.")
    st.subheader("Raw Memory Store Model State")
    st.json(mem)
    st.markdown("---")
    if st.button("🔴 Purge Arc Studio System Memory State", use_container_width=True):
        st.session_state.memory = DEFAULT_STATE.copy()
        st.session_state.active_design = None
        st.session_state.active_history = []
        save_memory()
        st.success("State maps reset clean.")
        st.rerun()

# ---------- SVG render helper ----------
def render_floor_plan_svg(rooms, width=800, height=500):
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" class="floorplan-svg" style="background: #0f172a;">'
    ]
    for i in range(0, width, 50):
        svg_parts.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="#1e293b" stroke-width="0.5" opacity="0.3"/>')
    for j in range(0, height, 50):
        svg_parts.append(f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="#1e293b" stroke-width="0.5" opacity="0.3"/>')
    for room in rooms:
        x, y, w, h = room["x"], room["y"], room["w"], room["h"]
        color = room["color"]
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.25" '
            f'stroke="#475569" stroke-width="2" stroke-opacity="0.8"/>'
        )
        font_size = min(w//8, h//6, 16)
        svg_parts.append(
            f'<text x="{x+w/2}" y="{y+h/2}" font-family="Syne, sans-serif" font-size="{font_size}" '
            f'fill="#e2e8f0" text-anchor="middle" dominant-baseline="middle" font-weight="600">{room["name"]}</text>'
        )
        dim_text = f'{w//5}m × {h//5}m'
        svg_parts.append(
            f'<text x="{x+w/2}" y="{y+h/2+font_size+5}" font-family="Inter" font-size="{max(8,font_size-2)}" '
            f'fill="#94a3b8" text-anchor="middle">{dim_text}</text>'
        )
    svg_parts.append('</svg>')
    return ''.join(svg_parts)

if __name__ == "__main__":
    pass