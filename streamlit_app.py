# streamlit_app.py
# =============================
# ARC STUDIO ENGINE – AEC/MEP SYNTHESIS
# Full-spectrum generator: Residential, Commercial, Industrial, Healthcare, Education, Hospitality
# MEP systems: HVAC, Electrical, Plumbing, Fire Protection, Lighting/Data
# Comparison mode, smarter layouts, cost estimates
# =============================

import streamlit as st
import math
import plotly.graph_objects as go
import random

st.set_page_config(page_title="AEC/MEP Studio", page_icon="🏗️", layout="wide")

# ---------- Custom styling ----------
st.markdown("""
<style>
    .stApp { background: #0b0f19; color: #e2e8f0; }
    h1,h2,h3 { font-family: 'Segoe UI', sans-serif; color: #f1f5f9; }
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;
        border: none; border-radius: 10px; padding: 0.6rem 1.8rem; font-weight: 600;
    }
    .metric-box {
        background: rgba(255,255,255,0.03); border: 1px solid #334155;
        border-radius: 12px; padding: 1rem; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Building Type Definitions ----------
BUILDING_CATEGORIES = {
    "Residential": {
        "subtypes": ["Apartment", "Villa", "Townhouse"],
        "room_types": ["Living Room", "Bedroom", "Bathroom", "Kitchen", "Dining"],
        "typical_area_range": (80, 300),
        "floor_height": 3.0
    },
    "Commercial": {
        "subtypes": ["Office", "Retail", "Restaurant"],
        "room_types": ["Open Office", "Meeting Room", "Reception", "Server Room", "Pantry"],
        "typical_area_range": (100, 1000),
        "floor_height": 3.5
    },
    "Industrial": {
        "subtypes": ["Factory", "Warehouse", "Workshop"],
        "room_types": ["Factory Floor", "Warehouse Bay", "Loading Dock", "Machine Room", "Office"],
        "typical_area_range": (200, 2000),
        "floor_height": 4.5
    },
    "Healthcare": {
        "subtypes": ["Hospital", "Clinic"],
        "room_types": ["Ward", "Operating Theatre", "Consultation Room", "Waiting Area", "Nurse Station"],
        "typical_area_range": (200, 1500),
        "floor_height": 3.6
    },
    "Education": {
        "subtypes": ["School", "University"],
        "room_types": ["Classroom", "Laboratory", "Library", "Auditorium", "Office"],
        "typical_area_range": (150, 1000),
        "floor_height": 3.6
    },
    "Hospitality": {
        "subtypes": ["Hotel", "Restaurant"],
        "room_types": ["Guest Room", "Lobby", "Restaurant", "Kitchen", "Meeting Room"],
        "typical_area_range": (100, 800),
        "floor_height": 3.0
    }
}

# ---------- MEP System Definitions ----------
MEP_SYSTEMS = {
    "HVAC": {"color_2d": "#f59e0b", "color_3d": "gold", "line_style": "solid"},
    "Electrical": {"color_2d": "#3b82f6", "color_3d": "cyan", "line_style": "dashed"},
    "Plumbing": {"color_2d": "#22c55e", "color_3d": "lime", "line_style": "dotted"},
    "Fire Protection": {"color_2d": "#ef4444", "color_3d": "red", "line_style": "dashdot"},
    "Lighting/Data": {"color_2d": "#a855f7", "color_3d": "magenta", "line_style": "dashed"}
}

ROOM_COLORS_2D = {
    "Living Room": "#1e3a8a", "Bedroom": "#4c1d95", "Bathroom": "#78350f",
    "Kitchen": "#b45309", "Dining": "#0f766e",
    "Open Office": "#064e3b", "Meeting Room": "#0e7490", "Reception": "#1e40af",
    "Server Room": "#312e81", "Pantry": "#9a3412",
    "Factory Floor": "#475569", "Warehouse Bay": "#334155", "Loading Dock": "#1e293b",
    "Machine Room": "#0f172a", "Office": "#064e3b",
    "Retail Space": "#8b5cf6", "Apartment": "#4c1d95",
    "Ward": "#2563eb", "Operating Theatre": "#0e7490", "Consultation Room": "#0891b2",
    "Waiting Area": "#6366f1", "Nurse Station": "#7c3aed",
    "Classroom": "#047857", "Laboratory": "#0d9488", "Library": "#6d28d9",
    "Auditorium": "#b91c1c", "Guest Room": "#a21caf", "Lobby": "#c026d3",
    "Restaurant": "#b45309", "Corridor": "#6b7280", "Stair/Elev Core": "#4b5563",
    "Storage": "#78716c"
}

ROOM_COLORS_3D = {
    "Living Room": "blue", "Bedroom": "purple", "Bathroom": "orange",
    "Kitchen": "brown", "Dining": "teal",
    "Open Office": "green", "Meeting Room": "cyan", "Reception": "navy",
    "Server Room": "indigo", "Pantry": "chocolate",
    "Factory Floor": "gray", "Warehouse Bay": "darkslategray", "Loading Dock": "black",
    "Machine Room": "darkgray", "Office": "green",
    "Retail Space": "violet", "Apartment": "purple",
    "Ward": "blue", "Operating Theatre": "teal", "Consultation Room": "skyblue",
    "Waiting Area": "cornflowerblue", "Nurse Station": "mediumpurple",
    "Classroom": "forestgreen", "Laboratory": "mediumseagreen", "Library": "indigo",
    "Auditorium": "firebrick", "Guest Room": "mediumorchid", "Lobby": "orchid",
    "Restaurant": "chocolate", "Corridor": "lightgray", "Stair/Elev Core": "darkgray",
    "Storage": "darkkhaki"
}

# ---------- Building Generator ----------
def generate_building(building_type, floors, area_per_floor, rooms_per_floor, hvac_type,
                      add_core=True, include_mep_layers=None):
    """Creates a multi‑floor building with rooms, MEP zones and structural elements."""
    if include_mep_layers is None:
        include_mep_layers = list(MEP_SYSTEMS.keys())

    # Determine category and base parameters
    category = None
    for cat, info in BUILDING_CATEGORIES.items():
        if building_type in info["subtypes"]:
            category = cat
            floor_height = info["floor_height"]
            break
    if category is None:
        category = "Mixed-Use"
        floor_height = 3.3
    room_pool = BUILDING_CATEGORIES[category]["room_types"]

    building = {
        "floors": floors,
        "area_per_floor": area_per_floor,
        "floor_height": floor_height,
        "rooms_per_floor": rooms_per_floor,
        "hvac": hvac_type,
        "type": building_type,
        "floors_data": []
    }

    for f in range(floors):
        # Floor shape – industrial tends elongated, others more square
        if category == "Industrial":
            width = math.sqrt(area_per_floor) * 1.5
            depth = area_per_floor / width
        else:
            width = math.sqrt(area_per_floor)
            depth = area_per_floor / width

        # Create a central circulation corridor (2 m wide) for non‑industrial
        if category != "Industrial" and add_core:
            corridor_y = depth / 2 - 1.0  # horizontal corridor
            corridor_h = 2.0
        else:
            corridor_y = None
            corridor_h = 0

        # Partition rooms around corridor
        rooms = []
        room_counter = 0
        # Divide the floor into two zones (above and below corridor) if present
        zones = []
        if corridor_y is not None:
            zones.append({"y": 0, "h": corridor_y})          # upper zone
            zones.append({"y": corridor_y + corridor_h, "h": depth - corridor_y - corridor_h})  # lower zone
        else:
            zones.append({"y": 0, "h": depth})

        # Distribute rooms roughly equally across zones
        rooms_zone0 = rooms_per_floor // len(zones)
        for z_idx, zone in enumerate(zones):
            cols = math.ceil(math.sqrt(rooms_zone0 if z_idx == 0 else rooms_per_floor - rooms_zone0))
            rows = math.ceil((rooms_zone0 if z_idx == 0 else rooms_per_floor - rooms_zone0) / cols)
            cell_w = width / cols
            cell_d = zone["h"] / rows
            for r in range(rows):
                for c in range(cols):
                    if room_counter >= rooms_per_floor:
                        break
                    room_type = room_pool[room_counter % len(room_pool)]
                    x = c * cell_w
                    y = zone["y"] + r * cell_d
                    rooms.append({
                        "name": f"{room_type} {room_counter+1}",
                        "x": x, "y": y,
                        "width": cell_w, "depth": cell_d,
                        "type": room_type
                    })
                    room_counter += 1

        # Add corridor and stair/elevator core if multi-storey
        if corridor_y is not None:
            rooms.append({
                "name": "Corridor",
                "x": 0, "y": corridor_y,
                "width": width, "depth": corridor_h,
                "type": "Corridor"
            })
            if floors > 1:
                core_x = width / 2 - 1.0
                core_y = depth / 2 - 1.0
                rooms.append({
                    "name": "Stair/Elev Core",
                    "x": core_x, "y": core_y,
                    "width": 2.0, "depth": 2.0,
                    "type": "Stair/Elev Core"
                })

        # MEP generation
        mep_zones = []
        main_trunk_x = width / 2 - 0.5   # HVAC main
        for sys_name in include_mep_layers:
            sys_info = MEP_SYSTEMS[sys_name]
            if sys_name == "HVAC":
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {"points": [[main_trunk_x, 0, 0.2], [main_trunk_x, depth, 0.2]], "size": 0.4}
                })
            elif sys_name == "Electrical":
                # perimeter ring
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {"points": [[0.5, 0, 0.15], [0.5, depth, 0.15], [width-0.5, depth, 0.15], [width-0.5, 0, 0.15]], "size": 0.15}
                })
            elif sys_name == "Plumbing":
                # supply risers
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {"points": [[width/3, 0, 0.1], [width/3, depth, 0.1], [2*width/3, depth, 0.1], [2*width/3, 0, 0.1]], "size": 0.2}
                })
            elif sys_name == "Fire Protection":
                # loop near ceiling
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Loop",
                    "geometry": {"points": [[1, 1, 0.3], [width-1, 1, 0.3], [width-1, depth-1, 0.3], [1, depth-1, 0.3], [1, 1, 0.3]], "size": 0.1}
                })
            elif sys_name == "Lighting/Data":
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Bus",
                    "geometry": {"points": [[width/4, 0, 0.25], [width/4, depth, 0.25], [3*width/4, depth, 0.25], [3*width/4, 0, 0.25]], "size": 0.1}
                })

        # Branch connections for HVAC and electrical to each room
        for room in rooms:
            if room["type"] in ["Corridor", "Stair/Elev Core"]:
                continue
            cx = room["x"] + room["width"]/2
            cy = room["y"] + room["depth"]/2
            if "HVAC" in include_mep_layers:
                mep_zones.append({
                    "system": "HVAC",
                    "type": "Branch Duct",
                    "geometry": {"points": [[main_trunk_x, cy, 0.2], [cx, cy, 0.2]], "size": 0.15}
                })
            if "Electrical" in include_mep_layers:
                mep_zones.append({
                    "system": "Electrical",
                    "type": "Branch Conduit",
                    "geometry": {"points": [[cx, room["y"], 0.15], [cx, room["y"]+room["depth"], 0.15]], "size": 0.1}
                })
            if "Plumbing" in include_mep_layers and room["type"] in ["Bathroom", "Kitchen", "Pantry"]:
                mep_zones.append({
                    "system": "Plumbing",
                    "type": "Branch Pipe",
                    "geometry": {"points": [[room["x"], cy, 0.1], [room["x"]+room["width"], cy, 0.1]], "size": 0.1}
                })
            if "Fire Protection" in include_mep_layers:
                mep_zones.append({
                    "system": "Fire Protection",
                    "type": "Sprinkler Drop",
                    "geometry": {"points": [[cx, cy, 0.3], [cx, cy, 0.15]], "size": 0.05}
                })
            if "Lighting/Data" in include_mep_layers:
                mep_zones.append({
                    "system": "Lighting/Data",
                    "type": "Data Point",
                    "geometry": {"points": [[cx, cy, 0.25], [cx, cy, 0.1]], "size": 0.05}
                })

        # Structural columns (5 m grid)
        columns = []
        col_spacing = 5
        for x in range(0, int(width)+1, col_spacing):
            for y in range(0, int(depth)+1, col_spacing):
                columns.append({"x": x, "y": y, "size": 0.3})

        building["floors_data"].append({
            "floor_num": f+1,
            "width": width,
            "depth": depth,
            "rooms": rooms,
            "mep_zones": mep_zones,
            "columns": columns,
            "elevation": f * floor_height
        })

    return building

# ---------- 2D SVG Renderer ----------
def render_2d_floor(floor_data):
    w = floor_data["width"] * 50
    d = floor_data["depth"] * 50
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {d}" style="background:#0f172a; width:100%; height:auto;">'
    # Grid
    for x in range(0, int(w), 50):
        svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{d}" stroke="#1e293b" stroke-width="0.5"/>'
    for y in range(0, int(d), 50):
        svg += f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="#1e293b" stroke-width="0.5"/>'

    # Columns
    for col in floor_data.get("columns", []):
        cx = col["x"] * 50
        cy = col["y"] * 50
        r = 2.5
        svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#64748b" opacity="0.6"/>'

    # Rooms
    for room in floor_data["rooms"]:
        rx = room["x"] * 50
        ry = room["y"] * 50
        rw = room["width"] * 50
        rd = room["depth"] * 50
        color = ROOM_COLORS_2D.get(room["type"], "#334155")
        svg += f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rd}" fill="{color}" fill-opacity="0.3" stroke="#94a3b8" stroke-width="2"/>'
        # Room name and area
        area_approx = room["width"] * room["depth"]
        svg += f'<text x="{rx+rw/2}" y="{ry+rd/2-6}" font-size="9" fill="white" text-anchor="middle">{room["name"]}</text>'
        svg += f'<text x="{rx+rw/2}" y="{ry+rd/2+8}" font-size="8" fill="#cbd5e1" text-anchor="middle">{area_approx:.0f} m²</text>'

    # MEP lines (by system)
    for zone in floor_data["mep_zones"]:
        sys_info = MEP_SYSTEMS[zone["system"]]
        color = sys_info["color_2d"]
        dash = "4" if sys_info["line_style"] == "dashed" else ("2,2" if sys_info["line_style"] == "dotted" else ("8,4" if sys_info["line_style"] == "dashdot" else "none"))
        pts = zone["geometry"]["points"]
        for i in range(len(pts)-1):
            x1, y1 = pts[i][0]*50, pts[i][1]*50
            x2, y2 = pts[i+1][0]*50, pts[i+1][1]*50
            svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.5" stroke-dasharray="{dash}"/>'
    svg += '</svg>'
    return svg

# ---------- 3D Plotly Renderer ----------
def render_3d_building(building):
    fig = go.Figure()

    for floor in building["floors_data"]:
        z_base = floor["elevation"]
        z_top = z_base + building["floor_height"]
        w = floor["width"]
        d = floor["depth"]

        # Floor slab (semi-transparent)
        fig.add_trace(go.Mesh3d(
            x=[0, w, w, 0], y=[0, 0, d, d], z=[z_base]*4,
            color='lightgray', opacity=0.15, flatshading=True, showlegend=False
        ))

        # Rooms
        for room in floor["rooms"]:
            x0, y0 = room["x"], room["y"]
            x1, y1 = x0 + room["width"], y0 + room["depth"]
            fig.add_trace(go.Mesh3d(
                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                z=[z_base]*4 + [z_top]*4,
                color=ROOM_COLORS_3D.get(room["type"], "gray"),
                opacity=0.7, flatshading=True,
                name=room["name"], showlegend=False
            ))

        # Columns
        for col in floor.get("columns", []):
            xc, yc = col["x"], col["y"]
            size = col["size"]
            fig.add_trace(go.Scatter3d(
                x=[xc, xc], y=[yc, yc], z=[z_base, z_top],
                mode='lines', line=dict(color='darkgray', width=4),
                showlegend=False
            ))

        # MEP lines
        mep_colors_3d = {sys: info["color_3d"] for sys, info in MEP_SYSTEMS.items()}
        for zone in floor["mep_zones"]:
            color = mep_colors_3d.get(zone["system"], "white")
            pts = zone["geometry"]["points"]
            for i in range(len(pts)-1):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[i+1]
                z_abs1 = z_base + z1
                z_abs2 = z_base + z2
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z_abs1, z_abs2],
                    mode='lines', line=dict(color=color, width=3),
                    showlegend=False
                ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor="#0b0f19", gridcolor="#1e293b"),
            yaxis=dict(title='Y (m)', backgroundcolor="#0b0f19", gridcolor="#1e293b"),
            zaxis=dict(title='Z (m)', backgroundcolor="#0b0f19", gridcolor="#1e293b"),
            aspectmode='data'
        ),
        paper_bgcolor="#0b0f19",
        margin=dict(l=0, r=0, b=0, t=30),
    )
    return fig

# ---------- Cost Estimation ----------
def estimate_cost(building):
    """Rough cost estimate based on area and type."""
    category = None
    for cat, info in BUILDING_CATEGORIES.items():
        if building["type"] in info["subtypes"]:
            category = cat
            break
    rates = {
        "Residential": 1500, "Commercial": 2000, "Industrial": 1200,
        "Healthcare": 2500, "Education": 1800, "Hospitality": 1900
    }
    rate = rates.get(category, 1600)
    total_area = building["floors"] * building["area_per_floor"]
    base_cost = total_area * rate
    hvac_adder = {"VAV": 1.1, "VRF": 1.15, "Chilled Beams": 1.25, "Split DX": 1.05, "Packaged Rooftop": 1.0}
    multiplier = hvac_adder.get(building["hvac"], 1.0)
    return base_cost * multiplier

# ---------- User Interface ----------
st.title("🏗️ AEC/MEP Building Synthesizer")
st.markdown("Design residential, commercial, industrial, healthcare, education, and hospitality buildings with full MEP coordination.")

with st.sidebar:
    st.header("Design Parameters")
    building_category = st.selectbox("Category", list(BUILDING_CATEGORIES.keys()))
    building_subtype = st.selectbox("Type", BUILDING_CATEGORIES[building_category]["subtypes"])

    floors = st.slider("Floors", 1, 15, 2)
    min_area, max_area = BUILDING_CATEGORIES[building_category]["typical_area_range"]
    area_per_floor = st.slider("Area per Floor (m²)", min_area, max_area, (min_area+max_area)//2)
    rooms_per_floor = st.slider("Rooms per Floor", 2, 20, 6)
    hvac_type = st.selectbox("HVAC System", ["VAV", "VRF", "Chilled Beams", "Split DX", "Packaged Rooftop"])

    with st.expander("MEP Layers", expanded=False):
        all_mep = list(MEP_SYSTEMS.keys())
        selected_mep = [sys for sys in all_mep if st.checkbox(sys, value=(sys != "Fire Protection"))]

    add_core = st.checkbox("Include corridor & core", value=True)

    st.markdown("---")
    generate_btn = st.button("Generate Building A", use_container_width=True)
    compare_mode = st.checkbox("Enable design comparison")
    if compare_mode:
        generate_btn_b = st.button("Generate Building B", use_container_width=True)

if generate_btn:
    building_a = generate_building(building_subtype, floors, area_per_floor, rooms_per_floor,
                                   hvac_type, add_core, selected_mep)
    st.session_state["building_a"] = building_a
if compare_mode and generate_btn_b:
    building_b = generate_building(building_subtype, floors, area_per_floor, rooms_per_floor,
                                   hvac_type, add_core, selected_mep)
    st.session_state["building_b"] = building_b

# Display Building A
if "building_a" in st.session_state:
    building = st.session_state["building_a"]
    with st.container():
        st.subheader("🏢 Building A")
        show_building(building, "A")
        if "building_b" in st.session_state:
            st.markdown("---")
            st.subheader("🏢 Building B (Comparison)")
            show_building(st.session_state["building_b"], "B")

elif "building_b" in st.session_state:
    st.info("Generate Building A first to enable comparison.") if compare_mode else None

def show_building(building, label):
    st.success(f"Building {label}: {building['floors']}‑storey {building['type']}, HVAC: {building['hvac']}")
    floor_choice = st.selectbox(f"Select Floor ({label})", [f"Floor {i+1}" for i in range(building["floors"])], key=f"floor_{label}")
    floor_idx = int(floor_choice.split()[-1]) - 1
    floor_data = building["floors_data"][floor_idx]

    col2d, col3d = st.columns(2)
    with col2d:
        st.subheader(f"2D Plan – {floor_choice}")
        svg = render_2d_floor(floor_data)
        st.markdown(f'<div style="border:1px solid #334155; border-radius:8px; overflow:hidden;">{svg}</div>', unsafe_allow_html=True)
        st.caption("MEP: gold=HVAC, blue=Elec, green=Plumb, red=Fire, purple=Lighting")
    with col3d:
        st.subheader("3D Model")
        fig3d = render_3d_building(building)
        st.plotly_chart(fig3d, use_container_width=True)

    # Metrics
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    total_area = building["floors"] * building["area_per_floor"]
    c1.metric("Total Area", f"{total_area} m²")
    c2.metric("Columns", sum(len(fd["columns"]) for fd in building["floors_data"]))
    c3.metric("Cost Estimate", f"${estimate_cost(building):,.0f}")
    c4.metric("Rooms total", sum(len(fd["rooms"]) for fd in building["floors_data"]))
