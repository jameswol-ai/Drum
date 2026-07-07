# streamlit_app.py
# =============================
# ARC STUDIO ENGINE – AEC/MEP SYNTHESIS
# Residential / Commercial / Industrial / Mixed-Use with full MEP (HVAC + Electrical + Plumbing)
# =============================

import streamlit as st
import math
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

# ---------- Building Type Definitions ----------
BUILDING_CATEGORIES = {
    "Residential": {
        "subtypes": ["Apartment", "Villa", "Townhouse"],
        "room_types": ["Living Room", "Bedroom", "Bathroom", "Kitchen", "Dining"],
        "typical_area_range": (80, 300),
    },
    "Commercial": {
        "subtypes": ["Office", "Retail", "Restaurant"],
        "room_types": ["Open Office", "Meeting Room", "Reception", "Server Room", "Pantry"],
        "typical_area_range": (100, 1000),
    },
    "Industrial": {
        "subtypes": ["Factory", "Warehouse", "Workshop"],
        "room_types": ["Factory Floor", "Warehouse Bay", "Loading Dock", "Machine Room", "Office"],
        "typical_area_range": (200, 2000),
    },
    "Mixed-Use": {
        "subtypes": ["Retail+Residential", "Office+Retail"],
        "room_types": ["Retail Space", "Office", "Apartment", "Corridor", "Storage"],
        "typical_area_range": (150, 800),
    }
}

# ---------- MEP System Definitions ----------
MEP_SYSTEMS = {
    "HVAC": {"color_2d": "#f59e0b", "color_3d": "gold", "line_style": "solid"},
    "Electrical": {"color_2d": "#3b82f6", "color_3d": "cyan", "line_style": "dashed"},
    "Plumbing": {"color_2d": "#22c55e", "color_3d": "lime", "line_style": "dotted"},
}

# ---------- Building Generator ----------
def generate_building(building_type, floors, area_per_floor, rooms_per_floor, hvac_type):
    """Creates a multi‑floor building with rooms, MEP zones and 3D data."""
    building = {
        "floors": floors,
        "area_per_floor": area_per_floor,
        "floor_height": 3.5 if building_type == "Industrial" else 3.0,  # higher ceilings for industrial
        "rooms_per_floor": rooms_per_floor,
        "hvac": hvac_type,
        "type": building_type,
        "floors_data": []
    }

    # Determine room types based on category
    category = None
    for cat, info in BUILDING_CATEGORIES.items():
        if building_type in info["subtypes"]:
            category = cat
            break
    if category is None:
        category = "Mixed-Use"
    room_pool = BUILDING_CATEGORIES[category]["room_types"]

    for f in range(floors):
        side = math.sqrt(area_per_floor)
        # Industrial buildings often elongated
        if category == "Industrial":
            width = side * 1.5
            depth = area_per_floor / width
        else:
            width = side
            depth = side

        cols = math.ceil(math.sqrt(rooms_per_floor))
        rows = math.ceil(rooms_per_floor / cols)
        cell_w = width / cols
        cell_d = depth / rows

        rooms = []
        room_counter = 0
        for r in range(rows):
            for c in range(cols):
                if room_counter >= rooms_per_floor:
                    break
                # Cycle through room pool
                room_type = room_pool[room_counter % len(room_pool)]
                x = c * cell_w
                y = r * cell_d
                rooms.append({
                    "name": f"{room_type} {room_counter+1}",
                    "x": x, "y": y,
                    "width": cell_w, "depth": cell_d,
                    "type": room_type
                })
                room_counter += 1

        # MEP zones: create main service corridors and branches
        mep_zones = []
        # Main HVAC trunk along centre
        corridor_x = width / 2 - 0.5
        # Main electrical and plumbing also follow similar paths
        main_y_offsets = [0.5, depth - 0.5]  # two main runs

        for sys_name, sys_info in MEP_SYSTEMS.items():
            # Main trunk for each system
            if sys_name == "HVAC":
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {
                        "points": [[corridor_x, 0, 0.2], [corridor_x, depth, 0.2]],
                        "size": 0.4
                    }
                })
            elif sys_name == "Electrical":
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {
                        "points": [[0.5, 0, 0.15], [0.5, depth, 0.15], [width - 0.5, depth, 0.15], [width - 0.5, 0, 0.15]],
                        "size": 0.15
                    }
                })
            elif sys_name == "Plumbing":
                mep_zones.append({
                    "system": sys_name,
                    "type": f"{sys_name} Main",
                    "geometry": {
                        "points": [[width/3, 0, 0.1], [width/3, depth, 0.1], [2*width/3, depth, 0.1], [2*width/3, 0, 0.1]],
                        "size": 0.2
                    }
                })

        # Branch connections to each room (simplified: only from HVAC trunk)
        for room in rooms:
            cx = room["x"] + room["width"] / 2
            cy = room["y"] + room["depth"] / 2
            mep_zones.append({
                "system": "HVAC",
                "type": "Branch Duct",
                "geometry": {
                    "points": [[corridor_x, cy, 0.2], [cx, cy, 0.2]],
                    "size": 0.15
                }
            })
            # Electrical branch
            mep_zones.append({
                "system": "Electrical",
                "type": "Branch Conduit",
                "geometry": {
                    "points": [[room["x"] + room["width"]/2, room["y"], 0.15],
                               [room["x"] + room["width"]/2, room["y"] + room["depth"], 0.15]],
                    "size": 0.1
                }
            })
            # Plumbing branch (to wet rooms)
            if room["type"] in ["Bathroom", "Kitchen", "Pantry"]:
                mep_zones.append({
                    "system": "Plumbing",
                    "type": "Branch Pipe",
                    "geometry": {
                        "points": [[room["x"], room["y"] + room["depth"]/2, 0.1],
                                   [room["x"] + room["width"], room["y"] + room["depth"]/2, 0.1]],
                        "size": 0.1
                    }
                })

        # Add structural columns (simplified grid)
        columns = []
        col_spacing = 5  # metres
        for x in range(0, int(width) + 1, col_spacing):
            for y in range(0, int(depth) + 1, col_spacing):
                columns.append({"x": x, "y": y, "size": 0.3})

        building["floors_data"].append({
            "floor_num": f+1,
            "width": width,
            "depth": depth,
            "rooms": rooms,
            "mep_zones": mep_zones,
            "columns": columns,
            "elevation": f * building["floor_height"]
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
    room_colors = {
        "Living Room": "#1e3a8a", "Bedroom": "#4c1d95", "Bathroom": "#78350f",
        "Kitchen": "#b45309", "Dining": "#0f766e",
        "Open Office": "#064e3b", "Meeting Room": "#0e7490", "Reception": "#1e40af",
        "Server Room": "#312e81", "Pantry": "#9a3412",
        "Factory Floor": "#475569", "Warehouse Bay": "#334155", "Loading Dock": "#1e293b",
        "Machine Room": "#0f172a", "Office": "#064e3b",
        "Retail Space": "#8b5cf6", "Apartment": "#4c1d95", "Corridor": "#6b7280",
        "Storage": "#78716c"
    }
    for room in floor_data["rooms"]:
        rx = room["x"] * 50
        ry = room["y"] * 50
        rw = room["width"] * 50
        rd = room["depth"] * 50
        color = room_colors.get(room["type"], "#334155")
        svg += f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rd}" fill="{color}" fill-opacity="0.3" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{rx+rw/2}" y="{ry+rd/2}" font-size="10" fill="white" text-anchor="middle" dominant-baseline="middle">{room["name"]}</text>'

    # MEP zones (line styles vary by system)
    for zone in floor_data["mep_zones"]:
        system = zone["system"]
        info = MEP_SYSTEMS.get(system, MEP_SYSTEMS["HVAC"])
        color = info["color_2d"]
        dash = "4" if info["line_style"] == "dashed" else ("2,2" if info["line_style"] == "dotted" else "none")
        pts = zone["geometry"]["points"]
        for i in range(len(pts)-1):
            x1, y1 = pts[i][0]*50, pts[i][1]*50
            x2, y2 = pts[i+1][0]*50, pts[i+1][1]*50
            svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2" stroke-dasharray="{dash}"/>'
    svg += '</svg>'
    return svg

# ---------- 3D Plotly Renderer ----------
def render_3d_building(building):
    fig = go.Figure()
    room_colors_3d = {
        "Living Room": "blue", "Bedroom": "purple", "Bathroom": "orange",
        "Kitchen": "brown", "Dining": "teal",
        "Open Office": "green", "Meeting Room": "cyan", "Reception": "navy",
        "Server Room": "indigo", "Pantry": "chocolate",
        "Factory Floor": "gray", "Warehouse Bay": "darkslategray", "Loading Dock": "black",
        "Machine Room": "darkgray", "Office": "green",
        "Retail Space": "violet", "Apartment": "purple", "Corridor": "lightgray",
        "Storage": "darkkhaki"
    }
    mep_colors_3d = {"HVAC": "gold", "Electrical": "cyan", "Plumbing": "lime"}

    for floor in building["floors_data"]:
        z_base = floor["elevation"]
        z_top = z_base + building["floor_height"]
        # Rooms
        for room in floor["rooms"]:
            x0, y0 = room["x"], room["y"]
            x1, y1 = x0 + room["width"], y0 + room["depth"]
            fig.add_trace(go.Mesh3d(
                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                z=[z_base]*4 + [z_top]*4,
                color=room_colors_3d.get(room["type"], "gray"),
                opacity=0.7,
                flatshading=True,
                name=room["name"],
                showlegend=False
            ))
        # Columns
        for col in floor.get("columns", []):
            xc, yc = col["x"], col["y"]
            size = col["size"]
            fig.add_trace(go.Scatter3d(
                x=[xc, xc], y=[yc, yc], z=[z_base, z_top],
                mode='lines', line=dict(color='darkgray', width=6),
                showlegend=False
            ))
        # MEP lines
        for zone in floor["mep_zones"]:
            system = zone["system"]
            color = mep_colors_3d.get(system, "white")
            pts = zone["geometry"]["points"]
            for i in range(len(pts)-1):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[i+1]
                z_abs1 = z_base + z1
                z_abs2 = z_base + z2
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z_abs1, z_abs2],
                    mode='lines',
                    line=dict(color=color, width=4),
                    name=f"{system}",
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

# ---------- User Interface ----------
st.title("🏗️ AEC/MEP Building Synthesizer")
st.markdown("Generate multidisciplinary buildings (Residential, Commercial, Industrial, Mixed‑Use) with **HVAC, electrical, plumbing** systems and interactive 3D.")

with st.sidebar:
    st.header("Design Parameters")
    # Building category and subtype
    building_category = st.selectbox("Building Category", list(BUILDING_CATEGORIES.keys()))
    building_subtype = st.selectbox("Building Type", BUILDING_CATEGORIES[building_category]["subtypes"])

    floors = st.slider("Number of Floors", 1, 10, 2)
    # Adapt area range based on category
    min_area, max_area = BUILDING_CATEGORIES[building_category]["typical_area_range"]
    area_per_floor = st.slider("Area per Floor (m²)", min_area, max_area, (min_area + max_area)//2)
    rooms_per_floor = st.slider("Rooms per Floor", 2, 16, 6)
    hvac_type = st.selectbox("HVAC System", ["VAV", "VRF", "Chilled Beams", "Split DX", "Packaged Rooftop"])
    generate_btn = st.button("Generate Building", use_container_width=True)

if generate_btn:
    building = generate_building(building_subtype, floors, area_per_floor, rooms_per_floor, hvac_type)
    st.session_state["building"] = building

if "building" in st.session_state:
    building = st.session_state["building"]
    st.success(f"Generated {building['floors']}‑storey {building['type']} building with {building['hvac']} HVAC.")

    floor_choice = st.selectbox("Select Floor for 2D Plan", [f"Floor {i+1}" for i in range(building["floors"])])
    floor_idx = int(floor_choice.split()[-1]) - 1
    floor_data = building["floors_data"][floor_idx]

    col2d, col3d = st.columns(2)
    with col2d:
        st.subheader(f"2D Floor Plan – {floor_choice}")
        svg = render_2d_floor(floor_data)
        st.markdown(f'<div style="border:1px solid #334155; border-radius:8px; overflow:hidden;">{svg}</div>', unsafe_allow_html=True)
        st.caption("Coloured rooms; dashed = electrical, dotted = plumbing, solid gold = HVAC ducts. Circles = columns.")
    with col3d:
        st.subheader("3D Building Model (Interactive)")
        fig3d = render_3d_building(building)
        st.plotly_chart(fig3d, use_container_width=True)
        st.caption("Drag to rotate, scroll to zoom. Gold = HVAC, cyan = electrical, green = plumbing.")

    st.markdown("---")
    st.subheader("📊 Building Summary")
    total_area = building["floors"] * building["area_per_floor"]
    st.metric("Total Gross Floor Area", f"{total_area} m²")
    st.metric("Structural Columns (approx)", f"{int(sum(len(fd['columns']) for fd in building['floors_data']))}")
    st.metric("HVAC System", building["hvac"])
    st.info("💡 **Autodesk Platform Services (APS)** can export this as a BIM model. Contact for integration details.")
