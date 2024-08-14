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
    Weather,
)
from GeoAwareGPT.tools.azure_integration.find_distance import FindDistance
from GeoAwareGPT.tools.image_segment import SegmentationTool
from GeoAwareGPT.tools.RAG_Tool import KnowledgeBase
from GeoAwareGPT.tools.database_integration.sql_bot import SQLGenerator
from GeoAwareGPT.tools.database_integration.get_landuse_data import GetLanduseData
from GeoAwareGPT.tools.database_integration.get_railway_length import GetRailwayLength

litellm.set_verbose = False  # type: ignore
with open("./system_prompt.txt") as fh:
    SYSTEM_PROMPT = fh.read()
tools = [
    GeoCode(),
    SearchPOI(),
    GeoDecode(),
    SatelliteImage(),
    Weather(),
    SegmentationTool(),
    FindDistance(),
    SQLGenerator(),
    GetLanduseData(),
    GetRailwayLength(),
]
states = [
    BaseState(
        name="GlobalState",
        goal="To Answer the user's query regarding geography using the tools available to the assistant",
        instructions="""- CALL ONLY ONE TOOL AT A TIME and respond to the user with the information fetched from the tool.
        - If the query requires you to decide based on some information or if it involves Geo-Technical Terms that you need to calculate then use the TOOL:KnowledgeBase to get the information about it and use that information to take the decision as a whole. 
        - YOUR OUTPUT SHOULD BE GROUNDED ON THE TOOL OUTPUT, DO NOT HALLUCINATE INFORMATION. Only if you are sure that you have answered the user's query then do not call any tools. 
        - Call tool with the right argument types. Use float or int for any numerical inputs
        - Give detailed answer about the query asked by the user, try to answer and solve the query as much as possible using the data available through different tools
        - TOOL:SQLGenerator contains information on roads, railways, landuse, places, points""",
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
    st.session_state.messages = []
    st.session_state.initialized = True
    st.session_state.agent.set_system_prompt(SYSTEM_PROMPT)
    st.session_state.AUA = cast(bool, True)

st.title("GeoAwareGPT")
st.write(
    "Welcome to GeoAwareGPT, your friendly conversational assistant for geography-related queries."
)
for user_input in st.session_state.messages:
    with st.chat_message(user_input["role"]):
        content = user_input["content"]
        if isinstance(content, Image.Image):
            st.image(content, use_column_width=True)
        else:
            st.markdown(content)

agent = st.session_state.agent

img_file: Optional[io.BytesIO] = st.file_uploader(
    "Upload an Image", accept_multiple_files=False, type="png"
)
image_input: Optional[Image.Image] = Image.open(img_file) if img_file else None
user_input = st.chat_input("Please enter your query...")
if image_input:
    agent.add_input_image(image_input)  # ! Must be done before query
    st.session_state.messages.append({"role": "User", "content": image_input})
# user_input = st.text_input("User Query", "")
if user_input:
    with st.chat_message("User"):
        st.markdown(f"{user_input}")
    st.session_state.messages.append({"role": "User", "content": user_input})
    c = 0
    agent.add_user_message(user_input)
    while True:
        print("Iteration:", c)
        if c > 10:
            st.write("Too many iterations, breaking")
            break
        if st.session_state.AUA:
            image, text, AUA, audio = asyncio.run(agent.agent_loop())
            if image:
                for img in image.values():
                    st.image(img.image, use_column_width=True)
                    st.session_state.messages.append(
                        {"role": "Assistant", "content": img.image}
                    )
            with st.chat_message("Audio"):
                st.markdown(f"Audio: {audio}")
            with st.chat_message("Assistant"):
                st.markdown(f"Tool Result: {text}")
            st.session_state.messages.append({"role": "Assistant", "content": text})
            st.session_state.messages.append({"role": "Audio", "content": audio})
            st.session_state.AUA = AUA
            c += 1
            continue
        else:
            break
    st.session_state.AUA = True
