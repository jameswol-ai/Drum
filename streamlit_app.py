# streamlit_app.py
# =============================
# DRUM – Professional Structural Analysis Workstation
# =============================
import streamlit as st
import math
from pathlib import Path
from datetime import datetime
import uuid
import json

# ---------- Engineering functions ----------
from engineering import *
from main import *   # assuming you still have main.py with game helpers

# ---------- Page Config ----------
st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

# ---------- Session State ----------
if "unit_system" not in st.session_state:
    st.session_state.unit_system = "metric"
if "active_building" not in st.session_state:
    st.session_state.active_building = None
# ... other session initializations from main.py

# ---------- CSS (Professional Dark Theme) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; background: #0F172A; color: #E2E8F0; }
h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
.sidebar .sidebar-content { background: #1E293B; }
.stButton>button {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px; padding: 0.5rem 1.5rem;
    font-weight: 600; transition: 0.2s;
}
.stButton>button:hover { transform: scale(1.02); }
.metric-card {
    background: #1E293B; border-radius: 12px; padding: 1rem;
    border: 1px solid #334155;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/construction.png", width=60)
    st.title("DRUM Studio")
    st.markdown("---")

    # Unit toggle
    unit = st.radio("Unit System", ["metric", "imperial"], index=0)
    st.session_state.unit_system = unit

    st.markdown("### Navigation")
    page = st.radio("", ["Command Center", "Evolution Chamber", "Structural Analysis", "Archives"])

    # Game settings (collapsed)
    with st.expander("⚙️ Game Settings"):
        # ... (same as before)
        pass

    if st.button("🚪 Logout"):
        # ... (logout logic)
        pass

# ========================
# PAGE: Structural Analysis
# ========================
if page == "Structural Analysis":
    st.title("🏗️ Structural Analysis Workstation")
    st.caption("Design & check beams, columns, slabs, foundations, walls & finishes to Eurocodes")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📐 Beams", "🧱 Columns", "🔲 Slabs", "🌍 Foundations", "🏛️ Walls & Finishes"]
    )

    # ---------- BEAMS ----------
    with tab1:
        st.subheader("Beam Design")
        col1, col2 = st.columns(2)
        with col1:
            beam_type = st.selectbox("Material", ["Reinforced Concrete", "Steel", "Timber", "Composite"])
            if beam_type == "Reinforced Concrete":
                concrete_grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()))
                b = st.number_input("Width (mm)", min_value=100, value=300, step=50)
                h = st.number_input("Total height (mm)", min_value=200, value=500, step=50)
                d = h - 50  # effective depth
                span = st.number_input("Span (m)", min_value=1.0, value=6.0, step=0.5)
                M_ed = st.number_input("Design Moment M_Ed (kNm)", value=120.0, step=10.0)
                V_ed = st.number_input("Design Shear V_Ed (kN)", value=80.0, step=10.0)
                if st.button("Check RC Beam"):
                    fck = CONCRETE_GRADES[concrete_grade]["fck"]
                    res = check_rc_beam(b*1e-3, h*1e-3, d*1e-3, fck, M_ed*1e3, V_ed*1e3, span)
                    st.json(res)
            elif beam_type == "Steel":
                steel_grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()))
                section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"])
                span = st.number_input("Span (m)", 2.0, 20.0, 6.0)
                M_ed = st.number_input("M_Ed (kNm)", 50.0, 500.0, 100.0)
                V_ed = st.number_input("V_Ed (kN)", 20.0, 300.0, 50.0)
                if st.button("Check Steel Beam"):
                    steel = STEEL_GRADES[steel_grade]
                    res = check_steel_beam(section, M_ed*1e3, V_ed*1e3, span, steel)
                    st.json(res)
            # (Timber & Composite can follow similar pattern)

    # ---------- COLUMNS ----------
    with tab2:
        st.subheader("Column Design")
        col_type = st.selectbox("Column Material", ["RC", "Steel", "Timber"])
        if col_type == "RC":
            N_ed = st.number_input("Axial load N_Ed (kN)", 100.0, 5000.0, 500.0)
            M_ed = st.number_input("Moment M_Ed (kNm)", 0.0, 500.0, 20.0)
            b = st.number_input("Width (mm)", 200, 1000, 300)
            h = st.number_input("Depth (mm)", 200, 1000, 300)
            l0 = st.number_input("Effective length (m)", 2.0, 10.0, 3.0)
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()))
            if st.button("Check Column"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_column(N_ed*1e3, M_ed*1e3, b*1e-3, h*1e-3, fck, l0)
                st.json(res)

    # ---------- SLABS ----------
    with tab3:
        st.subheader("Slab Thickness Estimation")
        span = st.number_input("Short span (m)", 2.0, 15.0, 5.0)
        support = st.selectbox("Support condition", ["simply_supported", "continuous"])
        t = slab_thickness_estimate(span, support)
        st.success(f"Recommended slab thickness: **{t*1000:.0f} mm**")

    # ---------- FOUNDATIONS ----------
    with tab4:
        st.subheader("Pad Footing Sizing")
        total_load = st.number_input("Total column load (kN)", 100.0, 10000.0, 500.0)
        bearing = st.number_input("Allowable bearing pressure (kN/m²)", 50.0, 500.0, 150.0)
        fs = st.number_input("Factor of safety", 2.0, 5.0, 3.0)
        if st.button("Size Footing"):
            res = foundation_size(bearing, total_load, fs)
            st.success(f"Square footing side: **{res['side_m']} m** (area: {res['area_m2']} m²)")

    # ---------- WALLS & FINISHES ----------
    with tab5:
        st.subheader("Wall Types & Finishes")
        selected_wall = st.selectbox("Wall Type", list(WALL_TYPES.keys()))
        props = WALL_TYPES[selected_wall]
        st.write(f"Weight: {props['weight']} kN/m², U‑value: {props['U']} W/m²K, Sound: {props['sound']} dB")

        st.markdown("---")
        st.subheader("Applied Finishes")
        finishes_selected = st.multiselect("Select finishes", list(FINISHES.keys()), default=["Plaster (internal)", "Paint"])
        total_finish_load = sum(FINISHES[f] for f in finishes_selected)
        st.metric("Total finish load", f"{total_finish_load:.3f} kN/m²")

        if st.button("Add to Building Model"):
            st.info("Wall/finish data will be saved to your project memory.")

    # ---------- Summary & Export ----------
    st.markdown("---")
    if st.button("📄 Generate Analysis Report"):
        # Collect all data and generate a summary (placeholder)
        st.success("Report generated (simulated).")
