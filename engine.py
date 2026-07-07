# engine.py
# =============================
# ARC ARCHITECTURE INTELLIGENCE ENGINE
# Core modules: genetic algorithm, BSP floor plan, fitness
# =============================

import random
import math
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# ------------------------------------------------------------
# Domain constants & colour mapping
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
# Data structures
# ------------------------------------------------------------

@dataclass
class Design:
    id: str
    type: str
    domain: str
    bedrooms: int
    rooms: List[str]
    area_sqm: float
    structure: Dict[str, int]   # {"columns": int, "beams": int}
    cost: int
    fitness: Dict[str, int] = field(default_factory=dict)
    score: int = 0
    plan: List[Dict] = field(default_factory=list)  # rooms for SVG

    def to_dict(self):
        """Serialise to JSON‑safe dict (plan is list of dicts)."""
        return {
            "id": self.id,
            "type": self.type,
            "domain": self.domain,
            "bedrooms": self.bedrooms,
            "rooms": self.rooms,
            "area_sqm": self.area_sqm,
            "structure": self.structure,
            "cost": self.cost,
            "fitness": self.fitness,
            "score": self.score,
            "plan": self.plan
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            type=d["type"],
            domain=d["domain"],
            bedrooms=d["bedrooms"],
            rooms=d["rooms"],
            area_sqm=d["area_sqm"],
            structure=d["structure"],
            cost=d["cost"],
            fitness=d.get("fitness", {}),
            score=d.get("score", 0),
            plan=d.get("plan", [])
        )

# ------------------------------------------------------------
# Genetic operators
# ------------------------------------------------------------

def get_domain(btype: str) -> str:
    for domain, types in ARCH_DOMAINS.items():
        if btype in types:
            return domain
    return "Unknown"

def generate_base_design(btype: str, bedrooms: int) -> Design:
    core_rooms = ["Living Room", "Gourmet Kitchen", "Primary Bathroom"] + ["Flex Space"] * random.randint(1, 3)
    est_area = (65) + (44) + (3 * 3) + (bedrooms * 18)
    return Design(
        id=str(uuid.uuid4())[:8].upper(),
        type=btype,
        domain=get_domain(btype),
        bedrooms=bedrooms,
        rooms=core_rooms,
        area_sqm=est_area,
        structure={"columns": random.randint(14, 36), "beams": random.randint(28, 72)},
        cost=int(est_area * random.randint(1400, 2600))
    )

def mutate_design(design: Design, config: dict) -> Design:
    d = design.to_dict()  # work with a copy
    col_mut = config.get("mutation_strength_col", 3)
    beam_mut = config.get("mutation_strength_beam", 5)
    d["structure"]["columns"] = max(10, d["structure"]["columns"] + random.randint(-col_mut, col_mut))
    d["structure"]["beams"] = max(16, d["structure"]["beams"] + random.randint(-beam_mut, beam_mut))
    if random.random() < config.get("mutation_rate", 0.5):
        d["rooms"].append("Adaptive Modular Terracing")
        d["area_sqm"] += 20
    d["cost"] = int(d["area_sqm"] * random.randint(1300, 2500) + (d["structure"]["columns"] * 600))
    return Design.from_dict(d)

def crossover_designs(parent1: Design, parent2: Design) -> Design:
    child = parent1.to_dict()
    if random.random() < 0.5:
        child["structure"]["columns"] = parent2.structure["columns"]
    if random.random() < 0.5:
        child["structure"]["beams"] = parent2.structure["beams"]
    child["rooms"] = list(set(parent1.rooms + parent2.rooms))
    child["area_sqm"] = max(parent1.area_sqm, parent2.area_sqm) + 5
    child["cost"] = int(child["area_sqm"] * random.randint(1400, 2600) + (child["structure"]["columns"] * 600))
    return Design.from_dict(child)

# ------------------------------------------------------------
# Fitness calculation (weighted)
# ------------------------------------------------------------

def calculate_fitness(design: Design, config: dict) -> Dict[str, int]:
    ideal_ratio = config.get("ideal_beam_col_ratio", 2.1)
    target_cost = config.get("target_cost_per_sqm", 1650)
    weights = config.get("fitness_weights", {"structural":1.0, "cost":1.0, "complexity":1.0})

    structural_ratio = design.structure["beams"] / max(1, design.structure["columns"])
    struct_score = max(0, 100 - int(abs(structural_ratio - ideal_ratio) * 22))
    cost_per_sqm = design.cost / max(1, design.area_sqm)
    cost_score = max(0, 100 - int(abs(cost_per_sqm - target_cost) * 0.04))
    complexity_score = min(100, len(design.rooms) * 9)

    return {
        "structural_integrity": int(struct_score * weights["structural"]),
        "cost_efficiency": int(cost_score * weights["cost"]),
        "spatial_complexity": int(complexity_score * weights["complexity"])
    }

def calculate_aggregate_score(fit_dict: Dict[str, int], weights: Dict[str, float]) -> int:
    """Weighted sum normalised to 0-100."""
    struct = fit_dict["structural_integrity"]
    cost   = fit_dict["cost_efficiency"]
    compl  = fit_dict["spatial_complexity"]
    w_s = weights.get("structural", 1.0)
    w_c = weights.get("cost", 1.0)
    w_x = weights.get("complexity", 1.0)
    total_weight = w_s + w_c + w_x
    if total_weight == 0:
        return 0
    weighted_avg = (struct*w_s + cost*w_c + compl*w_x) / total_weight
    return int(weighted_avg)

# ------------------------------------------------------------
# Evolution loop
# ------------------------------------------------------------

def run_evolutionary_loop(btype: str, bedrooms: int, generations: int,
                          pop_size: int, config: dict) -> Tuple[Design, List[int]]:
    population = [generate_base_design(btype, bedrooms) for _ in range(pop_size)]
    history = []
    elitism_count = max(1, int(pop_size * config.get("elitism_frac", 0.4)))
    weights = config.get("fitness_weights", {})

    for g in range(generations):
        # score
        for d in population:
            fit = calculate_fitness(d, config)
            d.fitness = fit
            d.score = calculate_aggregate_score(fit, weights)
        population.sort(key=lambda d: d.score, reverse=True)
        history.append(population[0].score)

        new_generation = population[:elitism_count]
        while len(new_generation) < pop_size:
            if config.get("crossover_enabled") and len(population) >= 2:
                parent1 = random.choice(population[:max(2, pop_size//2)])
                parent2 = random.choice(population[:max(2, pop_size//2)])
                child = crossover_designs(parent1, parent2)
                child = mutate_design(child, config)
                new_generation.append(child)
            else:
                parent = random.choice(population[:max(2, pop_size//2)])
                child = mutate_design(parent, config)
                new_generation.append(child)
        population = new_generation[:pop_size]

    # final scoring
    for d in population:
        fit = calculate_fitness(d, config)
        d.fitness = fit
        d.score = calculate_aggregate_score(fit, weights)
    best = max(population, key=lambda d: d.score)
    return best, history

# ------------------------------------------------------------
# BSP Floor Plan Generator (with adjacency optimisation)
# ------------------------------------------------------------

class BSPNode:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.left = None
        self.right = None
        self.room = None   # room name

def split_node(node: BSPNode, horizontal: bool = True):
    if horizontal:
        split = node.w // 2
        node.left = BSPNode(node.x, node.y, split, node.h)
        node.right = BSPNode(node.x + split, node.y, node.w - split, node.h)
    else:
        split = node.h // 2
        node.left = BSPNode(node.x, node.y, node.w, split)
        node.right = BSPNode(node.x, node.y + split, node.w, node.h - split)

def build_bsp_tree(node: BSPNode, depth: int, max_depth: int):
    if depth >= max_depth:
        return
    horizontal = (depth % 2 == 0)
    if (horizontal and node.w < 100) or (not horizontal and node.h < 100):
        return
    split_node(node, horizontal)
    build_bsp_tree(node.left, depth+1, max_depth)
    build_bsp_tree(node.right, depth+1, max_depth)

def collect_leaves(node: BSPNode, leaves: List[BSPNode]):
    if node.left is None and node.right is None:
        leaves.append(node)
    else:
        if node.left:
            collect_leaves(node.left, leaves)
        if node.right:
            collect_leaves(node.right, leaves)

def assign_rooms_to_leaves(leaves: List[BSPNode], rooms: List[str]):
    random.shuffle(rooms)
    for i, leaf in enumerate(leaves):
        leaf.room = rooms[i] if i < len(rooms) else "Corridor"

# Adjacency preference matrix
ADJACENCY = {
    "Living Room":       {"Gourmet Kitchen": 3, "Flex Space": 2},
    "Gourmet Kitchen":   {"Living Room": 3, "Flex Space": 2},
    "Primary Bathroom":  {"Master Bedroom": 3, "Bedroom": 2},
    "Bedroom":           {"Primary Bathroom": 3, "Master Bedroom": 2},
    "Master Bedroom":    {"Primary Bathroom": 3, "Bedroom": 2},
    "Flex Space":        {"Living Room": 2, "Gourmet Kitchen": 2},
}

def neighbour_score(a: BSPNode, b: BSPNode) -> int:
    if not a.room or not b.room:
        return 0
    s = ADJACENCY.get(a.room, {}).get(b.room, 0)
    s += ADJACENCY.get(b.room, {}).get(a.room, 0)
    return s

def optimise_adjacency(leaves: List[BSPNode], iterations: int = 200) -> None:
    """Greedy swap to improve adjacency of preferred room neighbours."""
    # Build neighbour pairs (touching rectangles)
    neighbours = {i: [] for i in range(len(leaves))}
    for i, a in enumerate(leaves):
        for j, b in enumerate(leaves):
            if i >= j:
                continue
            # Check axis-aligned adjacency (sharing a boundary)
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

def generate_floor_plan_ai(design: Design, canvas_width=800, canvas_height=500) -> List[Dict]:
    rooms_raw = design.rooms[:]
    for i in range(design.bedrooms):
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

    while len(leaves) < num_rooms and depth < 10:
        depth += 1
        root = BSPNode(0, 0, canvas_width, canvas_height)
        build_bsp_tree(root, 0, depth)
        leaves = []
        collect_leaves(root, leaves)

    assign_rooms_to_leaves(leaves, rooms_raw)
    optimise_adjacency(leaves)   # 🔥 the new adjacency optimisation

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
# Structural diagnostics & material takeoffs
# ------------------------------------------------------------

def run_structural_review(design: Design, config: dict) -> List[Tuple[str, str]]:
    alerts = []
    if design.structure["columns"] < 16:
        alerts.append(("danger", "🔴 Structural Warning: Column density too low for load transfer."))
    if design.cost / design.area_sqm > config["target_cost_per_sqm"] * 1.4:
        alerts.append(("warning", "🟡 Financial Alert: Cost per sqm exceeds target threshold."))
    if design.structure["beams"] / design.structure["columns"] < config["ideal_beam_col_ratio"] * 0.9:
        alerts.append(("info", "🔵 Framing Optimization: Beam-column ratio lower than ideal."))
    if not alerts:
        alerts.append(("success", "🟢 Synthesis Checked: Structural logic matrices clear."))
    return alerts

def calculate_material_takeoffs(design: Design) -> List[Dict]:
    return [
        {"Structural Asset Item": "High-Performance Concrete Pour", "Calculated Takeoff": f"{design.structure['columns'] * 2.6:.1f} m³"},
        {"Structural Asset Item": "Tensile Steel Rebar Skeleton", "Calculated Takeoff": f"{design.structure['beams'] * 0.48:.2f} Metric Tons"},
        {"Structural Asset Item": "Insulated Masonry CMU Blocks", "Calculated Takeoff": f"{int(design.area_sqm * 42):,} Structural Units"},
        {"Structural Asset Item": "Calculated Structural Dead Load Base", "Calculated Takeoff": f"{int(design.structure['columns'] * 13.2):,} kN"}
    ]