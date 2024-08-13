import streamlit as st
from streamlit_float import float_init
from file_chat_input import file_chat_input
float_init()
container = st.container()
with container:
    input = file_chat_input('WHO ARE YOU?')
    