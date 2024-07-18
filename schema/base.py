class BaseTool:
    def __init__(self, name, description, version):
        self.name = name
        self.description = description
        self.version = version
        self.args = []
        self.tool_type = "AU"  # Assistant

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return f"{self.name} - {self.description} - {self.version} - {self.args}"


class ModelConfig:
    def __init__(self, model_name, description, version="1.5"):
        self.name = model_name
        self.api_key = description
        self.version = version

    def __str__(self):
        return f"{self.name} - {self.description} - {self.version} - {self.args}"


class GeminiModelConfig(ModelConfig):
    def __init__(
        self,
        model_name="gemini/gemini-1.5-pro-latest",
        description="Gemini 1.5 Pro Model",
    ):
        super().__init__(
            model_name,
            description,
        )
