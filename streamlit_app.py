# streamlit_app.py
# =============================
# ARC ARCHITECTURE INTELLIGENCE ENGINE
# Evolutionary Spatial Layout Synthesis & Diagnostics
# Zero-Dependency Single-File Streamlit Implementation
# Includes: weighted fitness, adjacency-aware BSP, re-roll, export, design history
# =============================

import streamlit as st
import json
import uuid
import random
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ------------------------------------------------------------
# CONFIG & GLOBAL STUDIO STYLING
# ------------------------------------------------------------

st.set_page_config(
    page_title="Arc Studio Engine",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

MEMORY_FILE = Path("arc_memory.json")
MAX_HISTORY = 10  # keep only last N designs in memory

# ------------------------------------------------------------
# Custom Architectural Studio UI Skin – stored safely in a variable
# ------------------------------------------------------------
CUSTOM_CSS = """
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
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------
# SYSTEM MEMORY MANAGEMENT
# ------------------------------------------------------------
DEFAULT_STATE = {
    "projects": [],
    "designs": [],
    "logs": [],
    "evolution": [],
    "config_presets": {}
}

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
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
        if len(st.session_state.memory["designs"]) > MAX_HISTORY:
            st.session_state.memory["designs"] = st.session_state.memory["designs"][-MAX_HISTORY:]
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
        "fitness_weights": {
            "structural": 1.0,
            "cost": 1.0,
            "complexity": 1.0
        },
        "units": "metric"
    }

mem = st.session_state.memory

# ------------------------------------------------------------
# ARCHITECTURAL DOMAINS & ROOM COLOR MAPPING
# ------------------------------------------------------------
ARCH_DOMAINS = {
    "Residential": ["Luxury Villa", "Modern Apartment", "Townhouse"],
    "Commercial": ["Boutique Office", "Corporate Hub", "Hotel Resort", "Medical Clinic"],
    "Industrial": ["Distribution Warehouse", "Advanced Manufacturing Plant"]
}

ROOM_COLORS = {
    "Living Room": "#1e3a8a",
    "Gourmet Kitchen": "#064e3b",
    "Primary Bathroom": "#78350f",
    "Flex Space": "#475569",
    "Adaptive Modular Terracing": "#0f766e",
    "Bedroom": "#4c1d95",
    "Corridor": "#334155",
    "Master Bedroom": "#4c1d95",
    "Void": "#1e293b"
}

# ------------------------------------------------------------
# GENETIC OPERATORS
# ------------------------------------------------------------
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

def mutate_design(design, config):
    d = json.loads(json.dumps(design))  # deep copy
    col_mut = config.get("mutation_strength_col", 3)
    beam_mut = config.get("mutation_strength_beam", 5)
    d["structure"]["columns"] = max(10, d["structure"]["columns"] + random.randint(-col_mut, col_mut))
    d["structure"]["beams"] = max(16, d["structure"]["beams"] + random.randint(-beam_mut, beam_mut))
    if random.random() < config.get("mutation_rate", 0.5):
        d["rooms"].append("Adaptive Modular Terracing")
        d["area_sqm"] += 20
    d["cost"] = int(d["area_sqm"] * random.randint(1300, 2500) + (d["structure"]["columns"] * 600))
    return d

def crossover_designs(parent1, parent2):
    child = json.loads(json.dumps(parent1))
    if random.random() < 0.5:
        child["structure"]["columns"] = parent2["structure"]["columns"]
    if random.random() < 0.5:
        child["structure"]["beams"] = parent2["structure"]["beams"]
    child["rooms"] = list(set(parent1["rooms"] + parent2["rooms"]))
    child["area_sqm"] = max(parent1["area_sqm"], parent2["area_sqm"]) + 5
    child["cost"] = int(child["area_sqm"] * random.randint(1400, 2600) + (child["structure"]["columns"] * 600))
    return child

# ------------------------------------------------------------
# FITNESS CALCULATION (weighted)
# ------------------------------------------------------------
def calculate_fitness(d, config):
    ideal_ratio = config.get("ideal_beam_col_ratio", 2.1)
    target_cost = config.get("target_cost_per_sqm", 1650)
    weights = config.get("fitness_weights", {"structural":1.0, "cost":1.0, "complexity":1.0})
    structural_ratio = d["structure"]["beams"] / max(1, d["structure"]["columns"])
    struct_score = max(0, 100 - int(abs(structural_ratio - ideal_ratio) * 22))
    cost_per_sqm = d["cost"] / max(1, d["area_sqm"])
    cost_score = max(0, 100 - int(abs(cost_per_sqm - target_cost) * 0.04))
    complexity_score = min(100, len(d["rooms"]) * 9)
    return {
        "structural_integrity": int(struct_score * weights["structural"]),
        "cost_efficiency": int(cost_score * weights["cost"]),
        "spatial_complexity": int(complexity_score * weights["complexity"])
    }

def calculate_aggregate_score(fit_dict, weights):
    struct = fit_dict["structural_integrity"]
    cost   = fit_dict["cost_efficiency"]
    compl  = fit_dict["spatial_complexity"]
    w_s = weights.get("structural", 1.0)
    w_c = weights.get("cost", 1.0)
    w_x = weights.get("complexity", 1.0)
    total_weight = w_s + w_c + w_x
    if total_weight == 0:
        return 0
    return int((struct*w_s + cost*w_c + compl*w_x) / total_weight)

# ------------------------------------------------------------
# EVOLUTION LOOP
# ------------------------------------------------------------
def run_evolutionary_loop(btype, bedrooms, generations, pop_size, config):
    population = [generate_base_design(btype, bedrooms) for _ in range(pop_size)]
    history = []
    elitism_count = max(1, int(pop_size * config.get("elitism_frac", 0.4)))
    weights = config.get("fitness_weights", {})

    for g in range(generations):
        scored_pop = []
        for d in population:
            fit = calculate_fitness(d, config)
            d["fitness"] = fit
            d["score"] = calculate_aggregate_score(fit, weights)
            scored_pop.append(d)
        scored_pop.sort(key=lambda x: x["score"], reverse=True)
        history.append(scored_pop[0]["score"])

        new_generation = scored_pop[:elitism_count]
        while len(new_generation) < pop_size:
            if config.get("crossover_enabled") and len(scored_pop) >= 2:
                parent1 = random.choice(scored_pop[:max(2, pop_size//2)])
                parent2 = random.choice(scored_pop[:max(2, pop_size//2)])
                child = crossover_designs(parent1, parent2)
                child = mutate_design(child, config)
                new_generation.append(child)
            else:
                parent = random.choice(scored_pop[:max(2, pop_size//2)])
                child = mutate_design(parent, config)
                new_generation.append(child)
        population = new_generation[:pop_size]

    # final scoring
    for d in population:
        fit = calculate_fitness(d, config)
        d["fitness"] = fit
        d["score"] = calculate_aggregate_score(fit, weights)
    best = max(population, key=lambda x: x["score"])
    return best, history

# ------------------------------------------------------------
# BSP FLOOR PLAN GENERATOR (with adjacency optimization)
# ------------------------------------------------------------
class BSPNode:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.left = None
        self.right = None
        self.room = None

def split_node(node, horizontal=True):
    if horizontal:
        split = node.w // 2
        node.left = BSPNode(node.x, node.y, split, node.h)
        node.right = BSPNode(node.x + split, node.y, node.w - split, node.h)
    else:
        split = node.h // 2
        node.left = BSPNode(node.x, node.y, node.w, split)
        node.right = BSPNode(node.x, node.y + split, node.w, node.h - split)

def build_bsp_tree(node, depth, max_depth):
    if depth >= max_depth:
        return
    horizontal = (depth % 2 == 0)
    if (horizontal and node.w < 100) or (not horizontal and node.h < 100):
        return
    split_node(node, horizontal)
    build_bsp_tree(node.left, depth+1, max_depth)
    build_bsp_tree(node.right, depth+1, max_depth)

def collect_leaves(node, leaves):
    if node.left is None and node.right is None:
        leaves.append(node)
    else:
        if node.left:
            collect_leaves(node.left, leaves)
        if node.right:
            collect_leaves(node.right, leaves)

def assign_rooms_to_leaves(leaves, rooms):
    random.shuffle(rooms)
    for i, leaf in enumerate(leaves):
        leaf.room = rooms[i] if i < len(rooms) else "Corridor"

# Adjacency preferences
ADJACENCY = {
    "Living Room":       {"Gourmet Kitchen": 3, "Flex Space": 2},
    "Gourmet Kitchen":   {"Living Room": 3, "Flex Space": 2},
    "Primary Bathroom":  {"Master Bedroom": 3, "Bedroom": 2},
    "Bedroom":           {"Primary Bathroom": 3, "Master Bedroom": 2},
    "Master Bedroom":    {"Primary Bathroom": 3, "Bedroom": 2},
    "Flex Space":        {"Living Room": 2, "Gourmet Kitchen": 2},
}

def neighbour_score(a, b):
    if not a.room or not b.room:
        return 0
    s = ADJACENCY.get(a.room, {}).get(b.room, 0)
    s += ADJACENCY.get(b.room, {}).get(a.room, 0)
    return s

def optimise_adjacency(leaves, iterations=200):
    """Greedy swap to improve adjacency of preferred room neighbours."""
    # Build neighbour pairs (touching rectangles)
    neighbours = {i: [] for i in range(len(leaves))}
    for i, a in enumerate(leaves):
        for j, b in enumerate(leaves):
            if i >= j:
                continue
            h_overlap = (a.x < b.x + b.w and a.x + a.w > b.x)
            v_overlap = (a.y < b.y + b.h and a.y + a.h > b.y)
            if (abs(a.x + a.w - b.x) < 5 and v_overlap) or \
               (abs(b.x + b.w - a.x) < 5 and v_overlap) or \
               (abs(a.y + a.h - b.y) < 5 and h_overlap) or \
               (abs(b.y + b.h - a.y) < 5 and h_overlap):
                neighbours[i].append(j)
                neighbours[j].append(i)

    def total_score():
        s = 0
        for i, js in neighbours.items():
            for j in js:
                s += neighbour_score(leaves[i], leaves[j])
        return s

    current_score = total_score()
    for _ in range(iterations):
        i, j = random.sample(range(len(leaves)), 2)
        leaves[i].room, leaves[j].room = leaves[j].room, leaves[i].room
        new_score = total_score()
        if new_score > current_score:
            current_score = new_score
        else:
            leaves[i].room, leaves[j].room = leaves[j].room, leaves[i].room

def generate_floor_plan_ai(design, canvas_width=800, canvas_height=500):
    rooms_raw = design["rooms"][:]
    # Add bedrooms
    for i in range(design.get("bedrooms", 0)):
        room_name = "Master Bedroom" if i == 0 else f"Bedroom {i+1}"
        rooms_raw.append(room_name)
    if len(rooms_raw) < 3:
        rooms_raw += ["Flex Space"] * (3 - len(rooms_raw))

    num_rooms = len(rooms_raw)
    depth = math.ceil(math.log2(num_rooms)) + 1

    root = BSPNode(0, 0, canvas_width, canvas_height)
    build_bsp_tree(root, 0, depth)
    leaves = []
    collect_leaves(root, leaves)

    # fallback if not enough leaves
    while len(leaves) < num_rooms and depth < 10:
        depth += 1
        root = BSPNode(0, 0, canvas_width, canvas_height)
        build_bsp_tree(root, 0, depth)
        leaves = []
        collect_leaves(root, leaves)

    assign_rooms_to_leaves(leaves, rooms_raw)
    optimise_adjacency(leaves)   # 🔥 adjacency optimization

    plan_rooms = []
    for leaf in leaves:
        if leaf.room is None:
            leaf.room = "Void"
        color = ROOM_COLORS.get(leaf.room, "#" + ''.join(random.choices("89ABCDEF", k=6)))
        plan_rooms.append({
            "name": leaf.room,
            "x": leaf.x,
            "y": leaf.y,
            "w": leaf.w,
            "h": leaf.h,
            "color": color
        })
    return plan_rooms

# ------------------------------------------------------------
# STRUCTURAL DIAGNOSTICS & TAKEOFFS
# ------------------------------------------------------------
def run_structural_review(d, config):
    alerts = []
    if d["structure"]["columns"] < 16:
        alerts.append(("danger", "🔴 Structural Warning: Column density too low for load transfer."))
    if d["cost"] / d["area_sqm"] > config["target_cost_per_sqm"] * 1.4:
        alerts.append(("warning", "🟡 Financial Alert: Cost per sqm exceeds target threshold."))
    if d["structure"]["beams"] / d["structure"]["columns"] < config["ideal_beam_col_ratio"] * 0.9:
        alerts.append(("info", "🔵 Framing Optimization: Beam-column ratio lower than ideal."))
    if not alerts:
        alerts.append(("success", "🟢 Synthesis Checked: Structural logic matrices clear."))
    return alerts

def calculate_material_takeoffs(d):
    return [
        {"Structural Asset Item": "High-Performance Concrete Pour", "Calculated Takeoff": f"{d['structure']['columns'] * 2.6:.1f} m³"},
        {"Structural Asset Item": "Tensile Steel Rebar Skeleton", "Calculated Takeoff": f"{d['structure']['beams'] * 0.48:.2f} Metric Tons"},
        {"Structural Asset Item": "Insulated Masonry CMU Blocks", "Calculated Takeoff": f"{int(d['area_sqm'] * 42):,} Structural Units"},
        {"Structural Asset Item": "Calculated Structural Dead Load Base", "Calculated Takeoff": f"{int(d['structure']['columns'] * 13.2):,} kN"}
    ]

# ------------------------------------------------------------
# SVG RENDERING
# ------------------------------------------------------------
def render_floor_plan_svg(rooms, width=800, height=500):
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" class="floorplan-svg" style="background: #0f172a;">'
    ]
    # Grid
    for i in range(0, width, 50):
        svg_parts.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="#1e293b" stroke-width="0.5" opacity="0.3"/>')
    for j in range(0, height, 50):
        svg_parts.append(f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="#1e293b" stroke-width="0.5" opacity="0.3"/>')
    # Rooms
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

# ------------------------------------------------------------
# SIDEBAR WORKSPACE
# ------------------------------------------------------------
st.sidebar.title("📐 Arc Studio")
st.sidebar.caption("v10.3 • Generative Structural Design Loop")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Studio Workspace",
    ["Dashboard Control", "Design Synthesis Lab", "Memory Repositories"],
    index=1
)
st.sidebar.markdown("---")

with st.sidebar.expander("🏗️ Project & Typology", expanded=True):
    st.session_state.config["project_name"] = st.text_input("Project Name", value=st.session_state.config.get("project_name", "Unnamed Project"))
    all_typologies = [t for sub in ARCH_DOMAINS.values() for t in sub]
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

# ---------- Design History Gallery in Sidebar ----------
with st.sidebar.expander("📚 Design History", expanded=False):
    if mem["designs"]:
        ids = [d["id"] for d in mem["designs"]]
        selected_id = st.selectbox("Load a previous design", ["None"] + ids)
        if selected_id != "None":
            if st.button("↩️ Restore Design"):
                design_dict = next(d for d in mem["designs"] if d["id"] == selected_id)
                # Ensure it has a plan (for older designs)
                if "plan" not in design_dict or not design_dict["plan"]:
                    design_dict["plan"] = generate_floor_plan_ai(design_dict, 800, 500)
                st.session_state.active_design = design_dict
                st.session_state.active_history = []
                st.rerun()
    else:
        st.caption("No designs yet.")

# ------------------------------------------------------------
# VIEWPORT: DASHBOARD
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# VIEWPORT: DESIGN SYNTHESIS LAB
# ------------------------------------------------------------
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
                input_pop,
                st.session_state.config
            )

            # AI-powered floor plan (BSP with adjacency)
            best_specimen["plan"] = generate_floor_plan_ai(best_specimen, canvas_width=800, canvas_height=500)

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
            save_memory()

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
            st.markdown("### 🧠 AI-Generated Floor Plan (Binary Space Partitioning)")
            svg_content = render_floor_plan_svg(design["plan"], width=800, height=500)
            st.markdown(f'<div class="floorplan-container">{svg_content}</div>', unsafe_allow_html=True)
            st.caption("Adjacency‑optimised layout. Rooms are grouped intelligently.")

            # Re-roll & Export
            col_ctrl1, col_ctrl2 = st.columns(2)
            with col_ctrl1:
                if st.button("🎲 Regenerate Layout (same rooms)"):
                    design["plan"] = generate_floor_plan_ai(design, 800, 500)
                    # Update the stored design in memory
                    for i, d in enumerate(mem["designs"]):
                        if d["id"] == design["id"]:
                            mem["designs"][i] = design
                            break
                    save_memory()
                    st.rerun()
            with col_ctrl2:
                st.download_button("⬇️ Download SVG", data=svg_content,
                                   file_name=f"floorplan_{design['id']}.svg", mime="image/svg+xml")
                json_plan = json.dumps(design["plan"], indent=2)
                st.download_button("📋 Download Room Data (JSON)", data=json_plan,
                                   file_name=f"rooms_{design['id']}.json", mime="application/json")

        with tab_metrics:
            st.subheader("AI Structural Diagnostics")
            for level, msg in run_structural_review(design, st.session_state.config):
                st.markdown(f'<div class="alert alert-{level}">{msg}</div>', unsafe_allow_html=True)
            st.markdown("---")
            st.subheader("Material Quantum Requirements")
            st.table(calculate_material_takeoffs(design))

        with tab_analytics:
            st.subheader("Genetic Algorithm Fitness Convergence Wave")
            st.line_chart(trend)

    else:
        st.info("No active production layout model loaded. Configure settings and run the generator engine.")

# ------------------------------------------------------------
# VIEWPORT: MEMORY REPOSITORIES
# ------------------------------------------------------------
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

if __name__ == "__main__":
    pass