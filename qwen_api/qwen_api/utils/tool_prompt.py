from ..core.types.response.function_tool import Function

example = Function(
    name="name of function",
    arguments={"arg name": "arg value", "arg name": "arg value"},
)

TOOL_PROMPT_SYSTEM = """
\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>\n
{list_tools}
\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call>
"""
