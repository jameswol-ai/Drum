# streamlit_app.py
# =============================
# ARC STUDIO ENGINE – AEC/MEP SYNTHESIS
# Single‑click building generator: 2D SVG floor plan + interactive 3D (Plotly) with MEP/HVAC zones
# =============================

import streamlit as st
import math
import plotly.graph_objects as go

# ---------- Page config MUST be first Streamlit command ----------
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

# ---------- Building Generator ----------
def generate_building(building_type, floors, area_per_floor, rooms_per_floor, hvac_type):
    """Creates a multi‑floor building with rooms, MEP zones and 3D data."""
    building = {
        "floors": floors,
        "area_per_floor": area_per_floor,
        "floor_height": 3.0,  # metres
        "rooms_per_floor": rooms_per_floor,
        "hvac": hvac_type,
        "type": building_type,
        "floors_data": []
    }

    for f in range(floors):
        # Rectangular floor plan (square root of area)
        side = math.sqrt(area_per_floor)
        width = side
        depth = side

        # Subdivide into rooms (approximate grid)
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
                # Assign room type based on building type and position
                if building_type == "Office":
                    room_type = "Open Office" if c % 2 == 0 else "Meeting Room"
                elif building_type == "Residential":
                    room_type = "Living Room" if (r == 0 and c == 0) else ("Bedroom" if c < cols - 1 else "Bathroom")
                else:
                    room_type = "Flex Space"

                x = c * cell_w
                y = r * cell_d
                rooms.append({
                    "name": f"{room_type} {room_counter+1}",
                    "x": x, "y": y,
                    "width": cell_w, "depth": cell_d,
                    "type": room_type
                })
                room_counter += 1

        # MEP/HVAC zones (simplified)
        mep_zones = []
        # Main duct along the centre corridor
        corridor_x = width / 2 - 0.5
        mep_zones.append({
            "type": "HVAC Duct",
            "geometry": {
                "points": [[corridor_x, 0, 0.2], [corridor_x, depth, 0.2]],
                "size": 0.4
            }
        })
        # Branch ducts to each room
        for room in rooms:
            cx = room["x"] + room["width"] / 2
            cy = room["y"] + room["depth"] / 2
            mep_zones.append({
                "type": "Branch Duct",
                "geometry": {
                    "points": [[corridor_x, cy, 0.2], [cx, cy, 0.2]],
                    "size": 0.2
                }
            })

        building["floors_data"].append({
            "floor_num": f+1,
            "width": width,
            "depth": depth,
            "rooms": rooms,
            "mep_zones": mep_zones,
            "elevation": f * building["floor_height"]
        })

    return building

# ---------- 2D SVG Renderer ----------
def render_2d_floor(floor_data):
    w = floor_data["width"] * 50   # 1 m = 50 px
    d = floor_data["depth"] * 50
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {d}" style="background:#0f172a; width:100%; height:auto;">'
    # Grid
    for x in range(0, int(w), 50):
        svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{d}" stroke="#1e293b" stroke-width="0.5"/>'
    for y in range(0, int(d), 50):
        svg += f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="#1e293b" stroke-width="0.5"/>'
    # Rooms
    for room in floor_data["rooms"]:
        rx = room["x"] * 50
        ry = room["y"] * 50
        rw = room["width"] * 50
        rd = room["depth"] * 50
        color = {
            "Living Room": "#1e3a8a", "Bedroom": "#4c1d95", "Bathroom": "#78350f",
            "Open Office": "#064e3b", "Meeting Room": "#0f766e", "Flex Space": "#475569"
        }.get(room["type"], "#334155")
        svg += f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rd}" fill="{color}" fill-opacity="0.3" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{rx+rw/2}" y="{ry+rd/2}" font-size="10" fill="white" text-anchor="middle" dominant-baseline="middle">{room["name"]}</text>'
    # MEP ducts (dashed lines)
    for zone in floor_data["mep_zones"]:
        pts = zone["geometry"]["points"]
        color = "#f59e0b" if "Duct" in zone["type"] else "#3b82f6"
        for i in range(len(pts)-1):
            x1, y1 = pts[i][0]*50, pts[i][1]*50
            x2, y2 = pts[i+1][0]*50, pts[i+1][1]*50
            svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3" stroke-dasharray="4"/>'
    svg += '</svg>'
    return svg

# ---------- 3D Plotly Renderer ----------
def render_3d_building(building):
    fig = go.Figure()
    colors = {
        "Living Room": "blue", "Bedroom": "purple", "Bathroom": "orange",
        "Open Office": "green", "Meeting Room": "teal", "Flex Space": "gray",
        "HVAC Duct": "gold", "Branch Duct": "goldenrod"
    }

    for floor in building["floors_data"]:
        z_base = floor["elevation"]
        z_top = z_base + building["floor_height"]
        # Rooms as extruded boxes
        for room in floor["rooms"]:
            x0, y0 = room["x"], room["y"]
            x1, y1 = x0 + room["width"], y0 + room["depth"]
            fig.add_trace(go.Mesh3d(
                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                z=[z_base]*4 + [z_top]*4,
                color=colors.get(room["type"], "gray"),
                opacity=0.7,
                flatshading=True,
                name=room["name"],
                showlegend=False
            ))
        # MEP ducts as lines
        for zone in floor["mep_zones"]:
            pts = zone["geometry"]["points"]
            for i in range(len(pts)-1):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[i+1]
                z_abs1 = z_base + z1
                z_abs2 = z_base + z2
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z_abs1, z_abs2],
                    mode='lines',
                    line=dict(color=colors.get(zone["type"], "yellow"), width=6),
                    name=zone["type"],
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
st.markdown("One‑click generation of a multidisciplinary building with **architecture, structure, MEP & HVAC** – no epochs, no complex setup.")

with st.sidebar:
    st.header("Design Parameters")
    building_type = st.selectbox("Building Type", ["Office", "Residential", "Mixed Use"])
    floors = st.slider("Number of Floors", 1, 10, 2)
    area_per_floor = st.slider("Area per Floor (m²)", 50, 500, 150)
    rooms_per_floor = st.slider("Rooms per Floor", 2, 16, 6)
    hvac_type = st.selectbox("HVAC System", ["VAV", "VRF", "Chilled Beams"])
    generate_btn = st.button("Generate Building", use_container_width=True)

if generate_btn:
    building = generate_building(building_type, floors, area_per_floor, rooms_per_floor, hvac_type)
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
        st.caption("Rooms colour‑coded; dashed lines = HVAC ducts.")
    with col3d:
        st.subheader("3D Building Model (Interactive)")
        fig3d = render_3d_building(building)
        st.plotly_chart(fig3d, use_container_width=True)
        st.caption("Drag to rotate, scroll to zoom. Ducts shown at ceiling level.")

    st.markdown("---")
    st.subheader("📊 Building Summary")
    total_area = building["floors"] * building["area_per_floor"]
    st.metric("Total Gross Floor Area", f"{total_area} m²")
    st.metric("Estimated Structural Columns", f"{int(floors * 4 * math.sqrt(area_per_floor))}")

    # Note about Autodesk (informational only, no code)
    st.info("💡 **Autodesk Platform Services (APS)** could be integrated to export this as a BIM model. You would need your own Forge app credentials. Ask for example integration code.")
