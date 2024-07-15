
class BaseTool():
    def __init__(self, name, description, version):
        self.name = name
        self.description = description
        self.version = version
        self.args = []
        self.tool_type = "AU" # Assistant 

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return f"{self.name} - {self.description} - {self.version} - {self.args}"