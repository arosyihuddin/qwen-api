import json
import requests
import aiohttp
from ..core.types.chat import ChatMessage
from ..utils.tool_prompt import TOOL_PROMPT_SYSTEM
from ..core.types.endpoint_api import EndpointAPI
from ..core.exceptions import QwenAPIError, RateLimitError


def using_tools(messages, tools, model, temperature, max_tokens, stream, client):
    """
    Sync version of tool handling - simplified without selection logic
    """
    # Convert tools to individual JSON objects separated by newlines (no array brackets)
    tools_str = "\n".join([json.dumps(tool, ensure_ascii=False) for tool in tools])

    # Create system message with tools info
    system_content = TOOL_PROMPT_SYSTEM.replace("{list_tools}", tools_str)

    # Check if first message is already system message
    if messages and messages[0].role == "system":
        # Append tools info to existing system message
        system_content = messages[0].content + "\n\n" + system_content
        msg_tool = [ChatMessage(role="system", content=system_content)] + messages[1:]
    else:
        # Create new system message and include all original messages
        msg_tool = [ChatMessage(role="system", content=system_content)] + messages

    payload_tools = client._build_payload(
        messages=msg_tool, model=model, temperature=temperature, max_tokens=max_tokens
    )

    response_tool = requests.post(
        url=client.base_url + EndpointAPI.completions,
        headers=client._build_headers(),
        json=payload_tools,
        timeout=client.timeout,
        stream=stream,
    )

    if not response_tool.ok:
        error_text = response_tool.text
        client.logger.error(f"API Error: {response_tool.status_code} {error_text}")
        raise QwenAPIError(f"API Error: {response_tool.status_code} {error_text}")

    if response_tool.status_code == 429:
        client.logger.error("Too many requests")
        raise RateLimitError("Too many requests")

    client.logger.info(f"Response status: {response_tool.status_code}")
    client.logger.info(
        f"Response content-type: {response_tool.headers.get('content-type', 'unknown')}"
    )

    # Parse tool response directly
    try:
        # Check if response is streaming format
        content_type = response_tool.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Handle streaming response
            content = ""
            for line in response_tool.iter_lines(decode_unicode=True):
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    try:
                        data_part = line[6:]  # Remove 'data: ' prefix
                        if data_part and data_part != "[DONE]":
                            chunk_data = json.loads(data_part)
                            delta_content = (
                                chunk_data.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if delta_content:
                                content += delta_content
                    except json.JSONDecodeError:
                        continue
        else:
            # Handle regular JSON response
            response_data = response_tool.json()
            content = (
                response_data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

        # Check if content contains tool calls
        tool_calls = None
        if "<tool_call>" in content and "</tool_call>" in content:
            # Extract and parse tool calls
            tool_calls = []
            import re

            # Find all tool_call blocks
            tool_call_pattern = r"<tool_call>\s*({.*?})\s*</tool_call>"
            matches = re.findall(tool_call_pattern, content, re.DOTALL)

            for i, match in enumerate(matches):
                try:
                    tool_data = json.loads(match)

                    # Create ToolCall object following the schema
                    from ..core.types.response.function_tool import ToolCall, Function

                    function = Function(
                        name=tool_data.get("name", ""),
                        arguments=tool_data.get("arguments", {}),
                    )

                    tool_call = ToolCall(function=function)
                    tool_calls.append(tool_call)

                except json.JSONDecodeError:
                    client.logger.warning(f"Failed to parse tool call: {match}")

            # Clear content if we have tool calls (like OpenAI behavior)
            if tool_calls:
                content = ""

        # Create ChatResponse object
        from ..core.types.chat import ChatResponse, Choice, Message

        message = Message(role="assistant", content=content, tool_calls=tool_calls)

        choice = Choice(message=message, extra=None)

        chat_response = ChatResponse(choices=choice)

        return chat_response

    except Exception as e:
        client.logger.error(f"Error parsing tool response: {e}")
        # Return error response
        from ..core.types.chat import ChatResponse, Choice, Message

        message = Message(
            role="assistant", content="Error parsing tool response", tool_calls=None
        )

        choice = Choice(message=message, extra=None)

        return ChatResponse(choices=choice)


async def async_using_tools(messages, tools, model, temperature, max_tokens, client):
    """
    Main function for handling tools - simplified version without selection logic
    """
    # Convert tools to individual JSON objects separated by newlines (no array brackets)
    tools_str = "\n".join([json.dumps(tool, ensure_ascii=False) for tool in tools])

    # Create system message with tools info
    system_content = TOOL_PROMPT_SYSTEM.replace("{list_tools}", tools_str)

    # Check if first message is already system message
    if messages and messages[0].role == "system":
        # Append tools info to existing system message
        system_content = messages[0].content + "\n\n" + system_content
        msg_tool = [ChatMessage(role="system", content=system_content)] + messages[1:]
    else:
        # Create new system message and include all original messages
        msg_tool = [ChatMessage(role="system", content=system_content)] + messages

    payload_tools = client._build_payload(
        messages=msg_tool, model=model, temperature=temperature, max_tokens=max_tokens
    )

    session = aiohttp.ClientSession()
    try:
        response_tool = await session.post(
            url=client.base_url + EndpointAPI.completions,
            headers=client._build_headers(),
            json=payload_tools,
            timeout=aiohttp.ClientTimeout(total=client.timeout),
        )

        if not response_tool.ok:
            error_text = await response_tool.text()
            client.logger.error(f"API Error: {response_tool.status} {error_text}")
            raise QwenAPIError(f"API Error: {response_tool.status} {error_text}")

        if response_tool.status == 429:
            client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        client.logger.info(f"Response status: {response_tool.status}")
        client.logger.info(
            f"Response content-type: {response_tool.headers.get('content-type', 'unknown')}"
        )

        # Parse tool response directly
        try:
            # Check if response is streaming format
            content_type = response_tool.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                # Handle streaming response
                content = ""
                async for line in response_tool.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: ") and not line_str.endswith(
                        "[DONE]"
                    ):
                        try:
                            data_part = line_str[6:]  # Remove 'data: ' prefix
                            if data_part and data_part != "[DONE]":
                                chunk_data = json.loads(data_part)
                                delta_content = (
                                    chunk_data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if delta_content:
                                    content += delta_content
                        except json.JSONDecodeError:
                            continue
            else:
                # Handle regular JSON response
                response_data = await response_tool.json()
                content = (
                    response_data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

            # Check if content contains tool calls
            tool_calls = None
            if "<tool_call>" in content and "</tool_call>" in content:
                # Extract and parse tool calls
                tool_calls = []
                import re

                # Find all tool_call blocks
                tool_call_pattern = r"<tool_call>\s*({.*?})\s*</tool_call>"
                matches = re.findall(tool_call_pattern, content, re.DOTALL)

                for i, match in enumerate(matches):
                    try:
                        tool_data = json.loads(match)

                        # Create ToolCall object following the schema
                        from ..core.types.response.function_tool import (
                            ToolCall,
                            Function,
                        )

                        function = Function(
                            name=tool_data.get("name", ""),
                            arguments=tool_data.get("arguments", {}),
                        )

                        tool_call = ToolCall(function=function)
                        tool_calls.append(tool_call)

                    except json.JSONDecodeError:
                        client.logger.warning(f"Failed to parse tool call: {match}")

                # Clear content if we have tool calls (like OpenAI behavior)
                if tool_calls:
                    content = ""

            # Create ChatResponse object
            from ..core.types.chat import ChatResponse, Choice, Message

            message = Message(role="assistant", content=content, tool_calls=tool_calls)

            choice = Choice(message=message, extra=None)

            chat_response = ChatResponse(choices=choice)

            return chat_response

        except Exception as e:
            client.logger.error(f"Error parsing tool response: {e}")
            # Return error response
            from ..core.types.chat import ChatResponse, Choice, Message

            message = Message(
                role="assistant", content="Error parsing tool response", tool_calls=None
            )

            choice = Choice(message=message, extra=None)

            return ChatResponse(choices=choice)
    finally:
        await session.close()
