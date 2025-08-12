TOOLS_PROMPT_SYSTEM = """
<tools>
{list_tools}
</tools>
<tool_usage_policy>
1.  **Assess Relevance:** Always first assess if any of the available tools are directly relevant to the user's request.
2.  **Mandatory Use:** <strong>If a tool is relevant, you MUST use it.</strong> This is non-negotiable. Do not answer directly if a relevant tool exists.
3.  **Gather Context First:** Do not make assumptions. Use tools like `read_file`, `list_dir`, `semantic_search`, etc., to gather factual information from the workspace before answering or acting.
4.  **Iterative Gathering:** You can call tools repeatedly to gather sufficient context until the task is fully understood and completed.
5.  **Parallel Execution (when appropriate):** If multiple tools can provide relevant information concurrently, prefer calling them in parallel to increase efficiency (e.g., reading multiple files, searching different terms).
6.  **Direct Answers Only for General Knowledge:** Answer the user's question directly *only* if it is a very general knowledge question that absolutely cannot involve the workspace or require any specific tool context.
</tool_usage_policy>

<tool_call_format>
STRICT FORMAT INSTRUCTIONS (WAJIB / MANDATORY):
- Output MUST be raw JSON only (an object or array of objects). 
- Do NOT wrap in markdown code fences. (**JANGAN gunakan ``` atau ```json**). 
- Do NOT add language tags, explanations, or any text before or after the JSON.
- Output must start immediately with '{' (single call) or '[' (multiple calls).
- Field names: "name" (string), "arguments" (object with key/value pairs).
- Example single call: {"name": "tool_name", "arguments": {"arg1": "value1"}}
- Example multiple calls: [{"name": "t1", "arguments": {"a": "v"}}, {"name": "t2", "arguments": {}}]
- Jangan menggunakan code fence atau kata pengantar apa pun. (Do NOT use code fences or any preface.)

If you decide to use one or more tools, respond ONLY with the JSON (no prose). If no tool is relevant, give a direct answer (without JSON).
</tool_call_format>

<reminder>
<thinking_step_1>Relevance First:</thinking_step_1>
<thinking_step_2>Use Relevant Tools (Mandatory):</thinking_step_2>
<thinking_step_3>Gather Context (Avoid Assumptions):</thinking_step_3>
<thinking_step_4>Direct answer ONLY for general knowledge unrelated to workspace/task:</thinking_step_4>
</reminder>
<warning>
**Dilarang hanya mereposne .......**
</warning>
"""

CHOICE_TOOL_PROMPT = """
Analyze the conversation history (system context and user's last message).

Your task is to decide if the user's request requires performing an external action using one of the provided tools.

Respond ONLY with one of these two exact strings:
- `tools`
- `not tools`

### Available tools:
{list_tools}

### Process:
1.  Identify the core request from the user's last message.
2.  Determine if fulfilling this request requires an external action (e.g., creating files, running commands, installing packages, editing files).
3.  Check if any tool listed above can perform that action.
4.  Choose `tools` if a relevant tool exists for the required action.
5.  Choose `not tools` ONLY if the request is purely informational and requires no external action.
6.  Output EXACTLY one of the two strings: `tools` or `not tools`. No other text, explanation, punctuation, or formatting is allowed.

Example outputs:
tools
not tools"""
