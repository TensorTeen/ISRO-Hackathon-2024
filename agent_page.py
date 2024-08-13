import asyncio
import json
from json import JSONDecodeError
from PIL import Image
from typing import cast, Optional
import io

import streamlit as st
import litellm

from GeoAwareGPT import Agent, GeminiModel, GeminiModelConfig, ToolHandler
from GeoAwareGPT.schema import BaseTool, BaseState
from GeoAwareGPT.tools.azure_integration import (
    GeoCode,
    SearchPOI,
    GeoDecode,
    SatelliteImage,
)
litellm.set_verbose = True # type: ignore
with open('./system_prompt.txt') as fh:
    SYSTEM_PROMPT = fh.read()
tools = [GeoCode(), SearchPOI(), GeoDecode(), SatelliteImage()]
states = [
    BaseState(
        name="GlobalState",
        goal="To Answer the user's query regarding geography using the tools available to the assistant",
        instructions="1.CALL ONE TOOL AT A TIME and respond to the user with the information fetched from the tool. YOUR OUTPUT SHOULD BE GROUNDED ON THE TOOL OUTPUT, DO NOT HALLUCINATE INFORMATION. If you have answered the user's query then do not call any tools",
        tools=tools,
    )
]
tool_handler = ToolHandler(tools=tools)
if "initialized" not in st.session_state or not st.session_state.initialized:
    print("Initializing agent")
    st.session_state.agent = Agent(
        model=GeminiModel(
            model_config=GeminiModelConfig(model_name="gemini/gemini-1.5-flash")
        ),
        states=states,
    )
    st.session_state.initialized = True
    st.session_state.agent.set_system_prompt(SYSTEM_PROMPT)
    st.session_state.AUA = cast(bool, True)

agent = st.session_state.agent


st.title("GeoAwareGPT")
st.write(
    "Welcome to GeoAwareGPT, your friendly conversational assistant for geography-related queries."
)
st.write("Please enter your query below:")
user_input = st.text_input("User Query", "")
img_file: Optional[io.BytesIO] = st.file_uploader(
    "Upload an Image", accept_multiple_files=False, type="png"
)
image_input: Optional[Image.Image] = Image.open(img_file) if img_file else None

if st.button("Submit"):
    c = 0
    query = user_input
    if image_input:
        agent.add_input_image(image_input) # ! Must be done before query
        agent.add_user_message(query)
    while True:
        print("Iteration:", c)
        if c > 10:
            st.write("Too many iterations, breaking")
            break
        if st.session_state.AUA:
            image, text, AUA, audio = asyncio.run(agent.agent_loop())
            if image:
                for img in image.values():
                    st.image(img.image)
            st.write("Audio", audio)
            st.write("Tool Result:", text)
            st.session_state.AUA = AUA
            c += 1
            continue
        else:
            break
    st.session_state.AUA = True
