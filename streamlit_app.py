# streamlit_app.py
# DRUM Studio – Main entry point, sidebar, authentication, routing
import streamlit as st
import uuid
from datetime import datetime

from main import (
    load_users, save_users, get_user, create_user, authenticate,
    update_user_data, xp_for_level, add_xp, load_memory, save_memory,
    log_event, Building, generate_plan, simulate_evolution, generate_rhythm,
    init_quests, update_quests, grant_quest_rewards, DEFAULT_STATE
)
from engineering import (
    CONCRETE_GRADES, STEEL_GRADES, TIMBER_CLASSES, WALL_TYPES, FINISHES,
)

# Import page modules
from pages.command_center import command_center_page
from pages.evolution_chamber import evolution_chamber_page
from pages.structural_analysis import structural_analysis_page
from pages.archives import archives_page

# ---------- Page Config ----------
st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

# Session state initialisation (same as before)
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

# CSS (same as before)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; background: #0F172A; color: #E2E8F0; }
h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
.stButton>button {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px; padding: 0.5rem 1.5rem; font-weight: 600; transition: 0.2s;
}
.stButton>button:hover { transform: scale(1.02); }
.metric-card { background: #1E293B; border-radius: 12px; padding: 1rem; border: 1px solid #334155; }
.stNumberInput>div>div>input, .stSelectbox>div>div>select { background: #1E293B; color: #F8FAFC; }
</style>
""", unsafe_allow_html=True)

# UI Helpers (same as before)
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
    col1.markdown(f"""<div class="metric-card"><div style="font-size:0.8rem; color:#94A3B8;">SCORE</div><div style="font-size:1.8rem; font-weight:700; color:#FBBF24;">{building.score}</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class="metric-card"><div style="font-size:0.8rem; color:#94A3B8;">ID</div><div style="font-size:1.8rem; font-weight:700;">{building.id}</div></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class="metric-card"><div style="font-size:0.8rem; color:#94A3B8;">ROOMS</div><div style="font-size:1.8rem; font-weight:700;">{len(building.plan)}</div></div>""", unsafe_allow_html=True)
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

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {username}")
    st.caption(user_data.get("role", "user").upper())
    show_xp_bar(user_data)

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

    unit_choice = st.radio("Unit System", ["metric", "imperial"], index=0, key="unit_radio")
    st.session_state.unit_system = unit_choice

    with st.expander("🔧 Analysis Settings"):
        st.session_state.eng_params["live_load"] = st.number_input("Live Load (kN/m²)", 1.0, 10.0, 2.5, 0.5, key="live_load")
        st.session_state.eng_params["slab_thickness"] = st.number_input("Slab Thickness (m)", 0.1, 0.5, 0.2, 0.05, key="slab_thick")
        st.session_state.eng_params["additional_dead"] = st.number_input("Additional Dead (kN/m²)", 0.0, 5.0, 1.0, 0.1, key="add_dead")
        st.session_state.eng_params["glazing_ratio"] = st.slider("Glazing Ratio", 0.05, 0.8, 0.2, key="glaz_ratio")
        st.session_state.eng_params["orientation"] = st.selectbox("Orientation", ["north","south","east","west"], key="orient")

    with st.expander("⚙️ Game Settings"):
        st.session_state.config["generations"] = st.slider("Generations", 2, 20, 5, key="gen_slider")
        st.session_state.config["mutation_rate"] = st.slider("Mutation Rate", 0.0, 1.0, 0.1, 0.05, key="mut_rate")
        st.session_state.config["population_size"] = st.number_input("Population Size", 2, 50, 10, key="pop_size")

    if st.button("🚪 Logout"):
        save_memory(username, mem)
        for key in ["logged_in","username","user_data","memory","active_building"]:
            if key in st.session_state:
                if key == "memory": st.session_state[key] = DEFAULT_STATE.copy()
                else: st.session_state[key] = None
        st.rerun()

# Page routing
if page == "Command Center":
    command_center_page()
elif page == "Evolution Chamber":
    evolution_chamber_page()
elif page == "Structural Analysis":
    structural_analysis_page()
elif page == "Archives":
    archives_page()
