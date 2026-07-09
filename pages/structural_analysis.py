import streamlit as st
from engineering import *
from main import show_building, calculate_total_area, compute_floor_loads

def structural_analysis_page():
    st.title("🏗️ Structural Analysis Workstation")
    st.caption("Design & check beams, columns, slabs, foundations, connections, seismic, wind")

    tabs = st.tabs([
    "📐 Beams", "🧱 Columns", "🔲 Slabs", "🌍 Foundations",
    "🔗 Connections", "🌪️ Seismic/Wind", "🏛️ Walls & Finishes",
    "📌 Piles", "⚡ Prestressed", "📄 Export/Report"
])

    # ---- BEAMS ----
    with tabs[0]:
        st.subheader("Beam Design")
        beam_mat = st.selectbox("Material", ["Reinforced Concrete", "Steel", "Timber", "Composite"], key="beam_mat")
        if beam_mat == "Reinforced Concrete":
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()), key="beam_rc_grade")
            b = st.number_input("Width (mm)", 100, 1000, 300, key="beam_b")
            h = st.number_input("Total height (mm)", 200, 2000, 500, key="beam_h")
            d = h - 50
            span = st.number_input("Span (m)", 1.0, 30.0, 6.0, key="beam_span")
            M_ed = st.number_input("Design Moment M_Ed (kNm)", 10.0, 1000.0, 120.0, key="beam_Med")
            V_ed = st.number_input("Design Shear V_Ed (kN)", 10.0, 500.0, 80.0, key="beam_Ved")
            if st.button("Check RC Beam", key="check_rc_beam"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_beam(b*1e-3, h*1e-3, d*1e-3, fck, M_ed*1e3, V_ed*1e3, span)
                if res["pass"]: st.success("✅ Beam OK")
                else: st.error("❌ Beam fails check")
                st.json(res)
        elif beam_mat == "Steel":
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="beam_steel_grade")
            section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"], key="beam_sec")
            span = st.number_input("Span (m)", 2.0, 20.0, 6.0, key="beam_span_steel")
            M_ed = st.number_input("M_Ed (kNm)", 50.0, 500.0, 100.0, key="beam_Med_steel")
            V_ed = st.number_input("V_Ed (kN)", 20.0, 300.0, 50.0, key="beam_Ved_steel")
            if st.button("Check Steel Beam", key="check_steel_beam"):
                steel = STEEL_GRADES[grade]
                res = check_steel_beam(section, M_ed*1e3, V_ed*1e3, span, steel)
                if res["pass"]: st.success("✅ Beam OK")
                else: st.error("❌ Beam fails")
                st.json(res)
        elif beam_mat == "Timber":
            timber_cls = st.selectbox("Timber Class", list(TIMBER_CLASSES.keys()), key="timber_cls")
            b = st.number_input("Width (mm)", 50, 300, 100, key="timber_b")
            h = st.number_input("Height (mm)", 100, 600, 200, key="timber_h")
            L = st.number_input("Span (m)", 1.0, 10.0, 4.0, key="timber_L")
            qk = st.number_input("Live load (kN/m)", 0.5, 10.0, 2.0, key="timber_qk")
            gk = st.number_input("Dead load (kN/m)", 0.1, 5.0, 0.5, key="timber_gk")
            ld = st.selectbox("Load duration", ["permanent","long","medium","short","instant"], key="timber_ld")
            if st.button("Check Timber Beam", key="check_timber"):
                res = check_timber_beam(b*1e-3, h*1e-3, L, qk, gk, timber_cls, ld)
                if res["pass"]: st.success("✅ Timber beam OK")
                else: st.error("❌ Timber beam fails")
                st.json(res)
        else:  # Composite
            if st.button("Composite beam check (soon)"):
                st.info("Composite check not yet implemented.")

    # ---- COLUMNS ----
    with tabs[1]:
        st.subheader("Column Design")
        col_mat = st.selectbox("Material", ["RC", "Steel", "Timber"], key="col_mat")
        if col_mat == "RC":
            N_ed = st.number_input("Axial load N_Ed (kN)", 100.0, 5000.0, 500.0, key="col_Ned")
            M_ed = st.number_input("Moment M_Ed (kNm)", 0.0, 500.0, 20.0, key="col_Med")
            b = st.number_input("Width (mm)", 200, 1000, 300, key="col_b")
            h = st.number_input("Depth (mm)", 200, 1000, 300, key="col_h")
            l0 = st.number_input("Effective length (m)", 2.0, 10.0, 3.0, key="col_l0")
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()), key="col_grade")
            if st.button("Check Column", key="check_col"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_column(N_ed*1e3, M_ed*1e3, b*1e-3, h*1e-3, fck, l0)
                if res["pass"]: st.success("✅ Column OK")
                else: st.error("❌ Column fails")
                st.json(res)
        elif col_mat == "Steel":
            section = st.selectbox("Section", ["HEA 200", "HEA 240", "HEA 300"], key="steel_col_sec")
            N_ed = st.number_input("Axial load (kN)", 50.0, 5000.0, 500.0, key="steel_col_N")
            l = st.number_input("Buckling length (m)", 2.0, 15.0, 4.0, key="steel_col_l")
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="steel_col_grade")
            if st.button("Check Steel Column", key="check_steel_col"):
                steel = STEEL_GRADES[grade]
                res = check_steel_column(section, N_ed*1e3, l, steel)
                if res["pass"]: st.success("✅ Steel column OK")
                else: st.error("❌ Steel column fails")
                st.json(res)

    # ---- SLABS ----
    with tabs[2]:
        st.subheader("Slab Thickness")
        span = st.number_input("Short span (m)", 2.0, 15.0, 5.0, key="slab_span")
        support = st.selectbox("Support", ["simply_supported", "continuous"], key="slab_support")
        t = slab_thickness_estimate(span, support)
        st.success(f"Recommended thickness: **{t*1000:.0f} mm**")

    # ---- FOUNDATIONS ----
    with tabs[3]:
        st.subheader("Pad Footing Sizing")
        load = st.number_input("Total column load (kN)", 100.0, 10000.0, 500.0, key="fdn_load")
        bearing = st.number_input("Allowable bearing pressure (kN/m²)", 50.0, 500.0, 150.0, key="fdn_bearing")
        fs = st.number_input("Factor of safety", 2.0, 5.0, 3.0, key="fdn_fs")
        if st.button("Size Footing", key="size_fdn"):
            res = foundation_size(bearing, load, fs)
            st.success(f"Square footing side: **{res['side_m']} m** (area: {res['area_m2']} m²)")

    # ---- CONNECTIONS ----
    with tabs[4]:
        st.subheader("Bolted Connection (Shear)")
        V_ed = st.number_input("Shear force (kN)", 10.0, 1000.0, 100.0, key="conn_V")
        bolt_d = st.number_input("Bolt diameter (mm)", 12, 36, 20, key="conn_d")
        bolt_class = st.selectbox("Bolt class", ["8.8", "10.9"], key="conn_class")
        n_bolts = st.number_input("Number of bolts", 1, 10, 2, key="conn_n")
        if st.button("Check Connection", key="check_conn"):
            res = check_bolted_connection(V_ed*1e3, bolt_d*1e-3, bolt_class, n_bolts)
            if res["pass"]: st.success("✅ Connection OK")
            else: st.error("❌ Connection fails")
            st.json(res)

    # ---- SEISMIC / WIND ----
    with tabs[5]:
        st.subheader("Seismic Base Shear (EC8 simplified)")
        W = st.number_input("Seismic weight (kN)", 100.0, 50000.0, 1000.0, key="seis_W")
        S = st.number_input("Soil factor S", 0.8, 1.4, 1.0, key="seis_S")
        T = st.number_input("Period T (s)", 0.1, 4.0, 0.5, key="seis_T")
        q = st.number_input("Behavior factor q", 1.0, 5.0, 1.5, key="seis_q")
        ag = st.number_input("Peak ground acceleration ag (g)", 0.05, 0.4, 0.2, key="seis_ag")
        if st.button("Compute Base Shear", key="seis_btn"):
            res = seismic_base_shear(W, S, T, q, ag*9.81)
            st.success(f"Base shear: **{res['Fb_kN']} kN** (Sd = {res['Sd_g']} g)")

        st.markdown("---")
        st.subheader("Wind Load (simplified)")
        v_b = st.number_input("Basic wind speed (m/s)", 10.0, 50.0, 25.0, key="wind_vb")
        c_e = st.number_input("Exposure factor c_e", 1.0, 3.0, 1.5, key="wind_ce")
        c_f = st.number_input("Force coefficient c_f", 0.5, 2.5, 1.3, key="wind_cf")
        A_ref = st.number_input("Reference area (m²)", 1.0, 100.0, 10.0, key="wind_A")
        if st.button("Calculate Wind Force", key="wind_btn"):
            res = wind_load(v_b, c_e, c_f, A_ref)
            st.success(f"Wind force: **{res['Fw_kN']} kN** (q_p = {res['q_p_N/m2']} N/m²)")

    # ---- WALLS & FINISHES ----
    with tabs[6]:
        st.subheader("Wall Types & Finishes")
        wall = st.selectbox("Wall Type", list(WALL_TYPES.keys()), key="wall_type")
        props = WALL_TYPES[wall]
        st.write(f"Weight: {props['weight']} kN/m², U‑value: {props['U']} W/m²K, Sound: {props['sound']} dB")
        finishes = st.multiselect("Finishes", list(FINISHES.keys()), default=["Plaster (internal)", "Paint"], key="finishes")
        finish_load = sum(FINISHES[f] for f in finishes)
        st.metric("Total finish load", f"{finish_load:.3f} kN/m²")

    # ---- BUILDING INTEGRATION ----
    st.markdown("---")
    if st.session_state.active_building:
        st.subheader("📐 Building Plan Analysis")
        plan = st.session_state.active_building.plan
        area = calculate_total_area(plan)
        load = compute_floor_loads(plan,
            live_load=st.session_state.eng_params["live_load"],
            slab_thickness=st.session_state.eng_params["slab_thickness"],
            additional_dead=st.session_state.eng_params["additional_dead"])
        st.write(f"Total floor area: {area:.1f} m², Design load: {load:.1f} kN")
        integrity = check_structural_integrity(plan)
        st.write(f"Max span: {integrity['max_span_m']} m, Suggested beam: {integrity['suggested_beam']}")
    else:
        st.info("No active building.")
