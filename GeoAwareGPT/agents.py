from litellm import acompletion
import os, sys

from .schema import GeminiModelConfig, ChatBuilder, BaseTool, BaseState
from dotenv import load_dotenv

load_dotenv()


class Model:
    def __init__(self) -> None:
        pass

    async def generate(self, messages: ChatBuilder):
        "This method should be implemented by all child classes for prompt generation"
        raise NotImplementedError(
            "This method is meant to be implemented by child classes"
        )


class GeminiModel(Model):
    def __init__(self, model_config: GeminiModelConfig = GeminiModelConfig()):
        self.model_config = model_config
        self.check_api_key()
        self.input_params = model_config.__dict__()

    def check_api_key(self):
        """Check if the API key is available in the environment."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print(
                "Please set the GEMINI_API_KEY environment variable with the API key."
            )
            sys.exit(1)

    async def generate(
        self,
        messages: ChatBuilder,
    ):
        """Generate a response for the given messages."""
        return await acompletion(
            messages=messages.chat,
            **self.input_params,
        )


class Agent:
    def __init__(self, model: Model | None = None):
        self.model = model or GeminiModel()
        self.messages = ChatBuilder()
        self.states: list[BaseState] = []

    def set_system_prompt(self, prompt: str):
        self.messages.system_message(prompt + "\n" + str(self.states[0]))

    def add_user_message(self, message: str):
        self.messages.user_message(message)

    def add_assistant_message(self, message: str):
        self.messages.assistant_message(message)

    async def get_assistant_response(self):
        response = await self.model.generate(self.messages)
        if response and response.choices:
            answer = response.choices[0].message.content
        else:
            raise RuntimeError("No response from the model")
        self.add_assistant_message(answer)
        return answer

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)
