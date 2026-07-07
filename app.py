import streamlit as st
from ui.pages import command_center, evolution_chamber, archives
from core.auth import init_session, login_page

init_session()
if not st.session_state.logged_in:
    login_page()
else:
    page = st.sidebar.selectbox("Navigate", ["Command Center", "Evolution Chamber", "Archives"])
    if page == "Command Center":
        command_center.render()
    elif page == "Evolution Chamber":
        evolution_chamber.render()
    else:
        archives.render()
