class ToolHandler:
    def __init__(self, tools):
        self.tools = tools
        self.tools = {tool.name: tool for tool in tools}

    async def call_tool(self, tool_name, args):
        return self.tools[tool_name].run(**args)

    async def handle_tool(self, llm_output):
        tool_results = {}
        for i in range(len(llm_output)):
            tool_name = llm_output[i]["name"]
            args = llm_output[i]["args"]
            if self.tools[tool_name].tool_type == "AUA":
                tool_results["AUA"] = True
            try:
                tool_output = await self.call_tool(tool_name, args)
            except:
                tool_output = "An error occurred while running the tool."
            tool_results[tool_name] = tool_output
        return tool_results
