# engineering.py
# Structural engineering calculations – Eurocodes & general standards
import math
from typing import Dict, Any, List, Tuple

# =============================
# UNIT CONVERSION
# =============================
def to_metric(value: float, unit: str) -> float:
    """Convert from imperial to metric (SI)."""
    conversions = {
        "ft": 0.3048,
        "in": 0.0254,
        "kip": 4.44822,
        "lb": 0.00444822,
        "psi": 0.00689476,
        "psf": 0.0478803,
        "kips-ft": 1.35582,
    }
    return value * conversions.get(unit, 1.0)

def to_imperial(value: float, unit: str) -> float:
    """Convert from SI to imperial."""
    conversions = {
        "ft": 3.28084,
        "in": 39.3701,
        "kip": 0.224809,
        "lb": 224.809,
        "psi": 145.038,
        "psf": 20.8854,
        "kips-ft": 0.737562,
    }
    return value * conversions.get(unit, 1.0)

# =============================
# MATERIAL DATABASES
# =============================
CONCRETE_GRADES = {
    "C20/25": {"fck": 20.0, "fcd": 20.0 / 1.5, "Ecm": 30e9},
    "C25/30": {"fck": 25.0, "fcd": 25.0 / 1.5, "Ecm": 31e9},
    "C30/37": {"fck": 30.0, "fcd": 30.0 / 1.5, "Ecm": 33e9},
    "C35/45": {"fck": 35.0, "fcd": 35.0 / 1.5, "Ecm": 34e9},
}

STEEL_GRADES = {
    "S235": {"fy": 235e6, "fyd": 235e6/1.0, "Es": 210e9},
    "S275": {"fy": 275e6, "fyd": 275e6/1.0, "Es": 210e9},
    "S355": {"fy": 355e6, "fyd": 355e6/1.0, "Es": 210e9},
}

TIMBER_CLASSES = {
    "C24": {"fm_k": 24e6, "fv_k": 2.5e6, "E0_mean": 11e9, "gammaM": 1.3},
    "GL24h": {"fm_k": 24e6, "fv_k": 2.7e6, "E0_mean": 11.6e9, "gammaM": 1.25},
}

WALL_TYPES = {
    "Brick – 230mm": {"weight": 2.5, "U": 1.5, "sound": 45},
    "Brick – 350mm": {"weight": 3.8, "U": 1.1, "sound": 50},
    "Concrete block – 200mm": {"weight": 2.8, "U": 2.0, "sound": 40},
    "Timber frame – 140mm": {"weight": 0.8, "U": 0.35, "sound": 35},
}

FINISHES = {
    "Plaster (internal)": 0.02,   # kN/m²
    "Cladding (external)": 0.15,
    "Paint": 0.005,
    "Tiles": 0.6,
    "Insulation (100mm)": 0.04,
}

DEFAULT_COSTS = {
    "concrete_per_m2": 250,
    "steel_per_m": 50,
    "glass_per_m2": 150,
    "labor_per_m2": 100,
}

# =============================
# LOAD COMBINATIONS (Eurocode 0)
# =============================
def uls_combination(dead: float, live: float, snow: float = 0, wind: float = 0) -> float:
    """ULS (STR) combination: 1.35*G + 1.5*Q + 1.5*ψ0*S/W"""
    return 1.35 * dead + 1.5 * live + 1.5 * 0.7 * (snow + wind)

def sls_combination(dead: float, live: float) -> float:
    """SLS characteristic combination: G + Q"""
    return dead + live

# =============================
# BEAM CHECKS
# =============================
def check_rc_beam(b: float, h: float, d: float, fck: float, M_ed: float, V_ed: float, span: float) -> dict:
    """Reinforced concrete beam check to EC2."""
    fcd = fck / 1.5
    k = M_ed / (b * d**2 * fcd)
    if k > 0.167:
        return {"pass": False, "warning": "Compression reinforcement required (k>0.167)."}
    z = d * (0.5 + math.sqrt(0.25 - k/1.134))
    As_req = M_ed / (0.87 * 500e6 * z) * 1e4  # cm²
    # Shear check
    v_ed = V_ed / (b * d)
    v_rdc = 0.12 * (1 + math.sqrt(200/d)) * (100 * As_req*1e-4 / (b*d))**(1/3) * fck**(1/3)
    pass_shear = v_ed <= v_rdc
    allowable = 20
    actual = span / d
    return {
        "pass": k <= 0.167 and pass_shear and actual <= allowable,
        "As_req": round(As_req, 2),
        "k": round(k, 3),
        "v_ed": round(v_ed/1e6, 2),
        "v_rdc": round(v_rdc/1e6, 2),
        "span_depth": round(actual, 1),
    }

def check_steel_beam(section: str, M_ed: float, V_ed: float, span: float, steel: dict) -> dict:
    """Steel beam check to EC3 (simplified)."""
    fy = steel["fy"]
    sections = {
        "IPE 160": {"Wpl": 124e3, "Av": 9.66e2, "I": 869e4},
        "IPE 220": {"Wpl": 285e3, "Av": 15.9e2, "I": 2772e4},
        "IPE 300": {"Wpl": 628e3, "Av": 25.7e2, "I": 8356e4},
    }
    if section not in sections:
        return {"pass": False, "error": "Section not in database."}
    prop = sections[section]
    M_rd = prop["Wpl"] * fy / 1.0
    V_rd = prop["Av"] * (fy/math.sqrt(3)) / 1.0
    delta = 5 * M_ed * span**2 / (48 * steel["Es"] * prop["I"]) * 1e3  # mm
    pass_deflection = delta <= span*1e3/360
    return {
        "pass": M_ed <= M_rd and V_ed <= V_rd and pass_deflection,
        "M_rd": round(M_rd/1e6, 2),
        "V_rd": round(V_rd/1e3, 2),
        "utilization": round(max(M_ed/M_rd, V_ed/V_rd), 2) if M_rd else 0,
        "deflection_mm": round(delta, 1),
    }

# =============================
# COLUMN CHECK
# =============================
def check_rc_column(N_ed: float, M_ed: float, b: float, h: float, fck: float, l0: float) -> dict:
    """Simplified RC column check (EC2)."""
    fcd = fck / 1.5
    A = b * h
    N_rd = 0.567 * fck * A / 1.5
    slenderness = l0 / min(b, h)
    limit = 25
    return {
        "pass": N_ed <= N_rd and slenderness <= limit,
        "N_rd": round(N_rd/1e3, 1),
        "slenderness": round(slenderness, 1),
    }

# =============================
# SLAB & FOUNDATION
# =============================
def slab_thickness_estimate(span: float, support_condition="simply_supported") -> float:
    ratios = {"simply_supported": 20, "continuous": 26}
    return span / ratios.get(support_condition, 24)

def foundation_size(bearing_capacity: float, total_load: float, safety=3.0) -> dict:
    req_area = total_load * safety / bearing_capacity
    side = math.sqrt(req_area)
    return {"side_m": round(side, 2), "area_m2": round(req_area, 2)}

# =============================
# OLD FUNCTIONS (for backward compatibility)
# =============================
def calculate_total_area(plan: List[Dict]) -> float:
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
    total_area_m2 = calculate_total_area(plan)
    dead_load_kN = total_area_m2 * (24.0 * slab_thickness_m + additional_dead_load_kN_per_m2)
    live_load_kN = total_area_m2 * live_load_kN_per_m2
    return dead_load_kN + live_load_kN

def check_structural_integrity(plan: List[Dict]) -> Dict[str, Any]:
    max_span_m = 0.0
    for room in plan:
        diag = math.sqrt(room["w"]**2 + room["h"]**2) / 1000
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
    total_wall_area = 0.0
    for room in plan:
        perim = 2 * (room["w"] + room["h"]) / 1000
        wall_area = perim * 2.7
        total_wall_area += wall_area
    orient_factor = 1.1 if orientation == "south" else 0.95
    base_efficiency = 50 + (glazing_ratio * 100)
    return round(min(95, base_efficiency * orient_factor), 1)

def estimate_cost(plan: List[Dict], costs: dict = None) -> Dict[str, float]:
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

# =============================
# PILE FOUNDATION (simplified, EC7)
# =============================
def pile_capacity(diameter, length, soil_type="sand", N_value=20, safety=2.5):
    import math
    if soil_type == "sand":
        fs = 2 * N_value
        qb = 50 * N_value
    elif soil_type == "clay":
        fs = 5 * N_value
        qb = 30 * N_value
    else:
        fs = 2 * N_value
        qb = 30 * N_value
    As = math.pi * diameter * length
    Ab = math.pi * (diameter / 2) ** 2
    Q_ult = fs * As + qb * Ab
    Q_all = Q_ult / safety
    return {"Q_ult_kN": round(Q_ult, 1), "Q_all_kN": round(Q_all, 1),
            "shaft_kN": round(fs * As, 1), "base_kN": round(qb * Ab, 1)}

def check_prestressed_beam(M_ext, P, e, A, I, y_top, y_bot, fck):
    P_N = P * 1e3
    M_ext_Nmm = M_ext * 1e6
    A_mm2 = A * 1e6
    I_mm4 = I * 1e12
    e_mm = e * 1e3
    y_top_mm = y_top * 1e3
    y_bot_mm = y_bot * 1e3
    sigma_top = -P_N/A_mm2 + (P_N * e_mm * y_top_mm)/I_mm4 - (M_ext_Nmm * y_top_mm)/I_mm4
    sigma_bot = -P_N/A_mm2 - (P_N * e_mm * y_bot_mm)/I_mm4 + (M_ext_Nmm * y_bot_mm)/I_mm4
    fctm = 0.3 * fck ** (2/3)
    sigma_c_allow = 0.6 * fck
    sigma_t_allow = fctm
    top_ok = abs(sigma_top) <= sigma_c_allow if sigma_top < 0 else sigma_top <= sigma_t_allow
    bot_ok = abs(sigma_bot) <= sigma_c_allow if sigma_bot < 0 else sigma_bot <= sigma_t_allow
    return {"sigma_top_MPa": round(sigma_top, 2), "sigma_bot_MPa": round(sigma_bot, 2),
            "sigma_c_allow": round(sigma_c_allow, 2), "sigma_t_allow": round(sigma_t_allow, 2),
            "pass": top_ok and bot_ok}

def generate_analysis_report(results_dict, filename="analysis_report.pdf"):
    try:
        from fpdf import FPDF
    except ImportError:
        return None, "Install fpdf2: pip install fpdf2"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "DRUM Studio - Structural Analysis Report", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for key, value in results_dict.items():
        if isinstance(value, dict):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"{key}:", ln=True)
            pdf.set_font("Arial", "", 11)
            for subkey, subval in value.items():
                pdf.cell(80, 7, f"  {subkey}: {subval}", ln=True)
        else:
            pdf.cell(0, 8, f"{key}: {value}", ln=True)
    pdf.output(filename)
    return filename, None

# =============================
# PRESTRESSED CONCRETE BEAM (simplified stress check)
# =============================
def check_prestressed_beam(M_ext, P, e, A, I, y_top, y_bot, fck):
    """
    Check stresses in a prestressed concrete beam at transfer and service.
    M_ext: external moment (kNm)
    P: prestressing force (kN) (after losses)
    e: eccentricity (m), positive if tendon below centroid
    A: cross-sectional area (m²)
    I: second moment of area (m⁴)
    y_top, y_bot: distances from centroid to top/bottom fibres (m)
    fck: concrete characteristic strength (MPa)
    Returns stresses (MPa) and check.
    """
    # Convert to N and mm
    P_N = P * 1e3
    M_ext_Nmm = M_ext * 1e6
    A_mm2 = A * 1e6
    I_mm4 = I * 1e12
    e_mm = e * 1e3
    y_top_mm = y_top * 1e3
    y_bot_mm = y_bot * 1e3
    fck_MPa = fck

    # Stress at top: sigma_top = -P/A + (P*e*y_top)/I - M_ext*y_top/I  (sign convention: compression negative)
    sigma_top = -P_N/A_mm2 + (P_N * e_mm * y_top_mm) / I_mm4 - (M_ext_Nmm * y_top_mm) / I_mm4
    sigma_bot = -P_N/A_mm2 - (P_N * e_mm * y_bot_mm) / I_mm4 + (M_ext_Nmm * y_bot_mm) / I_mm4

    # Allowable stresses (simplified)
    fctm = 0.3 * fck_MPa**(2/3)   # tensile strength approx.
    sigma_c_allow = 0.6 * fck_MPa  # compression limit
    sigma_t_allow = fctm           # tension limit (cracking)

    top_ok = abs(sigma_top) <= sigma_c_allow if sigma_top < 0 else sigma_top <= sigma_t_allow
    bot_ok = abs(sigma_bot) <= sigma_c_allow if sigma_bot < 0 else sigma_bot <= sigma_t_allow

    return {
        "sigma_top_MPa": round(sigma_top, 2),
        "sigma_bot_MPa": round(sigma_bot, 2),
        "sigma_c_allow": round(sigma_c_allow, 2),
        "sigma_t_allow": round(sigma_t_allow, 2),
        "pass": top_ok and bot_ok
    }

# =============================
# PDF REPORT GENERATION (using fpdf2)
# =============================
def generate_analysis_report(results_dict, filename="analysis_report.pdf"):
    """Generate a simple PDF report of analysis results."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None, "Install fpdf2: pip install fpdf2"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "DRUM Studio - Structural Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for key, value in results_dict.items():
        if isinstance(value, dict):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"{key}:", ln=True)
            pdf.set_font("Arial", "", 11)
            for subkey, subval in value.items():
                pdf.cell(80, 7, f"  {subkey}: {subval}", ln=True)
        else:
            pdf.cell(0, 8, f"{key}: {value}", ln=True)
    pdf.output(filename)
    return filename, None

# =============================
# RETAINING WALL (simplified Coulomb/Rankine)
# =============================
def retaining_wall_stability(H, gamma, phi, c=0, surcharge=0, wall_friction=0.6):
    """
    Simple cantilever retaining wall check.
    H: wall height (m), gamma: soil unit weight (kN/m³), phi: friction angle (°),
    c: cohesion (kPa), surcharge: kPa, wall_friction: base friction coefficient.
    Returns overturning and sliding safety factors.
    """
    import math
    phi_rad = math.radians(phi)
    Ka = (1 - math.sin(phi_rad)) / (1 + math.sin(phi_rad))  # Rankine active
    # Active earth pressure resultant
    Pa = 0.5 * gamma * H**2 * Ka + surcharge * H * Ka
    # Overturning moment about toe (assume triangular distribution)
    M_ot = Pa * H / 3
    # Resisting moment (weight of wall – assume T-shaped base for simplicity)
    # Simplified: assume wall weight = gamma_concrete * volume, base width B = 0.4*H
    B = 0.4 * H
    W_wall = 24 * (0.3 * H * 1.0 + B * 0.4 * 1.0)  # stem + base, 1m strip
    M_res = W_wall * B / 2
    F_overt = M_res / M_ot if M_ot > 0 else 999
    # Sliding
    R_sliding = W_wall * wall_friction
    F_sliding = R_sliding / Pa if Pa > 0 else 999
    return {
        "Pa_kN": round(Pa, 2),
        "M_ot_kNm": round(M_ot, 2),
        "M_res_kNm": round(M_res, 2),
        "F_overt": round(F_overt, 2),
        "F_sliding": round(F_sliding, 2),
        "pass": F_overt >= 1.5 and F_sliding >= 1.5
    }

# =============================
# TRUSS ANALYSIS (method of joints – simple 2D)
# =============================
def truss_method_of_joints(nodes, members, loads, supports):
    """
    Very simplified 2D truss solver (placeholder).
    nodes: list of (x,y) tuples
    members: list of (node_i, node_j) tuples
    loads: dict {node_i: (Fx, Fy)}
    supports: dict {node_i: ('pin'/'roller', direction)}
    Returns member forces (positive = tension).
    """
    # This is a placeholder – real implementation requires matrix solution.
    # For now, return a message.
    return {"status": "Truss solver not fully implemented – coming soon."}
