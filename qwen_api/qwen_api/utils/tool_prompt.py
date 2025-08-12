from ..core.types.response.function_tool import Function

example = Function(
    name="name of function",
    arguments={"arg name": "arg value", "arg name": "arg value"},
)

# TOOL_PROMPT_SYSTEM = """
# You are a helpful AI assistant that can use external functions (tools) to assist the user.
#
# If the user's request matches a tool, respond ONLY with a valid JSON object containing:
# - "name" (string): The function name to call.
# - "arguments" (object): The required arguments for the function, even if empty (use {{}} if none).
#
# Strict Formatting Rules:
# - Respond ONLY with a JSON object. NO explanations, NO markdown, NO additional text.
# - Use DOUBLE QUOTES (") for all keys and string values.
# - The response MUST be **strictly valid JSON**. Do NOT respond with Python objects, do NOT use single quotes (').
# - Empty arguments → respond with `"arguments": {{}},` NOT `null` or omitted.
# - Do NOT include variables, placeholders, or any descriptive text.
#
# example:
# {output_example}
#
# Failure to follow this format will cause a system error.
#
# ---
# Available tool:
# {list_tools}
# """

TOOL_PROMPT_SYSTEM = """
You are a helpful AI assistant that must call the tool specified by the user.

The user's input (role: "user") will be the exact function name to call.
You must respond ONLY with a valid JSON object containing:
- "name" (string): The function name to call (exactly as provided in the user's input).
- "arguments" (object): The required arguments for the function, even if empty (use {{}} if none).

Strict Formatting Rules:
- Respond ONLY with a JSON object. NO explanations, NO markdown, NO extra text.
- Use DOUBLE QUOTES (") for all keys and string values.
- The response MUST be strictly valid JSON. Do NOT respond with Python objects. Do NOT use single quotes (').
- Empty arguments → respond with "arguments": {{}}, NOT null or omitted.
- Do NOT include placeholders or descriptions — only the final JSON object.

Example:
{{"name": "fetch_users", "arguments": {{"user_ids": [123]}}}}

---
Available tools:
{list_tools}
"""


# CHOICE_TOOL_PROMPT="""
# Your task is to decide whether to use tools to answer the user's question, based on the tools currently available. You must respond with one of the following two strings only:
#
# - `tools` — if ANY available tool is relevant and helpful for answering the question.
# - `not tools` — only if you are CERTAIN that a complete and accurate answer can be given WITHOUT using any tools.
#
# **Important Instructions:**
# 1. If a relevant tool is available, you MUST prefer using it — even if you could partially answer the question without it.
# 2. When multiple tools are available, focus on finding ANY tool that could be useful for the question.
# 3. Even if only ONE tool among many is relevant, you should still respond with `tools`.
# 4. Mathematical questions should use calculator tools.
# 5. API/HTTP requests should use HTTP or request tools.
# 6. Data retrieval should use appropriate data tools.
#
# **Available tools:**
# {list_tools}
#
# **Analysis approach:**
# 1. Read the user's question carefully
# 2. Check if ANY of the available tools could help answer it
# 3. If YES to step 2, respond with `tools`
# 4. If NO to step 2, respond with `not tools`
#
# **Final rule:**
# If in doubt, but any relevant tool is available, respond with `tools`.
#
# Your output must be strictly one of these two strings: `tools` or `not tools`.
#
# """

# CHOICE_TOOL_PROMPT = """
# Your task is to decide whether to use tools to answer the user's question, based on the tools currently available.
#
# You must respond ONLY in a strict JSON object format:
# {{
#   "use_tools": true/false,
#   "tool_name": "none" or "<tool_name>"
# }}
#
# ## Decision rules (neutral & actionable)
# 1. Use "use_tools": true only if the tool can be executed immediately with the information currently available in the conversation state.
# 2. If the required input for a tool is missing, do NOT select it.
# 3. If ANY tool has already been used in this conversation and has produced a result (not empty), do NOT select any tool again — unless the system message explicitly instructs you to use tools again.
# 4. Avoid selecting the same tool with identical arguments more than once in the same conversation.
# 5. If multiple tools are relevant and actionable, choose the one MOST likely to help the most.
# 6. If no tool is relevant or actionable, set "use_tools": false and "tool_name": "none".
# 7. When a question explicitly mentions a tool's name, select that tool immediately (if actionable).
#
# ## Available tools:
# {list_tools}
#
# ## Output rules:
# - Output must be valid JSON only.
# - Keys exactly: use_tools, tool_name.
# - Boolean for use_tools, string for tool_name.
# - No extra fields, no commentary, no markdown.
# """

CHOICE_TOOL_PROMPT = """
====== TOOL PLANNER ======
[PHASE: DECIDE_TOOLS ONLY]

(See SYSTEM PROMPT for more details, but always use only the JSON output format below.)

You MUST follow these rules when deciding whether to use tools:

1. Use a tool ONLY if it is truly needed and can be run NOW with the available inputs.  
   If the tool is not needed, DO NOT use any tool.
2. IF a tool has already been used and produced any result (even empty), DO NOT use any tool again — UNLESS the system explicitly instructs to run another tool.
3. If NO relevant tool is available, respond with:
    {{
        "use_tools": true/false,
        "tool_name": "none" or "<tool_name>"
    }}
4. If the user's message explicitly names a tool and it can be run, use it.
5. If the tool mentioned in the SYSTEM PROMPT is not present in the “Available tools” list, respond with:
    {{"use_tools": false, "tool_name": "none"}}.
6. If the tools in the SYSTEM PROMPT differ from the ones in “Available tools”, use the tool that is most relevant to the one mentioned in the SYSTEM PROMPT.

OUTPUT FORMAT (STRICT):
- JSON ONLY.
- Keys: "use_tools" (boolean), "tool_name" (string).
- No extra text, no markdown, no explanation.

Available tools:
{list_tools}
====== END ========
"""

# CHOICE_TOOL_PROMPT = """
# ---
# ====== TOOL PLANNER ======
# [PHASE: DECIDE_TOOLS ONLY]
#
# You MUST follow these rules when deciding whether to use tools:
#
# Rules:
# 1) Use a tool ONLY if it is REQUIRED and can run NOW with available inputs.
# 2) If has_used_tool == true → MUST return {{"use_tools": false, "tool_name":"none"}}.
# 3) If the user/system policy below mandates a specific tool/sequence, pick the FIRST unmet step that exists in Available tools.
# 4) If the named tool in the policy is NOT in Available tools, return {{"use_tools": false, "tool_name":"none"}} (controller will map aliases if any).
# 5) If the user explicitly names an available tool and it can run now, you MAY choose it.
# 6) If unsure or information is insufficient, choose {{"use_tools": false, "tool_name":"none"}}.
#
#
# Available tools:
# {list_tools}
# ====== END =======
# """
