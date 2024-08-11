from typing import List, Dict
from asyncio import iscoroutinefunction

from .schema import BaseTool

DEBUG = True
class ToolHandler:
    def __init__(self, tools: List[BaseTool]):
        self.tools = tools
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    async def call_tool(self, tool_name, args):
        return self.tools[tool_name].run(**args) if not iscoroutinefunction(self.tools[tool_name].run) else await self.tools[tool_name].run(**args)

    async def handle_tool(self, llm_output):
        tool_results = {}
        for i in range(len(llm_output)):
            tool_name = llm_output[i]["name"]
            args = llm_output[i]["args"]
            if self.tools[tool_name].tool_type == "AUA":
                tool_results["AUA"] = True
            try:
                tool_output = await self.call_tool(tool_name, args)
            except Exception as e:
                tool_output = "An error occurred while running the tool."
                if DEBUG:
                    print(llm_output)
                    raise e

            if self.tools[tool_name].tool_output == "image":
                
                # tool_results['image'].append(tool_output)
                ...
            tool_results[tool_name] = tool_output
        return tool_results
# class ToolImageOutput:
#     """A class representing the output of a tool with an image.

#     Attributes:
#         image_url (str): The URL of the image output.
#         args (dict): The arguments for the tool.

#     Methods:
#         __str__(): Returns a string representation of the tool image output.
#     """

#     def __init__(self):
#         self.image = None

#     def __str__(self):
#         """Returns a string representation of the tool image output."""
#         return f"Image URL: {self.image}"