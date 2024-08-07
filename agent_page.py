import streamlit as st
from GeoAwareGPT import Agent, GeminiModel, GeminiModelConfig, ToolHandler
from GeoAwareGPT.schema import BaseTool, BaseState
from GeoAwareGPT.tools.database_integration import CoordinateTool
import asyncio, json
from json import JSONDecodeError

SYSTEM_PROMPT = """You are a helpful conversational assistant. Below are the details about the usecase which you need to abide by stricly:
<usecase_details>
you are a conversational agent that helps users with their queries related to geography. You have access to a variety of tools that can help you fetch information about a location, and more.
</usecase_details>

You are currently in a specific state of the conversational-flow described below 
Details about the current-state:
Instructions to be followed:
- The thought should be very descriptive and should include the reason for selecting the tool and the parameters to be passed to the tool.
- Make the conversation coherent. The responses generated should feel like a normal conversation. 
- Only use the tools available in the should be there in the assistant outputs
- Do not generate unicode characters or hindi characters at all.
- The audio should be engaging, short and crisp. It should be more human conversation like.

Bot specific instructions to be followed: (Note: These instructions are specific to the bot type and should be followed strictly ovveriding the general instructions)
- Sentences in 'audio' key should be short and not verbose.
- Use informal, more conversational and colloquial language. Avoid decorative words and choice of too much drama in your language.
- Avoid bulleted lists, markdowns, structured outputs, and any special characters like double quotes, single quotes, or hyphen etc in your responses.
- Avoid any numericals or SI units in your 'audio' outputs. Ex: if you want to say 12:25, say twelve twenty five, or if you want to say 100m^2, say hundred meter square since this interaction is over call. Other fields can have numericals.
- Avoid any emoji or smiley faces since this interaction is over call.
- First transition to the end conversation state and then call the end_conversation tool.
- Call relevant tools whether it be some api or a RAG tool to fetch context needed to answer any query that the user might have. First decide if a tool call is needed in the thought and then call the appropriate tool. Respond to the user with a variant of 'let me check that for you' and then call the tool in the same turn.
- Audio should not be empty unless transition_state tool is called.

Respond to the user in the conversation strictly following the below JSON format:
{
    "thought": "...",  # Thought process of the bot to decide what cotent to reply with, which tool(s) to call, briefly describing reason for tool arguments as well
    "tool_calls": [{"name": "...", "args": {...}}, {"name": "...", "args": {...}}, ...],  # List of tools to be called along with the appropriate arguments
    "audio": "...",  # Audio response in simple, short, sentence segmented format
}
"""

tool_handler = ToolHandler()
if "initialized" not in st.session_state or not st.session_state.initialized:
    print("Initializing agent")
    st.session_state.agent = Agent(
        model=GeminiModel(
            model_config=GeminiModelConfig(model_name="gemini/gemini-1.5-flash")
        )
    )
    st.session_state.initialized = True
    state = BaseState(
        name="GlobalState",
        goal="To Answer the user's query regarding geography using the tools available to the assistant",
        instructions="1. Given the location name and what to landmark to search nearby use the TOOL:get_coordinates to fetch the latitude and longitude of the location. 2. Output this information to the user. You can follow this step by step process to answer the user's query. CALL ONE TOOL AT A TIME and respond to the user with the information fetched from the tool. YOUR OUTPUT SHOULD BE GROUNDED ON THE TOOL OUTPUT, DO NOT HALLUCINATE INFORMATION.",
        tools=[CoordinateTool()],
    )
    st.session_state.agent.states.append(state)
    st.session_state.agent.set_system_prompt(SYSTEM_PROMPT)


agent = st.session_state.agent


st.title("GeoAwareGPT")
st.write(
    "Welcome to GeoAwareGPT, your friendly conversational assistant for geography-related queries."
)
st.write("Please enter your query below:")
user_input = st.text_input("User Query", "")

if st.button("Submit"):
    agent.add_user_message(user_input)
    response = asyncio.run(agent.get_assistant_response())
    try:
        response = json.loads(response)
        agent.add_assistant_message(response["audio"])
    except JSONDecodeError:
        st.write(response)
    st.write(agent.messages)
