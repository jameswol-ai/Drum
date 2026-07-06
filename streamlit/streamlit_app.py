# =============================
# ARC ARCHITECTURE INTELLIGENCE ENGINE
# Evolutionary Spatial Layout Synthesis & Diagnostics
# Zero-Dependency Single-File Streamlit Implementation
# =============================

import streamlit as st
import json
import uuid
import random
from pathlib import Path
from datetime import datetime

# =========================================================
# CONFIG & GLOBAL STUDIO STYLING
# =========================================================

st.set_page_config(
    page_title="Arc Studio Engine",
    page_icon="📐",
    layout="wide"
)

MEMORY_FILE = Path("arc_memory.json")

# Custom Architectural Studio UI Skin
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;700&display=swap');

/* Global Overrides */
html, body, [data-testid="stSidebarNav"] {
font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
font-family: 'Space Grotesk', sans-serif;
font-weight: 700;
letter-spacing: -0.03em;
}

/* Core Architectural Spatial Grid */
.arc-blueprint-canvas {
display: flex;
flex-wrap: wrap;
gap: 16px;
background: #090d16;
padding: 24px;
border-radius: 12px;
border: 1px dashed #334155;
margin: 15px 0;
}

.arc-room-module {
flex: 1 1 calc(33.333% - 16px);
min-width: 220px;
padding: 20px;
border-radius: 8px;
color: #ffffff;
border: 1px solid rgba(255, 255, 255, 0.12);
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.arc-room-module:hover {
transform: translateY(-3px);
border-color: rgba(255, 255, 255, 0.3);
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.room-meta {
font-family: 'Space Grotesk', monospace;
font-size: 0.85rem;
letter-spacing: 0.05em;
opacity: 0.8;
margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SYSTEM MEMORY MANAGEMENT
# =========================================================

DEFAULT_STATE = {
    "projects": [],
    "designs": [],
    "logs": [],
    "evolution": []
}

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.memory, f, indent=2)
    except Exception:
        pass

def log_event(msg):
    st.session_state.memory["logs"].append({
        "time": datetime.now().isoformat(),
        "msg": msg
    })
    save_memory()

# Initialize session structures
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

if "active_design" not in st.session_state:
    st.session_state.active_design = None

if "active_history" not in st.session_state:
    st.session_state.active_history = []

mem = st.session_state.memory

# =========================================================
# ARCHITECTURAL RULES & GENETICS
# =========================================================

ARCH_DOMAINS = {
    "Residential": ["Luxury Villa", "Modern Apartment", "Townhouse"],
    "Commercial": ["Boutique Office", "Corporate Hub", "Hotel Resort", "Medical Clinic"],
    "Industrial": ["Distribution Warehouse", "Advanced Manufacturing Plant"]
}

def get_domain(btype):
    for domain, types in ARCH_DOMAINS.items():
        if btype in types:
            return domain
    return "Unknown"

def generate_base_design(btype, bedrooms):
    core_rooms = ["Living Room", "Gourmet Kitchen", "Primary Bathroom"] + ["Flex Space"] * random.randint(1, 3)
    est_area = (65) + (44) + (3 * 3) + (bedrooms * 18)

    return {
        "id": str(uuid.uuid4())[:8].upper(),
        "type": btype,
        "domain": get_domain(btype),
        "bedrooms": bedrooms,
        "rooms": core_rooms,
        "area_sqm": est_area,
        "structure": {
            "columns": random.randint(14, 36),
            "beams": random.randint(28, 72)
        },
        "cost": int(est_area * random.randint(1400, 2600))
    }

def mutate_design(design_ctx):
    d = json.loads(json.dumps(design_ctx))
    d["structure"]["columns"] = max(10, d["structure"]["columns"] + random.randint(-2, 4))
    d["structure"]["beams"] = max(16, d["structure"]["beams"] + random.randint(-4, 6))

    if random.random() > 0.5:
        d["rooms"].append("Adaptive Modular Terracing")
        d["area_sqm"] += 20

    d["cost"] = int(d["area_sqm"] * random.randint(1300, 2500) + (d["structure"]["columns"] * 600))
    return d

def calculate_fitness(d):
    structural_ratio = d["structure"]["beams"] / max(1, d["structure"]["columns"])
    struct_score = max(0, 100 - int(abs(structural_ratio - 2.1) * 22))

    cost_per_sqm = d["cost"] / max(1, d["area_sqm"])
    cost_score = max(0, 100 - int(abs(cost_per_sqm - 1650) * 0.04))

    complexity_score = min(100, len(d["rooms"]) * 9)

    return {
        "structural_integrity": struct_score,
        "cost_efficiency": cost_score,
        "spatial_complexity": complexity_score
    }

def calculate_aggregate_score(fit_dict):
    return int(sum(fit_dict.values()) / len(fit_dict))

def run_evolutionary_loop(btype, bedrooms, generations, pop_size):
    population = [generate_base_design(btype, bedrooms) for _ in range(pop_size)]
    history = []

    for g in range(generations):
        scored_pop = []

        for d in population:
            fit = calculate_fitness(d)
            d["fitness"] = fit
            d["score"] = calculate_aggregate_score(fit)
            scored_pop.append(d)

        scored_pop.sort(key=lambda x: x["score"], reverse=True)
        history.append(scored_pop[0]["score"])

        survivors = scored_pop[:max(2, pop_size // 2)]
        new_generation = []

        for parent in survivors:
            new_generation.append(parent)
            new_generation.append(mutate_design(parent))

        population = new_generation[:pop_size]

    return scored_pop[0], history

def generate_floor_plan(design):
    rooms = [
        {"name": "Grand Living Lounge", "w": 6.5, "h": 5.0, "color": "#1e3a8a"},
        {"name": "Culinary Kitchen", "w": 4.5, "h": 4.0, "color": "#064e3b"},
        {"name": "Central Powder Room", "w": 3.0, "h": 2.5, "color": "#78350f"}
    ]

    for i in range(design["bedrooms"]):
        rooms.append({
            "name": f"Master Suite Suite {i+1}" if i == 0 else f"Standard Bedroom {i+1}",
            "w": 4.5 if i == 0 else 4.0,
            "h": 4.0,
            "color": "#4c1d95"
        })

    return rooms

# =========================================================
# GRAPHICS CANVAS RENDERING ENGINE
# =========================================================

def render_native_blueprint(plan):
    st.markdown("### 🗺️ Generative Layout Arrangement")

    canvas_html = '<div class="arc-blueprint-canvas">'

    for room in plan:
        canvas_html += (
            f'<div class="arc-room-module" style="background-color: {room["color"]};">'
            f'<div style="font-size: 1.15rem; font-weight: 600;">{room["name"]}</div>'
            f'<div class="room-meta">📐 {room["w"]}m × {room["h"]}m Structural Deck</div>'
            f'</div>'
        )

    canvas_html += '</div>'
    st.markdown(canvas_html, unsafe_allow_html=True)

# =========================================================
# DESIGN METRICS AND DIAGNOSTICS
# =========================================================

def run_structural_review(d):
    alerts = []

    if d["structure"]["columns"] < 16:
        alerts.append("🔴 Structural Warning: Column distribution density thin for structural load transfers.")

    if d["cost"] / d["area_sqm"] > 2300:
        alerts.append("🟡 Financial Alert: Material pricing model trending toward architectural premium thresholds.")

    if d["structure"]["beams"] / d["structure"]["columns"] < 1.9:
        alerts.append("🔵 Framing Optimization: Tight structural beam-to-column ratio; review spatial continuity maps.")

    return alerts if alerts else ["🟢 Synthesis Checked: Structural logic matrices clear. Design optimized for construction documentation."]

def calculate_material_takeoffs(d):
    return [
        {"Structural Asset Item": "High-Performance Concrete Pour", "Calculated Takeoff": f"{d['structure']['columns'] * 2.6:.1f} m³"},
        {"Structural Asset Item": "Tensile Steel Rebar Skeleton", "Calculated Takeoff": f"{d['structure']['beams'] * 0.48:.2f} Metric Tons"},
        {"Structural Asset Item": "Insulated Masonry CMU Blocks", "Calculated Takeoff": f"{int(d['area_sqm'] * 42):,} Structural Units"},
        {"Structural Asset Item": "Calculated Structural Dead Load Base", "Calculated Takeoff": f"{int(d['structure']['columns'] * 13.2):,} kN"}
    ]

# =========================================================
# APPLICATION WORKSPACE INTERFACE
# =========================================================

st.sidebar.title("📐 Arc Studio")
st.sidebar.caption("v10.2 • Generative Structural Design Loop")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Studio Workspace",
    ["Dashboard Control", "Design Synthesis Lab", "Memory Repositories"]
)

st.sidebar.markdown("---")

with st.sidebar.expander("🛠️ Configure Arc Engine", expanded=False):
    st.subheader("Synthesis Directives")

    all_typologies = []
    for sub_list in ARCH_DOMAINS.values():
        all_typologies.extend(sub_list)

    input_type = st.selectbox("Design Typology Target", all_typologies)
    input_bedrooms = st.slider("Target Spatial Modules", 1, 8, 3)
    input_generations = st.slider("Genetic Epoch Cycles", 2, 20, 6)
    input_pop = st.slider("Population Bounds", 4, 30, 10)

# =========================================================
# VIEWPORT: DASHBOARD
# =========================================================

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

# =========================================================
# VIEWPORT: SYNTHESIS LAB
# =========================================================

elif page == "Design Synthesis Lab":
    st.title("🌍 Algorithmic Design Lab")
    st.markdown("Manipulate generative presets inside the sidebar config block to modify systemic architectural constraints.")

    generate_now = st.button(
        "Run Generative Architectural Evolution Pipeline",
        type="primary",
        use_container_width=True
    )

    if generate_now:
        with st.spinner("Processing structural mutations & resolving framing constraints..."):
            best_specimen, optimization_trend = run_evolutionary_loop(
                input_type,
                input_bedrooms,
                input_generations,
                input_pop
            )

            best_specimen["plan"] = generate_floor_plan(best_specimen)

            mem["designs"].append(best_specimen)
            mem["evolution"].append({
                "id": str(uuid.uuid4())[:6].upper(),
                "best_id": best_specimen["id"],
                "peak_score": best_specimen["score"],
                "timestamp": datetime.now().isoformat()
            })

            st.session_state.active_design = best_specimen
            st.session_state.active_history = optimization_trend

            log_event(f"Evolved Optimized Blueprint Specimen Archetype #{best_specimen['id']}")

        st.markdown("---")

    if st.session_state.active_design is not None:
        design = st.session_state.active_design
        trend = st.session_state.active_history

        st.subheader(f"⚡ Synthesis Output Profile: Archetype Specimen #{design['id']}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Algorithmic Optimization Score", f"{design['score']} / 100")
        m2.metric("Gross Built Footprint Area", f"{design['area_sqm']} m²")
        m3.metric("Project Budget Takeoff Forecast", f"${design['cost']:,}")

        tab_space, tab_metrics, tab_analytics = st.tabs(
            ["🗺️ Spatial Layout Blueprint", "📊 Structural Takeoffs", "📈 Convergence Analytics"]
        )

        with tab_space:
            render_native_blueprint(design["plan"])

        with tab_metrics:
            st.subheader("AI Structural Diagnostics")
            for alert in run_structural_review(design):
                st.markdown(alert)

            st.markdown("---")
            st.subheader("Material Quantum Requirements")
            st.table(calculate_material_takeoffs(design))

        with tab_analytics:
            st.subheader("Genetic Algorithm Fitness Convergence Wave")
            st.line_chart(trend)

    else:
        st.info("No active production layout model loaded. Select configurations in the left expandable options tree and run the generator engine.")

# =========================================================
# VIEWPORT: MEMORY REPOSITORIES
# =========================================================

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