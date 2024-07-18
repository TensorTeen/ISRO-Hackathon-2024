from typing import List


class BaseTool:
    """A base class representing a tool.

    Attributes:
        name (str): The name of the tool.
        description (str): The description of the tool.
        version (str): The version of the tool.
        args (List): A list of arguments for the tool.
        tool_type (str): The type of the tool.

    Methods:
        run(): Abstract method to run the tool.
        __str__(): Returns a string representation of the tool.
    """

    def __init__(self, name: str, description: str, version: str):
        self.name = name
        self.description = description
        self.version = version
        self.args: List = []
        self.tool_type: str = "AU"  # Assistant

    def run(self):
        """Abstract method to run the tool."""
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        """Returns a string representation of the tool."""
        return f"{self.name} - {self.description} - {self.version} - {self.args}"


class ModelConfig:
    """A class representing the configuration of a model.

    Attributes:
        name (str): The name of the model.
        api_key (str): The API key for the model.
        version (str): The version of the model.

    Methods:
        __str__(): Returns a string representation of the model configuration.
    """

    def __init__(self, model_name: str, description: str, version: str = "1.5"):  # noqa
        self.model_name = model_name
        self.api_key = description
        self.version = version

    def __str__(self):
        """Returns a string representation of the model configuration."""
        return (
            f"{self.name} - {self.description} - {self.version} - {self.args}"  # noqa
        )


class GeminiModelConfig(ModelConfig):
    """A class representing the configuration of the Gemini model.

    Attributes:
        model_name (str): The name of the Gemini model.
        description (str): The description of the Gemini model.

    Methods:
        __init__(): Initializes the Gemini model configuration.
    """

    def __init__(
        self,
        model_name: str = "gemini/gemini-1.5-pro-latest",
        description: str = "Gemini 1.5 Pro Model",
        response_format: str | None = None,
    ):
        super().__init__(
            model_name,
            description,
        )
        self.response_format = response_format

    def __dict__(self):
        return {
            "model": self.model_name,
            "response_format": self.response_format,
        }


class QueryInput:
    """A class representing a query input.

    Attributes:
        query (str): The query string.
        image (Any): The image associated with the query.

    Methods:
        __str__(): Returns a string representation of the query input.
    """

    def __init__(self, query: str, image=None):
        self.query = query
        self.image = image

    def __str__(self):
        """Returns a string representation of the query input."""
        return f"{self.query}"


class ChatBuilder:
    """A class representing a chat builder.

    Attributes:
        chat (str): The chat string.

    Methods:
        __str__(): Returns a string representation of the chat builder.
    """

    def __init__(
        self,
    ):
        self.chat: List[dict] = []
        self.roles: List[str] = []

    def __str__(self):
        """Returns a string representation of the chat builder."""
        return f"{self.chat}"

    def append(self, role: str, content: str):
        self.chat.append({"role": role, "content": content})
        self.roles.append(role)

    def insert(self, index: int, role: str, content: str):
        self.chat.insert(index, {"role": role, "content": content})
        self.roles.insert(index, role)

    def replace(self, index: int, role: str, content: str):
        self.chat[index] = {"role": role, "content": content}
        self.roles.insert(index, role)

    def system_message(self, content: str):
        if "system" not in self.roles:
            self.insert(0, "system", content)
        else:
            self.replace(0, "system", content)

    def user_message(self, content: str):
        self.append("user", content)

    def assistant_message(self, content: str):
        self.append("assistant", content)

    def build(self):
        return self.chat
