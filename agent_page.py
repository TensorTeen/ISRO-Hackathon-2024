import asyncio
import json
from json import JSONDecodeError
from PIL import Image
from typing import cast, Optional, List, Tuple
import io

import folium
import streamlit as st
from streamlit_folium import folium_static, st_folium
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


from asr_tts import Speech


litellm.set_verbose = False # type: ignore
with open('./system_prompt.txt') as fh:
    SYSTEM_PROMPT = fh.read()
tools = [
    GeoCode(),
    SearchPOI(),
    GeoDecode(),
    SatelliteImage(),
    Weather(),
    SegmentationTool(),
    FindDistance(),
    KnowledgeBase(),
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
        - If the query requires you to decide based on some information or if it involves Geo-Technical Terms that you need to calculate then use the TOOL:KnowledgeBase to get the information about it and use that information to take the decision as a whole.
        - TOOL:SQLGenerator contains information on roads, railways, landuse, places, points""",
        tools=tools,
    )
]
# TOOL:KnowledgeBase to get the information about it and use that information to take the decision as a whole. 
tool_handler = ToolHandler(tools=tools)

col1, col2 = st.columns(2)
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
    st.session_state.mic = None
    st.session_state.markers = []
    st.session_state.popups = []
    with col2:
        st.session_state.map = folium.Map((17.4065, 78.4772), zoom_start=5, control_scale=True)
with col2:
    mp = st.session_state.map
    for marker, popup in zip(st.session_state.markers, st.session_state.popups):
        folium.Marker(marker, popup).add_to(mp)

def bounds(markers: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    lats, lons = zip(*markers)
    return (min(lats), min(lons)), (max(lats), max(lons))



with col1:
    st.title("GeoAwareGPT")
    st.write(
        "Welcome to GeoAwareGPT, your friendly conversational assistant for geography-related queries."
    )
    def on_microphone():
        audio_input = st.chat_input("Please speak...")
        if not language.split('-')[0] == 'en':
            result, _ = translator.translate_speech(language, 'en')
            st.session_state.mic = result
        else:
            user_input = translator.recognize_from_microphone()
            st.session_state.mic = user_input
    img_file: Optional[io.BytesIO] = st.file_uploader(
        "Upload an Image", accept_multiple_files=False, type="png"
    )
with st.sidebar:
    lang_map = {
        'en-US': 'en-US',
        'हिन्दी': 'hi-IN'
    }
    language: str = st.selectbox('Language', ('en-US', 'हिन्दी'))
    language = lang_map[language]
    microphone = st.button('Microphone', on_click=on_microphone)
    audio_output = st.toggle('Audio Output')
for user_input in st.session_state.messages:
    with col1:
        with st.chat_message(user_input["role"]):
            content = user_input["content"]
            if isinstance(content, Image.Image):
                st.image(content, use_column_width=True)
            else:
                st.markdown(content)

agent = st.session_state.agent
with col1:
    image_input: Optional[Image.Image] = Image.open(img_file) if img_file else None
    if image_input:
        agent.add_input_image(image_input) # ! Must be done before query
        st.session_state.messages.append({
            "role": "User",
            "content": image_input
        })
    translator = Speech()
    if st.session_state.mic:
        if not language.split('-')[0] == 'en':
            result = st.session_state.mic
            user_input = result.text
        else:
            user_input = st.session_state.mic
        st.session_state.mic = None
    else:
        user_input = st.chat_input("Please enter your query...")
        if user_input and language.split('-')[0] != 'en':
            user_input = translator.translate_text(user_input, from_language=language, to_language='en')
    # user_input = st.text_input("User Query", "")
    if user_input:
        if not microphone:
            with st.chat_message('User'):
                st.markdown(f'{user_input}')
            st.session_state.messages.append({"role": "User", "content": user_input})
        else:
            with st.chat_message('User'):
                st.markdown(f'{user_input}')
            st.session_state.messages.append({"role": "User", "content": user_input})
if user_input:
    c = 0
    agent.add_user_message(user_input if language.split('-')[0] == 'en' else result.translations['en'])
    while True:
        print("Iteration:", c)
        if c > 10:
            st.write("Too many iterations, breaking")
            break
        if st.session_state.AUA:
            image, text, AUA, audio, custom = asyncio.run(agent.agent_loop())
            if image:
                for img in image.values():
                    with col1:
                        st.image(img.image, use_column_width=True)
                    st.session_state.messages.append({
                        "role": "Assistant",
                        "content": img.image
                    })
            if custom:
                for key, val in custom.items():
                    if val.metadata['type'] == 'coordinates':
                        mp.location = val.output['latitude'], val.output['longitude']
                        folium.Marker(mp.location, popup=val.metadata.get('name')).add_to(mp)
                        st.session_state.markers.append(val.output)
                        if len(st.session_state.markers) > 1:
                            mp.fit_bounds(bounds(st.session_state.markers))
                        # with col2:
                        #     folium_static(mp, width=600, height=750)
                        with col2:
                            # fs = folium_static(mp, width=600, height=750)
                            pass
            else:
                with col2:
                    # fs = folium_static(mp, width=600, height=750)
                    pass
            
            with col1:
                with st.chat_message('Audio'):
                    if not language.split('-')[0] == 'en':
                        audio = translator.translate_text(audio)
                    st.markdown(f'Audio: {audio}')
                    if audio_output:
                        translator.text_to_speech(audio, language.split('-')[0]+'-IN')
                with st.chat_message('Assistant'):
                    st.markdown(f'Tool Result: {text}')
            st.session_state.messages.append({"role": "Assistant", "content": text})
            st.session_state.messages.append({"role": "Audio", "content": audio})
            st.session_state.AUA = AUA
            c += 1
            continue
        else:
            print("Breaking")
            break
    st.session_state.AUA = True
with col2:
    fs = folium_static(mp, width=600, height=750)

