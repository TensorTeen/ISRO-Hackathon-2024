import streamlit as st

agent_page = st.Page(
    "agent_page.py", title="Create entry", icon=":material/add_circle:"
)
st.set_page_config(page_title="GeoAwareGPT", page_icon=":material/edit:", layout="wide")
pg = st.navigation(
    [
        agent_page,
    ],
)

pg.run()
