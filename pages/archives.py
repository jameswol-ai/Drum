import streamlit as st
from main import Building, show_building, show_rhythm

def archives_page():
    st.title("🗄️ Archives")
    mem = st.session_state.memory
    if mem["buildings"]:
        for i, bdict in enumerate(reversed(mem["buildings"])):
            building = Building.from_dict(bdict)
            with st.expander(f"{building.name} – Score {building.score}"):
                show_building(building)
                if i < len(mem["rhythms"]):
                    show_rhythm(mem["rhythms"][-i-1])
    else:
        st.info("No buildings yet. Use the Command Center or Evolution Chamber to create one.")
