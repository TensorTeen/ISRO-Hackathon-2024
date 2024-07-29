from GeoAwareGPT import GeminiModel, Agent, GeminiModelConfig
import asyncio
import pytest


@pytest.fixture(scope="module")
def model_config():
    return GeminiModelConfig(model_name="gemini/gemini-1.5-flash")


def test_gemini_llm(agent_instance, model_config):
    # Create an instance of the GeminiLLM class
    print("test 1")
    gemini_llm = agent_instance
    gemini_llm.model = GeminiModel(model_config=model_config)
    # Test the class type
    assert isinstance(gemini_llm, Agent)
    gemini_llm.set_system_prompt(
        "Whatever the user says repeat it back as it is"
    )  # noqa
    gemini_llm.add_user_message("Hello")
    response = asyncio.run(gemini_llm.get_assistant_response())
    print("response1", response)
    assert response.strip() == "Hello"
    gemini_llm.add_user_message("How are you?")
    response = asyncio.run(gemini_llm.get_assistant_response())
    print("response2", response)
    print(gemini_llm)
    assert response.strip() == "How are you?"
