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
    layout="wide",
    initial_sidebar_state="expanded"
)

MEMORY_FILE = Path("arc_memory.json")

# ---------------------------------------------------------
# Custom Architectural Studio UI Skin – Enhanced Aesthetic
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600&family=Syne:wght@500;700;800&display=swap');

    /* ---------- Global Overrides ---------- */
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

    /* ---------- Sidebar Glass Panel ---------- */
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

    /* Sidebar title & caption */
    section[data-testid="stSidebar"] h1 {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* ---------- Buttons ---------- */
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

    /* Danger button (memory purge) */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%);
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
    }
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6);
    }

    /* ---------- Metrics Cards ---------- */
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
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
    }

    /* ---------- Tabs ---------- */
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

    /* ---------- Blueprint Canvas ---------- */
    .arc-blueprint-canvas {
        display: flex;
        flex-wrap: wrap;
        gap: 1.2rem;
        background: rgba(9, 13, 22, 0.7);
        backdrop-filter: blur(16px);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.15);
        margin: 1rem 0;
    }

    .arc-room-module {
        flex: 1 1 calc(33.333% - 1.2rem);
        min-width: 200px;
        padding: 1.5rem 1.5rem 1.2rem;
        border-radius: 12px;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.7));
        backdrop-filter: blur(8px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .arc-room-module::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--room-color), rgba(255,255,255,0.2));
        opacity: 0.6;
    }
    .arc-room-module:hover {
        transform: translateY(-6px);
        border-color: rgba(255, 255, 255, 0.25);
        box-shadow: 0 20px 35px rgba(0, 0, 0, 0.6);
    }
    .room-meta {
        font-family: 'Inter', monospace;
        font-size: 0.8rem;
        letter-spacing: 0.03em;
        opacity: 0.7;
        margin-top: 0.8rem;
    }
    .room-name {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    /* ---------- Data Tables (Takeoffs) ---------- */
    .stTable {
        background: rgba(15, 23, 42, 0.5);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    .stTable th {
        background: rgba(79, 70, 229, 0.15);
        color: #cbd5e1;
        font-family: 'Syne', sans-serif;
        font-weight: 600;
    }
    .stTable td {
        color: #e2e8f0;
    }

    /* ---------- Alerts (Structural Diagnostics) ---------- */
    .stMarkdown .alert {
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        backdrop-filter: blur(8px);
        border-left: 4px solid;
    }
    .alert-warning {
        background: rgba(234, 179, 8, 0.1);
        border-left-color: #eab308;
        color: #fef08a;
    }
    .alert-danger {
        background: rgba(239, 68, 68, 0.1);
        border-left-color: #ef4444;
        color: #fca5a5;
    }
    .alert-info {
        background: rgba(59, 130, 246, 0.1);
        border-left-color: #3b82f6;
        color: #93c5fd;
    }
    .alert-success {
        background: rgba(34, 197, 94, 0.1);
        border-left-color: #22c55e;
        color: #86efac;
    }

    /* ---------- Scrollbar ---------- */
    ::-webkit-scrollbar {
        width: 8px;
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
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
# GRAPHICS CANVAS RENDERING ENGINE (Enhanced)
# =========================================================

def render_native_blueprint(plan):
    st.markdown("### 🗺️ Generative Layout Arrangement")
    canvas_html = '<div class="arc-blueprint-canvas">'
    for room in plan:
        canvas_html += (
            f'<div class="arc-room-module" style="--room-color: {room["color"]}; background: linear-gradient(135deg, {room["color"]}dd, {room["color"]}44);">'
            f'<div class="room-name">{room["name"]}</div>'
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
        alerts.append(("danger", "🔴 Structural Warning: Column distribution density thin for structural load transfers."))
    if d["cost"] / d["area_sqm"] > 2300:
        alerts.append(("warning", "🟡 Financial Alert: Material pricing model trending toward architectural premium thresholds."))
    if d["structure"]["beams"] / d["structure"]["columns"] < 1.9:
        alerts.append(("info", "🔵 Framing Optimization: Tight structural beam-to-column ratio; review spatial continuity maps."))
    if not alerts:
        alerts.append(("success", "🟢 Synthesis Checked: Structural logic matrices clear. Design optimized for construction documentation."))
    return alerts

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
    ["Dashboard Control", "Design Synthesis Lab", "Memory Repositories"],
    index=1  # default to Synthesis Lab for quick access
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
        "▶ Run Generative Architectural Evolution Pipeline",
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
            for level, msg in run_structural_review(design):
                # Render styled alerts
                st.markdown(f'<div class="alert alert-{level}">{msg}</div>', unsafe_allow_html=True)

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