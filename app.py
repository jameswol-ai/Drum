import streamlit as st
from core.auth import load_users, create_user, authenticate, get_user, update_user_data, add_xp
from core.memory import load_memory, save_memory, log_event, DEFAULT_STATE
from core.building import Building
from ui.style import GAME_CSS
from ui.components import show_xp_bar
from ui.pages import command_center, evolution_chamber, archives

st.set_page_config(page_title="DRUM Studio", page_icon="🥁", layout="wide", initial_sidebar_state="expanded")
st.markdown(GAME_CSS, unsafe_allow_html=True)

# --- Session init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.memory = DEFAULT_STATE.copy()
    st.session_state.active_building = None
    st.session_state.config = {"generations": 5, "style": "minimal"}

# --- Auto-create admin if no users ---
if not load_users():
    create_user("admin", "admin123", role="admin")

# --- Login page ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🥁 DRUM</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-family: \"Press Start 2P\"; color: #a78bfa;'>Login or create your architect identity</p>", unsafe_allow_html=True)
        with st.form("auth_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            register_btn = st.form_submit_button("Register")

            if login_btn:
                user = authenticate(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_data = user
                    st.session_state.memory = load_memory(username)
                    # restore active building
                    mem = st.session_state.memory
                    if mem["sessions"]:
                        last = mem["sessions"][-1]
                        bid = last.get("building_id")
                        match = next((b for b in mem["buildings"] if b.get("id") == bid), None)
                        if match:
                            st.session_state.active_building = Building.from_dict(match)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

            if register_btn:
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    try:
                        create_user(username, password)
                        st.success("Account created! You can now log in.")
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

# --- Logged in ---
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 15px;">
        <div style="font-size: 18px; color: #fbbf24;">👤 {username}</div>
        <div style="font-size: 12px; color: #94a3b8;">{user_data.get('role', 'user').upper()}</div>
    </div>
    """, unsafe_allow_html=True)
    show_xp_bar(user_data)
    st.markdown("---")
    page = st.radio("Navigate", ["Command Center", "Evolution Chamber", "Archives"])

    # Admin link
    if user_data.get("role") == "admin":
        if st.sidebar.checkbox("🔧 User Management"):
            # Admin panel
            st.title("🛡️ Admin Panel – User Management")
            users = load_users()
            for u in users:
                cols = st.columns([3,1,1])
                cols[0].write(f"**{u['username']}** (Role: {u['role']}, Lvl {u['level']})")
                if u["username"] != username:
                    if cols[1].button("🗑️ Delete", key=f"del_{u['username']}"):
                        users.remove(u)
                        save_users(users)
                        st.rerun()
                    if cols[2].button("⭐ Make Admin", key=f"adm_{u['username']}") and u["role"] != "admin":
                        u["role"] = "admin"
                        save_users(users)
                        st.rerun()
                else:
                    cols[1].write("(you)")
            st.stop()

    st.markdown("---")
    with st.expander("⚙️ Settings"):
        st.session_state.config["generations"] = st.slider("Generations", 2, 20, st.session_state.config["generations"])
        st.session_state.config["style"] = st.selectbox("Style", ["minimal", "bold", "organic"])

    if st.button("🚪 Logout"):
        save_memory(username, mem)
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_data = None
        st.session_state.memory = DEFAULT_STATE.copy()
        st.session_state.active_building = None
        st.rerun()

# --- Page routing ---
if page == "Command Center":
    command_center.render()
elif page == "Evolution Chamber":
    evolution_chamber.render()
else:
    archives.render()
