import streamlit as st
import uuid
from datetime import datetime
from main import (
    log_event, update_quests, grant_quest_rewards, add_xp, get_user,
    save_memory, simulate_evolution, generate_rhythm, generate_plan, Building,
    show_building, show_rhythm
)

def evolution_chamber_page():
    st.title("🧬 Evolution Chamber")
    st.caption("Configure evolution parameters in the sidebar under Game Settings.")
    mem = st.session_state.memory
    username = st.session_state.username

    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("🚀 EVOLVE!", type="primary"):
            with st.spinner("Mixing genes..."):
                best, trend = simulate_evolution(st.session_state.config)
                rhythm = generate_rhythm(best)
                mem["buildings"].append(best.to_dict())
                mem["rhythms"].append(rhythm)
                mem["sessions"].append({
                    "id": str(uuid.uuid4())[:6],
                    "building_id": best.id,
                    "time": datetime.now().isoformat()
                })
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
