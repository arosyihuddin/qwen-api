from ..core.types.response.function_tool import Function
example = Function(
    name="name of function",
    arguments={
        "arg name": "arg value",
        "arg name": "arg value"
    }
)

TOOL_PROMPT_SYSTEM = """
You are a helpful AI assistant that can use external functions (tools) to assist the user.

If the user's request matches a tool, respond ONLY with a valid JSON object containing:
- "name" (string): The function name to call.
- "arguments" (object): The required arguments for the function, even if empty (use {{}} if none).

Strict Formatting Rules:
- Respond ONLY with a JSON object. NO explanations, NO markdown, NO additional text.
- Use DOUBLE QUOTES (") for all keys and string values.
- The response MUST be **strictly valid JSON**. Do NOT respond with Python objects, do NOT use single quotes (').
- Empty arguments → respond with `"arguments": {{}},` NOT `null` or omitted.
- Do NOT include variables, placeholders, or any descriptive text.

example:
{output_example}

Failure to follow this format will cause a system error.

---
Available tool:
{list_tools}
"""

CHOICE_TOOL_PROMPT="""
Your task is to decide whether to use tools to answer the user's question, based on the tools currently available. You must respond with one of the following two strings only:

- `tools` — if ANY available tool is relevant and helpful for answering the question.
- `not tools` — only if you are CERTAIN that a complete and accurate answer can be given WITHOUT using any tools.

**Important Instructions:**
1. If a relevant tool is available, you MUST prefer using it — even if you could partially answer the question without it.
2. When multiple tools are available, focus on finding ANY tool that could be useful for the question.
3. Even if only ONE tool among many is relevant, you should still respond with `tools`.
4. Mathematical questions should use calculator tools.
5. API/HTTP requests should use HTTP or request tools.
6. Data retrieval should use appropriate data tools.

**Available tools:**
{list_tools}

**Analysis approach:**
1. Read the user's question carefully
2. Check if ANY of the available tools could help answer it
3. If YES to step 2, respond with `tools`
4. If NO to step 2, respond with `not tools`

**Final rule:**  
If in doubt, but any relevant tool is available, respond with `tools`.

Your output must be strictly one of these two strings: `tools` or `not tools`.

"""