# engineering.py
# Structural analysis & costing for DRUM
import math
from typing import List, Dict, Any

# Constants for default materials (you can later add UI controls)
CONCRETE_COST_PER_M2 = 250   # $/m² for a 200mm slab
STEEL_COST_PER_M = 50        # $/m for a typical I‑beam
GLASS_COST_PER_M2 = 150      # $/m² for double‑glazed facade
LABOR_COST_PER_M2 = 100      # installation

def calculate_total_area(plan: List[Dict]) -> float:
    """Return total floor area of all rooms in m²."""
    # plan expects x,y,w,h in mm – convert to metres
    area = 0.0
    for room in plan:
        area += (room["w"] * room["h"]) / 1e6   # mm² → m²
    return area

def estimate_concrete_volume(plan: List[Dict], slab_thickness_m: float = 0.2) -> float:
    """Total concrete volume in m³."""
    return calculate_total_area(plan) * slab_thickness_m

def compute_floor_loads(plan: List[Dict], live_load_kN_per_m2: float = 2.5) -> float:
    """Dead + live load for the whole floor (kN)."""
    total_area_m2 = calculate_total_area(plan)
    dead_load_kN = total_area_m2 * 3.0   # assume 3 kN/m² self‑weight
    live_load_kN = total_area_m2 * live_load_kN_per_m2
    return dead_load_kN + live_load_kN

def check_structural_integrity(plan: List[Dict]) -> Dict[str, Any]:
    """
    Simple heuristic: check spans between columns (room centres).
    Returns a report with pass/fail and recommended beam sizes.
    """
    max_span_m = 0.0
    room_centers = []
    for room in plan:
        cx = room["x"] + room["w"] / 2
        cy = room["y"] + room["h"] / 2
        room_centers.append((cx, cy))

    # crude span calculation: longest distance between any two adjacent rooms
    # Here we just use the maximum diagonal length among all rooms as a proxy
    for room in plan:
        diag = math.sqrt(room["w"]**2 + room["h"]**2) / 1000  # mm → m
        max_span_m = max(max_span_m, diag)

    # Simple beam sizing table (IPE profiles)
    if max_span_m <= 4:
        beam = "IPE 160"
    elif max_span_m <= 6:
        beam = "IPE 220"
    elif max_span_m <= 8:
        beam = "IPE 300"
    else:
        beam = "IPE 400 – may need intermediate columns"

    safety_factor = max(1.0, 8.0 / max_span_m)  # simplistic
    return {
        "max_span_m": round(max_span_m, 2),
        "suggested_beam": beam,
        "safety_factor": round(safety_factor, 2),
        "pass": max_span_m <= 8   # arbitrary limit
    }

def calculate_energy_score(plan: List[Dict], orientation: str = "south") -> float:
    """
    Very rough estimate based on window ratio (we simulate windows as 20% of wall area).
    """
    total_wall_area = 0
    for room in plan:
        # perimeter of each room (assuming 2.7m floor height)
        perim = 2 * (room["w"] + room["h"]) / 1000  # m
        wall_area = perim * 2.7
        total_wall_area += wall_area

    # Assume 20% glazing ratio
    glazing_ratio = 0.2
    # South orientation gives 10% better performance
    orient_factor = 1.1 if orientation == "south" else 0.95
    base_efficiency = 50 + (glazing_ratio * 100)  # scale 50-90
    energy_score = min(95, base_efficiency * orient_factor)
    return round(energy_score, 1)

def estimate_cost(plan: List[Dict]) -> Dict[str, float]:
    """Return itemised cost in $."""
    total_area = calculate_total_area(plan)
    concrete_cost = total_area * CONCRETE_COST_PER_M2
    labor = total_area * LABOR_COST_PER_M2
    # approximate steel based on perimeter
    perimeter_m = sum(2 * (room["w"] + room["h"]) / 1000 for room in plan)
    steel_cost = perimeter_m * STEEL_COST_PER_M
    # glass = 20% of total wall area * glass cost
    wall_area = perimeter_m * 2.7
    glass_cost = wall_area * 0.2 * GLASS_COST_PER_M2

    total = concrete_cost + steel_cost + glass_cost + labor
    return {
        "concrete": round(concrete_cost, 2),
        "steel": round(steel_cost, 2),
        "glass": round(glass_cost, 2),
        "labor": round(labor, 2),
        "total": round(total, 2)
    }
