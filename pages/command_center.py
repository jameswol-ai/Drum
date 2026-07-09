import streamlit as st
import uuid
from datetime import datetime
from main import (
    log_event, update_quests, grant_quest_rewards, add_xp, get_user,
    save_memory, simulate_evolution, Building, show_building
)

def command_center_page():
    st.title("📊 Command Center")
    mem = st.session_state.memory
    username = st.session_state.username
    col1, col2, col3 = st.columns(3)
    col1.metric("Buildings", len(mem["buildings"]))
    col2.metric("Sessions", len(mem["sessions"]))
    col3.metric("Badges", "🏅" * len(st.session_state.user_data.get("badges", [])))

    st.subheader("Quick Actions")
    if st.button("🏗️ Generate Random Building"):
        best, trend = simulate_evolution(st.session_state.config)
        mem["buildings"].append(best.to_dict())
        mem["sessions"].append({
            "id": str(uuid.uuid4())[:6],
            "building_id": best.id,
            "time": datetime.now().isoformat()
        })
        st.session_state.active_building = best
        log_event(username, mem, f"Quick build: {best.name}")
        update_quests(username, mem, "evolution", {"plan": best.plan})
        grant_quest_rewards(username, mem, on_level_up=st.balloons)
        add_xp(username, int(best.score * 2))
        st.session_state.user_data = get_user(username)
        save_memory(username, mem)
        st.success(f"Created building {best.name} with score {best.score}")
        st.rerun()

    if st.session_state.active_building:
        show_building(st.session_state.active_building, "Active")
    else:
        st.info("No active building. Generate one above or go to Evolution Chamber.")

    st.subheader("Recent Logs")
    for log in reversed(mem["logs"][-5:]):
        st.caption(f"`{log['time'][11:19]}` – {log['msg']}")
