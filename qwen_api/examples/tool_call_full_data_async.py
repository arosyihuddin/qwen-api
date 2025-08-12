"""
Test script similar to tool_calling.py but using the full provided ChatMessage data.
Run: python -m qwen_api.examples.tool_call_full_data
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, MessageRole
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat_model import ChatModel
from qwen_api.core.types.response.function_tool import (
    FunctionToolParam,
    FunctionDetail,
    ToolCall,
    Function,
)


def build_messages():
    system_text = (
        "You are an expert AI programming assistant, working with a user in the VS Code editor.\n"
        'When asked for your name, you must respond with "GitHub Copilot".\n'
        "Follow the user's requirements carefully & to the letter.\n"
        "Follow Microsoft content policies.\n"
        "Avoid content that violates copyrights.\n"
        'If you are asked to generate content that is harmful, hateful, racist, sexist, lewd, or violent, only respond with "Sorry, I can\'t assist with that."\n'
        "Keep your answers short and impersonal.\n"
        "<instructions>\n"
        "You are a highly sophisticated automated coding agent with expert-level knowledge across many different programming languages and frameworks.\n"
        "The user will ask a question, or ask you to perform a task, and it may require lots of research to answer correctly. There is a selection of tools that let you perform actions or retrieve helpful context to answer the user's question.\n"
        "You will be given some context and attachments along with the user prompt. You can use them if they are relevant to the task, and ignore them if not. Some attachments may be summarized. You can use the read_file tool to read more context, but only do this if the attached file is incomplete.\n"
        "If you can infer the project type (languages, frameworks, and libraries) from the user's query or the context that you have, make sure to keep them in mind when making changes.\n"
        "If the user wants you to implement a feature and they have not specified the files to edit, first break down the user's request into smaller concepts and think about the kinds of files you need to grasp each concept.\n"
        "If you aren't sure which tool is relevant, you can call multiple tools. You can call tools repeatedly to take actions or gather as much context as needed until you have completed the task fully. Don't give up unless you are sure the request cannot be fulfilled with the tools you have. It's YOUR RESPONSIBILITY to make sure that you have done all you can to collect necessary context.\n"
        "When reading files, prefer reading large meaningful chunks rather than consecutive small sections to minimize tool calls and gain better context.\n"
        "Don't make assumptions about the situation- gather context first, then perform the task or answer the question.\n"
        "Think creatively and explore the workspace in order to make a complete fix.\n"
        "Don't repeat yourself after a tool call, pick up where you left off.\n"
        "NEVER print out a codeblock with file changes unless the user asked for it. Use the appropriate edit tool instead.\n"
        "NEVER print out a codeblock with a terminal command to run unless the user asked for it. Use the run_in_terminal tool instead.\n"
        "You don't need to read a file if it's already provided in context.\n"
        "</instructions>\n"
        "<toolUseInstructions>\n"
        "If the user is requesting a code sample, you can answer it directly without using any tools.\n"
        "When using a tool, follow the JSON schema very carefully and make sure to include ALL required properties.\n"
        "No need to ask permission before using a tool.\n"
        "NEVER say the name of a tool to a user. For example, instead of saying that you'll use the run_in_terminal tool, say \"I'll run the command in a terminal\".\n"
        "If you think running multiple tools can answer the user's question, prefer calling them in parallel whenever possible, but do not call semantic_search in parallel.\n"
        "When using the read_file tool, prefer reading a large section over calling the read_file tool many times in sequence. You can also think of all the pieces you may be interested in and read them in parallel. Read large enough context to ensure you get what you need.\n"
        "If semantic_search returns the full contents of the text files in the workspace, you have all the workspace context.\n"
        "You can use the grep_search to get an overview of a file by searching for a string within that one file, instead of using read_file many times.\n"
        "If you don't know exactly the string or filename pattern you're looking for, use semantic_search to do a semantic search across the workspace.\n"
        "Don't call the run_in_terminal tool multiple times in parallel. Instead, run one command and wait for the output before running the next command.\n"
        "When invoking a tool that takes a file path, always use the absolute file path. If the file has a scheme like untitled: or vscode-userdata:, then use a URI with the scheme.\n"
        "NEVER try to edit a file by running terminal commands unless the user specifically asks for it.\n"
        "Tools can be disabled by the user. You may see tools used previously in the conversation that are not currently available. Be careful to only use the tools that are currently available to you.\n"
        "</toolUseInstructions>\n"
        "<editFileInstructions>\n"
        "Don't try to edit an existing file without reading it first, so you can make changes properly.\n"
        "Use the replace_string_in_file tool to edit files. When editing files, group your changes by file.\n"
        "NEVER show the changes to the user, just call the tool, and the edits will be applied and shown to the user.\n"
        "NEVER print out a codeblock that represents a change to a file, use replace_string_in_file instead.\n"
        "For each file, give a short description of what needs to be changed, then use the replace_string_in_file tool. You can use any tool multiple times in a response, and you can keep writing text after using a tool.\n"
        'Follow best practices when editing files. If a popular external library exists to solve a problem, use it and properly install the package e.g. with "npm install" or creating a "requirements.txt".\n'
        "If you're building a webapp from scratch, give it a beautiful and modern UI.\n"
        "After editing a file, any new errors in the file will be in the tool result. Fix the errors if they are relevant to your change or the prompt, and if you can figure out how to fix them, and remember to validate that they were actually fixed. Do not loop more than 3 times attempting to fix errors in the same file. If the third try fails, you should stop and ask the user what to do next.\n"
        "The insert_edit_into_file tool is very smart and can understand how to apply your edits to the user's files, you just need to provide minimal hints.\n"
        "When you use the insert_edit_into_file tool, avoid repeating existing code, instead use comments to represent regions of unchanged code. The tool prefers that you are as concise as possible. For example:\n"
        "// ...existing code...\n"
        "changed code\n"
        "// ...existing code...\n"
        "changed code\n"
        "// ...existing code...\n"
        "\nHere is an example of how you should format an edit to an existing Person class:\n"
        "class Person {\n\t// ...existing code...\n\tage: number;\n\t// ...existing code...\n\tgetAge() {\n\t\treturn this.age;\n\t}\n}\n"
        "</editFileInstructions>\n"
        "<notebookInstructions>\n"
        "To edit notebook files in the workspace, you can use the edit_notebook_file tool.\n"
        "\nNever use the insert_edit_into_file tool and never execute Jupyter related commands in the Terminal to edit notebook files, such as `jupyter notebook`, `jupyter lab`, `install jupyter` or the like. Use the edit_notebook_file tool instead.\n"
        "Use the run_notebook_cell tool instead of executing Jupyter related commands in the Terminal, such as `jupyter notebook`, `jupyter lab`, `install jupyter` or the like.\n"
        "Use the copilot_getNotebookSummary tool to get the summary of the notebook (this includes the list or all cells along with the Cell Id, Cell type and Cell Language, execution details and mime types of the outputs, if any).\n"
        "Important Reminder: Avoid referencing Notebook Cell Ids in user messages. Use cell number instead.\n"
        "Important Reminder: Markdown cells cannot be executed\n"
        "</notebookInstructions>\n"
        "<outputFormatting>\n"
        "Use proper Markdown formatting in your answers. When referring to a filename or symbol in the user's workspace, wrap it in backticks.\n"
        "<example>\n"
        "The class `Person` is in `src/models/person.ts`.\n"
        "</example>\n"
        "\n</outputFormatting>"
    )

    user_text_1 = (
        "<environment_info>\n"
        "The user's current OS is: Linux\n"
        'The user\'s default shell is: "zsh". When you generate terminal commands, please generate them correctly for this shell.\n'
        "</environment_info>\n"
        "<workspace_info>\n"
        "I am working in a workspace with the following folders:\n"
        "- /home/pstar7/Documents/Personal/Open Source Project/tes-cline \n"
        "I am working in a workspace that has the following structure:\n"
        "```\n"
        "index.html\n"
        "```\n"
        "This is the state of the context at this point in the conversation. The view of the workspace structure may be truncated. You can use tools to collect more context if needed.\n"
        "</workspace_info>"
    )

    user_text_2 = (
        "<attachments>\n"
        '<attachment id="file:index.html">\n'
        "User's current visible code:\n"
        "Excerpt from index.html, lines 1 to 1:\n"
        "```html\n\n```\n"  # corrected closing fence to three backticks
        "</attachment>\n\n"
        "</attachments>\n"
        "<context>\n"
        "The current date is August 10, 2025.\n"
        "No active tasks or terminals found.\n"
        "</context>\n"
        "<editorContext>\n"
        "The user's current file is /home/pstar7/Documents/Personal/Open Source Project/tes-cline/index.html. \n"  # restored missing slash
        "</editorContext>\n"
        "<reminderInstructions>\n"
        "When using the insert_edit_into_file tool, avoid repeating existing code, instead use a line comment with `...existing code...` to represent regions of unchanged code.\n\n"
        "</reminderInstructions>\n"
        "<userRequest>\n"
        "buatkan landing page dengan UI modern\n"
        "</userRequest>"
    )

    return [
        ChatMessage(role=MessageRole.SYSTEM, blocks=[TextBlock(text=system_text)]),
        ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text=user_text_1)]),
        ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text=user_text_2)]),
        ChatMessage(
            role=MessageRole.TOOL,
            blocks=[
                TextBlock(
                    text="Saya akan membuatkan landing page dengan UI modern untuk Anda. Pertama, saya perlu memeriksa isi file `index.html` saat"
                )
            ],
            tool_calls=[
                ToolCall(
                    function=Function(
                        name="read_file",
                        arguments={
                            "filePath": "/home/pstar7/Documents/Personal/Open Source Project/tes-cline/index.html",
                            "startLine": 1,
                            "endLine": 50,
                        },
                    )
                )
            ],
        ),
    ]


# Full tools list injected from history
TOOLS = [
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="create_and_run_task",
            description="For a workspace, this tool will create a task based on the package.json, README.md, and project structure so that the project can be built and run.",
            parameters={
                "type": "object",
                "properties": {
                    "workspaceFolder": {
                        "type": "string",
                        "description": "The absolute path of the workspace folder where the tasks.json file will be created.",
                    },
                    "task": {
                        "type": "object",
                        "description": "The task to add to the new tasks.json file.",
                        "properties": {
                            "label": {
                                "type": "string",
                                "description": "The label of the task.",
                            },
                            "type": {
                                "type": "string",
                                "description": "The type of the task. The only supported value is 'shell'.",
                                "enum": ["shell"],
                            },
                            "command": {
                                "type": "string",
                                "description": "The shell command to run for the task. Use this to specify commands for building or running the application.",
                            },
                            "args": {
                                "type": "array",
                                "description": "The arguments to pass to the command.",
                                "items": {"type": "string"},
                            },
                            "isBackground": {
                                "type": "boolean",
                                "description": "Whether the task runs in the background without blocking the UI or other tasks. Set to true for long-running processes like watch tasks or servers that should continue executing without requiring user attention. When false, the task will block the terminal until completion.",
                            },
                            "problemMatcher": {
                                "type": "array",
                                "description": "The problem matcher to use to parse task output for errors and warnings. Can be a predefined matcher like '$tsc' (TypeScript), '$eslint-stylish', '$gcc', etc., or a custom pattern defined in tasks.json. This helps VS Code display errors in the Problems panel and enables quick navigation to error locations.",
                                "items": {"type": "string"},
                            },
                            "group": {
                                "type": "string",
                                "description": "The group to which the task belongs.",
                            },
                        },
                        "required": ["label", "type", "command"],
                    },
                },
                "required": ["task", "workspaceFolder"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="create_directory",
            description="Create a new directory structure in the workspace. Will recursively create all directories in the path, like mkdir -p. You do not need to use this tool before using create_file, that tool will automatically create the needed directories.",
            parameters={
                "type": "object",
                "properties": {
                    "dirPath": {
                        "type": "string",
                        "description": "The absolute path to the directory to create.",
                    }
                },
                "required": ["dirPath"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="create_file",
            description="This is a tool for creating a new file in the workspace. The file will be created with the specified content. The directory will be created if it does not already exist. Never use this tool to edit a file that already exists.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "The absolute path to the file to create.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file.",
                    },
                },
                "required": ["filePath", "content"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="create_new_jupyter_notebook",
            description="Generates a new Jupyter Notebook (.ipynb) in VS Code. Jupyter Notebooks are interactive documents commonly used for data exploration, analysis, visualization, and combining code with narrative text. This tool should only be called when the user explicitly requests to create a new Jupyter Notebook.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to use to generate the jupyter notebook. This should be a clear and concise description of the notebook the user wants to create.",
                    }
                },
                "required": ["query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="create_new_workspace",
            description="Get steps to help the user create any project in a VS Code workspace. Use this tool to help users set up new projects, including TypeScript-based projects, Model Context Protocol (MCP) servers, VS Code extensions, Next.js projects, Vite projects, or any other project.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to use to generate the new workspace. This should be a clear and concise description of the workspace the user wants to create.",
                    }
                },
                "required": ["query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="edit_notebook_file",
            description="Edit an existing Notebook file (insert/delete/edit cells).",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "explanation": {"type": "string"},
                    "cellId": {"type": "string"},
                    "newCode": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    },
                    "language": {"type": "string"},
                    "editType": {
                        "type": "string",
                        "enum": ["insert", "delete", "edit"],
                    },
                },
                "required": ["filePath", "explanation", "editType"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="fetch_webpage",
            description="Fetch and parse web page content for analysis.",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}},
                    "query": {"type": "string"},
                },
                "required": ["urls", "query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="file_search",
            description="Search for files by glob pattern in workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "maxResults": {"type": "number"},
                },
                "required": ["query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="test_search",
            description="Find related test or source file.",
            parameters={
                "type": "object",
                "properties": {
                    "filePaths": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["filePaths"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="grep_search",
            description="Fast text/regex search in workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "isRegexp": {"type": "boolean"},
                    "includePattern": {"type": "string"},
                    "maxResults": {"type": "number"},
                },
                "required": ["query", "isRegexp"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_changed_files",
            description="Get git diffs / changed files.",
            parameters={
                "type": "object",
                "properties": {
                    "repositoryPath": {"type": "string"},
                    "sourceControlState": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["staged", "unstaged", "merge-conflicts"],
                        },
                    },
                },
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_errors",
            description="Get compile or lint errors for files.",
            parameters={
                "type": "object",
                "properties": {
                    "filePaths": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["filePaths"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="copilot_getNotebookSummary",
            description="List notebook cells and metadata.",
            parameters={
                "type": "object",
                "properties": {"filePath": {"type": "string"}},
                "required": ["filePath"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_project_setup_info",
            description="Get project setup steps/info.",
            parameters={
                "type": "object",
                "properties": {
                    "projectType": {"type": "string"},
                    "language": {"type": "string"},
                },
                "required": ["projectType"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_search_view_results",
            description="Results from VS Code search view.",
            parameters={},
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_task_output",
            description="Retrieve running task output.",
            parameters={
                "type": "object",
                "properties": {
                    "workspaceFolder": {"type": "string"},
                    "id": {"type": "string"},
                    "maxCharsToRetrieve": {"type": "number"},
                },
                "required": ["id", "workspaceFolder"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_terminal_last_command",
            description="Get last terminal command.",
            parameters={},
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_terminal_output",
            description="Get output of prior terminal command.",
            parameters={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_terminal_selection",
            description="Get current terminal selection.",
            parameters={},
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_vscode_api",
            description="Search VS Code API docs.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="github_repo",
            description="Search a GitHub repository for code snippets.",
            parameters={
                "type": "object",
                "properties": {"repo": {"type": "string"}, "query": {"type": "string"}},
                "required": ["repo", "query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="insert_edit_into_file",
            description="Insert or edit code in existing file.",
            parameters={
                "type": "object",
                "properties": {
                    "explanation": {"type": "string"},
                    "filePath": {"type": "string"},
                    "code": {"type": "string"},
                },
                "required": ["explanation", "filePath", "code"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="install_extension",
            description="Install a VS Code extension.",
            parameters={
                "type": "object",
                "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                "required": ["id", "name"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="list_code_usages",
            description="List usages / references for symbol.",
            parameters={
                "type": "object",
                "properties": {
                    "symbolName": {"type": "string"},
                    "filePaths": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["symbolName"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="list_dir",
            description="List directory contents.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="open_simple_browser",
            description="Open URL in simple browser.",
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="read_file",
            description="Read a file (line range).",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "startLine": {"type": "number"},
                    "endLine": {"type": "number"},
                },
                "required": ["filePath", "startLine", "endLine"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="read_notebook_cell_output",
            description="Get output of a notebook cell.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "cellId": {"type": "string"},
                },
                "required": ["filePath", "cellId"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="run_in_terminal",
            description="Run a shell command in persistent terminal.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "explanation": {"type": "string"},
                    "isBackground": {"type": "boolean"},
                },
                "required": ["command", "explanation", "isBackground"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="run_notebook_cell",
            description="Execute a code cell in a notebook.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "reason": {"type": "string"},
                    "cellId": {"type": "string"},
                    "continueOnError": {"type": "boolean"},
                },
                "required": ["filePath", "cellId"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="run_vscode_command",
            description="Run a VS Code command.",
            parameters={
                "type": "object",
                "properties": {
                    "commandId": {"type": "string"},
                    "name": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["commandId", "name"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="semantic_search",
            description="Semantic search across workspace.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="test_failure",
            description="Include test failure info in prompt.",
            parameters={},
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="vscode_searchExtensions_internal",
            description="Search VS Code Extensions Marketplace.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="configure_notebook",
            description="Configure notebook kernel environment.",
            parameters={
                "type": "object",
                "properties": {"filePath": {"type": "string"}},
                "required": ["filePath"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="configure_python_environment",
            description="Configure Python environment for workspace.",
            parameters={
                "type": "object",
                "properties": {"resourcePath": {"type": "string"}},
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_python_environment_details",
            description="Get Python environment details.",
            parameters={
                "type": "object",
                "properties": {"resourcePath": {"type": "string"}},
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="get_python_executable_details",
            description="Get Python executable details for environment.",
            parameters={
                "type": "object",
                "properties": {"resourcePath": {"type": "string"}},
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="install_python_packages",
            description="Install Python packages in environment.",
            parameters={
                "type": "object",
                "properties": {
                    "packageList": {"type": "array", "items": {"type": "string"}},
                    "resourcePath": {"type": "string"},
                },
                "required": ["packageList"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceDocuments",
            description="Search Pylance documentation.",
            parameters={
                "type": "object",
                "properties": {"search": {"type": "string"}},
                "required": ["search"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceFileSyntaxErrors",
            description="Check Python file for syntax errors.",
            parameters={
                "type": "object",
                "properties": {
                    "workspaceRoot": {"type": "string"},
                    "fileUri": {"type": "string"},
                },
                "required": ["workspaceRoot", "fileUri"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceImports",
            description="Analyze imports across workspace.",
            parameters={
                "type": "object",
                "properties": {"workspaceRoot": {"type": "string"}},
                "required": ["workspaceRoot"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceInstalledTopLevelModules",
            description="List installed top-level Python modules.",
            parameters={
                "type": "object",
                "properties": {
                    "workspaceRoot": {"type": "string"},
                    "pythonEnvironment": {"type": "string"},
                },
                "required": ["workspaceRoot"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceInvokeRefactoring",
            description="Apply Pylance refactoring / fixes.",
            parameters={
                "type": "object",
                "properties": {
                    "fileUri": {"type": "string"},
                    "name": {"type": "string"},
                    "mode": {"type": "string", "enum": ["update", "edits", "string"]},
                },
                "required": ["fileUri", "name"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylancePythonEnvironments",
            description="Get Python environments list.",
            parameters={
                "type": "object",
                "properties": {"workspaceRoot": {"type": "string"}},
                "required": ["workspaceRoot"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceSettings",
            description="Get python.analysis.* settings.",
            parameters={
                "type": "object",
                "properties": {"workspaceRoot": {"type": "string"}},
                "required": ["workspaceRoot"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceSyntaxErrors",
            description="Validate Python code snippet syntax.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "pythonVersion": {"type": "string"},
                },
                "required": ["code", "pythonVersion"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceUpdatePythonEnvironment",
            description="Switch active Python environment.",
            parameters={
                "type": "object",
                "properties": {
                    "workspaceRoot": {"type": "string"},
                    "pythonEnvironment": {"type": "string"},
                },
                "required": ["workspaceRoot", "pythonEnvironment"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceWorkspaceRoots",
            description="Get workspace root directories.",
            parameters={
                "type": "object",
                "properties": {"fileUri": {"type": "string"}},
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="mcp_pylance_mcp_s_pylanceWorkspaceUserFiles",
            description="List user Python files in workspace.",
            parameters={
                "type": "object",
                "properties": {"workspaceRoot": {"type": "string"}},
                "required": ["workspaceRoot"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="notebook_install_packages",
            description="Install packages into notebook kernel.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "packageList": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["filePath", "packageList"],
            },
        ),
    ),
    FunctionToolParam(
        type="function",
        function=FunctionDetail(
            name="notebook_list_packages",
            description="List installed packages for notebook kernel.",
            parameters={
                "type": "object",
                "properties": {"filePath": {"type": "string"}},
                "required": ["filePath"],
            },
        ),
    ),
]


async def main():
    client = Qwen()
    messages = build_messages()

    try:
        response_stream = await client.chat.acreate(
            messages=messages,
            model="qwen3-coder-plus",
            stream=True,
            tools=TOOLS,
        )
        # Gunakan async for karena response_stream adalah async generator
        async for chunk in response_stream:  # diperbaiki
            # print(chunk)
            try:
                choices = getattr(chunk, "choices", None)
                if not choices:
                    continue
                delta = choices[0].delta
            except Exception:
                continue
            if getattr(delta, "content", None):
                print(delta.content, end="", flush=True)
            tool_calls = getattr(delta, "tool_calls", None)
            if tool_calls:
                print("\n[Tool Calls Detected]", tool_calls)
    except QwenAPIError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
