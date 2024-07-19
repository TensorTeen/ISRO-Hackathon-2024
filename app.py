import streamlit as st

agent_page = st.Page(
    "agent_page.py", title="Create entry", icon=":material/add_circle:". 
)
agent_page.
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg = st.navigation(
    [
        agent_page,
    ],
)

pg.run()
