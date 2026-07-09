# engineering.py
# Structural analysis, costing, and energy evaluation for DRUM
import math
from typing import List, Dict, Any

DEFAULT_COSTS = {
    "concrete_per_m2": 250,   # $/m²
    "steel_per_m": 50,        # $/m
    "glass_per_m2": 150,      # $/m²
    "labor_per_m2": 100,      # $/m²
}

def calculate_total_area(plan: List[Dict]) -> float:
    """Total floor area in m² from plan (x,y,w,h in mm)."""
    area = 0.0
    for room in plan:
        area += (room["w"] * room["h"]) / 1e6
    return area

def compute_floor_loads(
    plan: List[Dict],
    live_load_kN_per_m2: float = 2.5,
    slab_thickness_m: float = 0.2,
    additional_dead_load_kN_per_m2: float = 1.0
) -> float:
    """Dead + live load for the whole floor (kN)."""
    total_area_m2 = calculate_total_area(plan)
    dead_load_kN = total_area_m2 * (24.0 * slab_thickness_m + additional_dead_load_kN_per_m2)
    live_load_kN = total_area_m2 * live_load_kN_per_m2
    return dead_load_kN + live_load_kN

def check_structural_integrity(plan: List[Dict]) -> Dict[str, Any]:
    """Max diagonal span → beam size recommendation."""
    max_span_m = 0.0
    for room in plan:
        diag = math.sqrt(room["w"]**2 + room["h"]**2) / 1000  # mm → m
        max_span_m = max(max_span_m, diag)

    if max_span_m <= 4:
        beam = "IPE 160"
    elif max_span_m <= 6:
        beam = "IPE 220"
    elif max_span_m <= 8:
        beam = "IPE 300"
    else:
        beam = "IPE 400 – may need intermediate columns"

    safety_factor = max(1.0, 8.0 / max_span_m)
    return {
        "max_span_m": round(max_span_m, 2),
        "suggested_beam": beam,
        "safety_factor": round(safety_factor, 2),
        "pass": max_span_m <= 8
    }

def calculate_energy_score(
    plan: List[Dict],
    orientation: str = "south",
    glazing_ratio: float = 0.2
) -> float:
    """Energy score based on glazing ratio and orientation."""
    total_wall_area = 0.0
    for room in plan:
        perim = 2 * (room["w"] + room["h"]) / 1000  # m
        wall_area = perim * 2.7
        total_wall_area += wall_area

    orient_factor = 1.1 if orientation == "south" else 0.95
    base_efficiency = 50 + (glazing_ratio * 100)
    energy_score = min(95, base_efficiency * orient_factor)
    return round(energy_score, 1)

def estimate_cost(plan: List[Dict], costs: dict = None) -> Dict[str, float]:
    """Itemised cost estimate."""
    if costs is None:
        costs = DEFAULT_COSTS

    total_area = calculate_total_area(plan)
    concrete_cost = total_area * costs["concrete_per_m2"]
    labor = total_area * costs["labor_per_m2"]

    perimeter_m = sum(2 * (room["w"] + room["h"]) / 1000 for room in plan)
    steel_cost = perimeter_m * costs["steel_per_m"]
    wall_area = perimeter_m * 2.7
    glass_cost = wall_area * 0.2 * costs["glass_per_m2"]

    total = concrete_cost + steel_cost + glass_cost + labor
    return {
        "concrete": round(concrete_cost, 2),
        "steel": round(steel_cost, 2),
        "glass": round(glass_cost, 2),
        "labor": round(labor, 2),
        "total": round(total, 2)
    }
