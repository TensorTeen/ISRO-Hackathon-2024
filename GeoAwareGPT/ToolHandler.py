from .tools.database_integration import CoordinateTool
from .tools.database_integration import NearbyLandmarksTool
from .tools.image_segment import ImageSegmentTool


class ToolHandler:
    def __init__(self):
        self.tools = {
            "get_nearby_hospitals": CoordinateTool(),
        }

    async def call_tool(self, tool_name, args):
        return self.tools[tool_name].run(args)

    async def handle_tool(self, llm_output):
        tool_results = {}
        for i in range(len(llm_output)):
            tool_name = llm_output[i]["name"]
            args = llm_output[i]["args"]
            tool_output = await self.call_tool(tool_name, args)
            tool_results[tool_name] = tool_output
        return tool_results
