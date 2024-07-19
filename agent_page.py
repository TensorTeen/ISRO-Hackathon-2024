import streamlit as st
from GeoAwareGPT import Agent, GeminiModel, GeminiModelConfig
import asyncio

agent = Agent(
    model=GeminiModel(
        model_config=GeminiModelConfig(model_name="gemini/gemini-1.0-pro")
    )
)

st.title("GeoAwareGPT")
input = st.text_input("Enter your Query")
st.write("You entered: ", input)
if input:
    agent.set_system_prompt("You are a helpful assistant.")
    agent.add_user_message(input)
    response = asyncio.run(agent.get_assistant_response())

    st.write("Response: ", response)
