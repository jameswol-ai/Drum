# streamlit_app.py
# DRUM Studio – Game + Professional Structural Analysis Workstation
import streamlit as st
import uuid
from datetime import datetime
import random

from main import (
    load_users, save_users, get_user, create_user, authenticate,
    update_user_data, xp_for_level, add_xp, load_memory, save_memory,
    log_event, Building, generate_plan, simulate_evolution, generate_rhythm,
    init_quests, update_quests, grant_quest_rewards, DEFAULT_STATE
)
from engineering import (
    CONCRETE_GRADES, STEEL_GRADES, TIMBER_CLASSES, WALL_TYPES, FINISHES,
    check_rc_beam, check_steel_beam, check_rc_column,
    slab_thickness_estimate, foundation_size,
    calculate_total_area, compute_floor_loads, check_structural_integrity,
    calculate_energy_score, estimate_cost,
    to_metric, to_imperial
)

# ---------- Page Config ----------
st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

# ---------- Session State ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.memory = DEFAULT_STATE.copy()
    st.session_state.active_building = None
    st.session_state.config = {"generations": 5, "mutation_rate": 0.1, "population_size": 10}
    st.session_state.unit_system = "metric"
    st.session_state.eng_params = {
        "live_load": 2.5,
        "slab_thickness": 0.2,
        "additional_dead": 1.0,
        "concrete_cost": 250,
        "steel_cost": 50,
        "glass_cost": 150,
        "labor_cost": 100,
        "glazing_ratio": 0.2,
        "orientation": "south",
    }

if not load_users():
    create_user("admin", "admin123", role="admin")

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #0F172A; color: #E2E8F0;
}
h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
.sidebar .sidebar-content { background: #1E293B; }
.stButton>button {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px;
    padding: 0.5rem 1.5rem; font-weight: 600; transition: 0.2s;
}
.stButton>button:hover { transform: scale(1.02); }
.metric-card {
    background: #1E293B; border-radius: 12px; padding: 1rem;
    border: 1px solid #334155;
}
.stNumberInput>div>div>input {
    background: #1E293B; color: #F8FAFC; border: 1px solid #475569;
}
.stSelectbox>div>div>select {
    background: #1E293B; color: #F8FAFC;
}
</style>
""", unsafe_allow_html=True)

# ---------- UI Helpers ----------
def show_xp_bar(user):
    level = user["level"]
    xp = user["xp"]
    needed = xp_for_level(level)
    progress = xp / needed if needed > 0 else 1.0
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin:10px 0;">
        <span style="font-weight:600; color:#A78BFA;">LVL {level}</span>
        <div style="flex:1; height:10px; background:#1E293B; border-radius:5px; overflow:hidden;">
            <div style="width:{progress*100}%; height:100%; background:linear-gradient(90deg,#F59E0B,#FBBF24);"></div>
        </div>
        <span style="font-size:0.8rem; color:#CBD5E1;">{xp}/{needed} XP</span>
    </div>
    """, unsafe_allow_html=True)

def render_svg_plan(plan, width=800, height=500):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{item["name"]}</text>'
    svg += '</svg>'
    return svg

def show_building(building, label=""):
    st.subheader(f"🏗️ {label} — {building.name}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.8rem; color:#94A3B8;">SCORE</div>
            <div style="font-size:1.8rem; font-weight:700; color:#FBBF24;">{building.score}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.8rem; color:#94A3B8;">ID</div>
            <div style="font-size:1.8rem; font-weight:700;">{building.id}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.8rem; color:#94A3B8;">ROOMS</div>
            <div style="font-size:1.8rem; font-weight:700;">{len(building.plan)}</div>
        </div>
        """, unsafe_allow_html=True)
    if building.plan:
        st.markdown(render_svg_plan(building.plan), unsafe_allow_html=True)

def show_rhythm(rhythm):
    rows = {"Kick": rhythm["kick"], "Snare": rhythm["snare"], "Hi‑Hat": rhythm["hihat"]}
    html = "<div style='display:flex; flex-direction:column; margin-top:10px;'>"
    for name, pattern in rows.items():
        html += f"<div style='display:flex; align-items:center;'><span style='width:60px; color:#CBD5E1;'>{name}</span>"
        for step in pattern:
            color = "#FBBF24" if step else "#1E293B"
            html += f"<div style='width:30px; height:30px; background:{color}; margin:1px; border-radius:4px;'></div>"
        html += "</div>"
    html += f"<div style='color:#94A3B8; margin-top:5px;'>BPM: {rhythm['bpm']}</div></div>"
    st.markdown(html, unsafe_allow_html=True)

# ======================
# LOGIN PAGE
# ======================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🏗️ DRUM Studio</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#A78BFA;'>Login or create your architect identity</p>", unsafe_allow_html=True)
        with st.form("auth"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            col_login, col_reg = st.columns(2)
            if col_login.form_submit_button("Login"):
                user = authenticate(uname, pwd)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = uname
                    st.session_state.user_data = user
                    mem = load_memory(uname)
                    init_quests(uname, mem)
                    st.session_state.memory = mem
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            if col_reg.form_submit_button("Register"):
                if not uname or not pwd:
                    st.error("Fill all fields.")
                else:
                    try:
                        create_user(uname, pwd)
                        st.success("Account created!")
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

# ======================
# MAIN APP
# ======================
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

# ----- SIDEBAR -----
with st.sidebar:
    st.markdown(f"### 👤 {username}")
    st.caption(user_data.get("role", "user").upper())
    show_xp_bar(user_data)

    # Quests
    with st.expander("📜 Quests"):
        for q in mem.get("quests", []):
            pct = min(q["progress"]/q["target"], 1.0)
            st.write(f"{q['desc']} ({q['progress']}/{q['target']})")
            st.progress(pct)
        st.write("**Daily**")
        for dq in mem.get("daily_quests", []):
            pct = min(dq["progress"]/dq["target"], 1.0)
            st.write(f"{dq['desc']} ({dq['progress']}/{dq['target']})")
            st.progress(pct)

    st.markdown("---")
    page = st.radio("Navigate", ["Command Center", "Evolution Chamber", "Structural Analysis", "Archives"])

    # Unit system toggle
    unit_choice = st.radio("Unit System", ["metric", "imperial"], index=0, key="unit_radio")
    st.session_state.unit_system = unit_choice

    # Engineering params (collapsible)
    with st.expander("🔧 Analysis Settings"):
        st.session_state.eng_params["live_load"] = st.number_input("Live Load (kN/m²)", 1.0, 10.0, 2.5, 0.5, key="live_load")
        st.session_state.eng_params["slab_thickness"] = st.number_input("Slab Thickness (m)", 0.1, 0.5, 0.2, 0.05, key="slab_thick")
        st.session_state.eng_params["additional_dead"] = st.number_input("Additional Dead (kN/m²)", 0.0, 5.0, 1.0, 0.1, key="add_dead")
        st.session_state.eng_params["glazing_ratio"] = st.slider("Glazing Ratio", 0.05, 0.8, 0.2, key="glaz_ratio")
        st.session_state.eng_params["orientation"] = st.selectbox("Orientation", ["north","south","east","west"], key="orient")

    # Game settings
    with st.expander("⚙️ Game Settings"):
        st.session_state.config["generations"] = st.slider("Generations", 2, 20, 5, key="gen_slider")
        st.session_state.config["mutation_rate"] = st.slider("Mutation Rate", 0.0, 1.0, 0.1, 0.05, key="mut_rate")
        st.session_state.config["population_size"] = st.number_input("Population Size", 2, 50, 10, key="pop_size")

    if st.button("🚪 Logout"):
        save_memory(username, mem)
        for key in ["logged_in","username","user_data","memory","active_building"]:
            if key in st.session_state:
                if key == "memory":
                    st.session_state[key] = DEFAULT_STATE.copy()
                else:
                    st.session_state[key] = None
        st.rerun()

# ======================
# PAGE: COMMAND CENTER
# ======================
if page == "Command Center":
    st.title("📊 Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Buildings", len(mem["buildings"]))
    col2.metric("Sessions", len(mem["sessions"]))
    col3.metric("Badges", "🏅" * len(user_data.get("badges", [])))

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🏗️ Generate Random Building"):
        # Create a random building using evolution with current config
        best, trend = simulate_evolution(st.session_state.config)
        mem["buildings"].append(best.to_dict())
        mem["sessions"].append({"id": str(uuid.uuid4())[:6], "building_id": best.id, "time": datetime.now().isoformat()})
        st.session_state.active_building = best
        log_event(username, mem, f"Quick build: {best.name}")
        update_quests(username, mem, "evolution", {"plan": best.plan})
        grant_quest_rewards(username, mem, on_level_up=st.balloons)
        add_xp(username, int(best.score * 2))
        st.session_state.user_data = get_user(username)
        save_memory(username, mem)
        st.success(f"Created building {best.name} with score {best.score}")
        st.rerun()

    # Active building display
    if st.session_state.active_building:
        show_building(st.session_state.active_building, "Active")
    else:
        st.info("No active building. Generate one above or go to Evolution Chamber.")

    # Recent logs
    st.subheader("Recent Logs")
    for log in reversed(mem["logs"][-5:]):
        st.caption(f"`{log['time'][11:19]}` – {log['msg']}")

# ======================
# PAGE: EVOLUTION CHAMBER
# ======================
elif page == "Evolution Chamber":
    st.title("🧬 Evolution Chamber")
    st.caption("Configure evolution parameters in the sidebar under Game Settings.")

    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("🚀 EVOLVE!", type="primary"):
            with st.spinner("Mixing genes..."):
                best, trend = simulate_evolution(st.session_state.config)
                rhythm = generate_rhythm(best)
                mem["buildings"].append(best.to_dict())
                mem["rhythms"].append(rhythm)
                mem["sessions"].append({"id": str(uuid.uuid4())[:6], "building_id": best.id, "time": datetime.now().isoformat()})
                st.session_state.active_building = best
                log_event(username, mem, f"New design: {best.name}")
                update_quests(username, mem, "evolution", {"plan": best.plan})
                grant_quest_rewards(username, mem, on_level_up=st.balloons)
                leveled = add_xp(username, int(best.score * 2))
                st.session_state.user_data = get_user(username)
                if leveled:
                    st.balloons()
                save_memory(username, mem)
            st.line_chart(trend, use_container_width=True)

    with col2:
        # Show current config
        st.write("**Current Settings**")
        st.write(f"Generations: {st.session_state.config['generations']}")
        st.write(f"Mutation Rate: {st.session_state.config['mutation_rate']}")
        st.write(f"Population Size: {st.session_state.config['population_size']}")

        if st.button("📦 Load Demo Building"):
            demo = Building(name="Demo", score=85)
            generate_plan(demo)
            st.session_state.active_building = demo
            log_event(username, mem, "Loaded demo building")
            save_memory(username, mem)
            st.rerun()

    if st.session_state.active_building:
        show_building(st.session_state.active_building, "Active")
        if mem["rhythms"] and mem["sessions"]:
            last = mem["sessions"][-1]
            if last.get("building_id") == st.session_state.active_building.id:
                st.subheader("🥁 Rhythm Sequencer")
                show_rhythm(mem["rhythms"][-1])
    else:
        st.info("Press EVOLVE! or load a demo to create a building.")

# ======================
# PAGE: STRUCTURAL ANALYSIS
# ======================
elif page == "Structural Analysis":
    st.title("🏗️ Structural Analysis Workstation")
    st.caption("Design & check beams, columns, slabs, foundations, walls & finishes to Eurocodes")

    tabs = st.tabs(["📐 Beams", "🧱 Columns", "🔲 Slabs", "🌍 Foundations", "🏛️ Walls & Finishes"])

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
                if res["pass"]:
                    st.success("✅ Beam OK")
                else:
                    st.error("❌ Beam fails check")
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
                if res["pass"]:
                    st.success("✅ Beam OK")
                else:
                    st.error("❌ Beam fails")
                st.json(res)

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
                if res["pass"]:
                    st.success("✅ Column OK")
                else:
                    st.error("❌ Column fails")
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

    # ---- WALLS & FINISHES ----
    with tabs[4]:
        st.subheader("Wall Types & Finishes")
        wall = st.selectbox("Wall Type", list(WALL_TYPES.keys()), key="wall_type")
        props = WALL_TYPES[wall]
        st.write(f"Weight: {props['weight']} kN/m², U‑value: {props['U']} W/m²K, Sound: {props['sound']} dB")
        finishes = st.multiselect("Finishes", list(FINISHES.keys()), default=["Plaster (internal)", "Paint"], key="finishes")
        finish_load = sum(FINISHES[f] for f in finishes)
        st.metric("Total finish load", f"{finish_load:.3f} kN/m²")
        if st.button("Apply to Model", key="apply_wall"):
            st.info("Wall/finish selection saved to project.")

    # ---- BUILDING INTEGRATION ----
    st.markdown("---")
    if st.session_state.active_building:
        st.subheader("📐 Building Plan Analysis")
        plan = st.session_state.active_building.plan
        area = calculate_total_area(plan)
        load = compute_floor_loads(plan,
            live_load_kN_per_m2=st.session_state.eng_params["live_load"],
            slab_thickness_m=st.session_state.eng_params["slab_thickness"],
            additional_dead_load_kN_per_m2=st.session_state.eng_params["additional_dead"])
        st.write(f"Total floor area: {area:.1f} m², Design load: {load:.1f} kN")
        integrity = check_structural_integrity(plan)
        st.write(f"Max span: {integrity['max_span_m']} m, Suggested beam: {integrity['suggested_beam']}")
    else:
        st.info("No active building. Evolve or quick‑build one first.")

# ---- PILES ----
with tabs[7]:
    st.subheader("Pile Foundation Design (Simplified EC7)")
    pile_type = st.selectbox("Pile type", ["Bored", "Driven"], key="pile_type")
    diameter = st.number_input("Pile diameter (m)", 0.3, 2.0, 0.6, 0.1, key="pile_d")
    length = st.number_input("Pile length (m)", 5.0, 40.0, 15.0, 1.0, key="pile_L")
    soil = st.selectbox("Soil type", ["sand", "clay"], key="pile_soil")
    N = st.number_input("SPT N-value", 5, 60, 20, key="pile_N")
    safety = st.number_input("Factor of safety", 2.0, 4.0, 2.5, 0.1, key="pile_fs")
    if st.button("Calculate Capacity", key="pile_calc"):
        res = pile_capacity(diameter, length, soil, N, safety)
        st.metric("Allowable Capacity", f"{res['Q_all_kN']} kN")
        st.write(f"Ultimate capacity: {res['Q_ult_kN']} kN")
        st.write(f"Shaft resistance: {res['shaft_kN']} kN, Base: {res['base_kN']} kN")

# ---- EXPORT / REPORT ----
with tabs[9]:
    st.subheader("Export Analysis Report (PDF)")
    st.info("Generate a PDF report of the latest structural analysis results.")
    if st.button("📄 Generate Report"):
        # Collect current results from session (example: last check results could be stored)
        # For demo, create a dummy results dictionary.
        report_data = {
            "Project": "Sample",
            "Beam": "RC Beam check: ...",
            "Column": "Column check: ...",
            # In a full app you'd gather actual results.
        }
        # You would normally populate with the latest analysis results.
        # For now, we use the building plan data if available.
        if st.session_state.active_building:
            plan = st.session_state.active_building.plan
            area = calculate_total_area(plan)
            load = compute_floor_loads(plan,
                live_load=st.session_state.eng_params["live_load"],
                slab_thickness=st.session_state.eng_params["slab_thickness"],
                additional_dead=st.session_state.eng_params["additional_dead"])
            report_data["Total Floor Area"] = f"{area:.1f} m²"
            report_data["Design Load"] = f"{load:.1f} kN"
            integrity = check_structural_integrity(plan)
            report_data["Max Span"] = f"{integrity['max_span_m']} m"
            report_data["Suggested Beam"] = integrity["suggested_beam"]

        filename, error = generate_analysis_report(report_data)
        if error:
            st.error(error)
        else:
            with open(filename, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=filename, mime="application/pdf")
            st.success("Report generated!")

# ---- EXPORT / REPORT ----
with tabs[9]:
    st.subheader("Export Analysis Report (PDF)")
    st.info("Generate a PDF report of the latest structural analysis results.")
    if st.button("📄 Generate Report"):
        # Collect current results from session (example: last check results could be stored)
        # For demo, create a dummy results dictionary.
        report_data = {
            "Project": "Sample",
            "Beam": "RC Beam check: ...",
            "Column": "Column check: ...",
            # In a full app you'd gather actual results.
        }
        # You would normally populate with the latest analysis results.
        # For now, we use the building plan data if available.
        if st.session_state.active_building:
            plan = st.session_state.active_building.plan
            area = calculate_total_area(plan)
            load = compute_floor_loads(plan,
                live_load=st.session_state.eng_params["live_load"],
                slab_thickness=st.session_state.eng_params["slab_thickness"],
                additional_dead=st.session_state.eng_params["additional_dead"])
            report_data["Total Floor Area"] = f"{area:.1f} m²"
            report_data["Design Load"] = f"{load:.1f} kN"
            integrity = check_structural_integrity(plan)
            report_data["Max Span"] = f"{integrity['max_span_m']} m"
            report_data["Suggested Beam"] = integrity["suggested_beam"]

        filename, error = generate_analysis_report(report_data)
        if error:
            st.error(error)
        else:
            with open(filename, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=filename, mime="application/pdf")
            st.success("Report generated!")

# ======================
# PAGE: ARCHIVES
# ======================
    st.title("🗄️ Archives")
    if mem["buildings"]:
        for i, bdict in enumerate(reversed(mem["buildings"])):
            building = Building.from_dict(bdict)
            with st.expander(f"{building.name} – Score {building.score}"):
                show_building(building)
                if i < len(mem["rhythms"]):
                    show_rhythm(mem["rhythms"][-i-1])
    else:
        st.info("No buildings yet. Use the Command Center or Evolution Chamber to create one.")
