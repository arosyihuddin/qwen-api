import requests
import json
import aiohttp
from ..core.types.chat import ChatMessage
from ..utils.tool_prompt import CHOICE_TOOL_PROMPT, TOOL_PROMPT_SYSTEM, example
from ..core.types.endpoint_api import EndpointAPI
from ..core.exceptions import QwenAPIError, RateLimitError
from ..core.types.chat import MessageRole


def action_selection(messages, tools, model, temperature, max_tokens, stream, client):
    client.logger.info("Starting action selection")
    if messages[-1].role == "tool":
        return False

        # Fallback to original logic with all tools
    choice_messages = [
        ChatMessage(role="system", content=CHOICE_TOOL_PROMPT.format(list_tools=tools)),
        ChatMessage(role="user", content=messages[-1].content),
    ]

    payload = client._build_payload(
        messages=choice_messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    response = requests.post(
        url=client.base_url + EndpointAPI.completions,
        headers=client._build_headers(),
        json=payload,
        timeout=client.timeout,
        stream=stream,
    )

    if not response.ok:
        error_text = response.text()
        client.logger.error(f"API Error: {response.status_code} {error_text}")
        raise QwenAPIError(f"API Error: {response.status_code} {error_text}")

    if response.status_code == 429:
        client.logger.error("Too many requests")
        raise RateLimitError("Too many requests")

    client.logger.info(f"Response status: {response.status_code}")

    result = client._process_response(response)
    return True if (result.choices.message.content) == "tools" else False


def using_tools(messages, tools, model, temperature, max_tokens, stream, client):
    tool = [tool if isinstance(tool, dict) else tool.dict() for tool in tools]
    tools_list = "\n".join([str(tool["function"]) for tool in tool])
    msg_tool = [
        ChatMessage(
            role="system",
            content=TOOL_PROMPT_SYSTEM.format(
                list_tools=tools_list, output_example=example.model_dump()
            ),
        ),
        ChatMessage(role="user", content=messages[-1].content),
    ]

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
        error_text = response_tool.text()
        client.logger.error(f"API Error: {response_tool.status_code} {error_text}")
        raise QwenAPIError(f"API Error: {response_tool.status_code} {error_text}")

    if response_tool.status_code == 429:
        client.logger.error("Too many requests")
        raise RateLimitError("Too many requests")

    client.logger.info(f"Response status: {response_tool.status_code}")

    result = client._process_response_tool(response_tool)
    return result


async def async_action_selection(
    messages, tools, model, temperature, max_tokens, client
):
    client.logger.info("Starting async action selection")

    # history_system_message = (
    #     messages[0].content if messages[0].role == MessageRole.SYSTEM else None
    # )
    system_content = CHOICE_TOOL_PROMPT.format(list_tools=tools)
    # if history_system_message:
    #     system_content += f"\n\n###More Instructions\n{history_system_message}\n"

    chat_message = [
        ChatMessage(role=i.role, content=i.content)
        for i in messages
        if i.role != MessageRole.SYSTEM
    ]
    chat_message.insert(0, ChatMessage(role=MessageRole.SYSTEM, content=system_content))
    # print(chat_message)

    payload = client._build_payload(
        messages=chat_message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    session = aiohttp.ClientSession()
    response = await session.post(
        url=client.base_url + EndpointAPI.completions,
        headers=client._build_headers(),
        json=payload,
        timeout=aiohttp.ClientTimeout(total=client.timeout),
    )

    if not response.ok:
        error_text = await response.text()
        client.logger.error(f"API Error: {response.status} {error_text}")
        raise QwenAPIError(f"API Error: {response.status} {error_text}")

    if response.status == 429:
        client.logger.error("Too many requests")
        raise RateLimitError("Too many requests")

    client.logger.info(f"Response status: {response.status}")

    result = await client._process_aresponse(response, session)
    print(result)
    return True if (result.choices.message.content) == "tools" else False


async def async_using_tools(messages, tools, model, temperature, max_tokens, client):
    tool_definition = [
        tool if isinstance(tool, dict) else tool.dict() for tool in tools
    ]
    tools_list = json.dumps(tool_definition, indent=2)
    history_chat_system = (
        messages[0].content if messages[0].role == MessageRole.SYSTEM else None
    )

    content_system = TOOL_PROMPT_SYSTEM.replace("{list_tools}", tools_list)

    if history_chat_system:
        content_system += (
            f"\n\n<more_instructions>\n{history_chat_system}\n</more_instructions>"
        )

    chat_message = [
        ChatMessage(role=i.role, content=i.content)
        for i in messages
        if i.role != MessageRole.SYSTEM
    ]

    chat_message.insert(0, ChatMessage(role=MessageRole.SYSTEM, content=content_system))

    # print(content_system)
    # print(messages[-1].content)
    # msg_tool = [
    #     ChatMessage(
    #         role=MessageRole.SYSTEM,
    #         content=content_system,
    #     ),
    #     ChatMessage(role=MessageRole.USER, content=messages[-1].content),
    # ]

    payload_tools = client._build_payload(
        messages=chat_message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    session = aiohttp.ClientSession()
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

    return await client._process_aresponse_tool(response_tool, session)


async def async_using_tools_stream(messages, tools, model, temperature, max_tokens, client):
    """
    Streaming version of tool handling that converts tool response to streaming format.
    For now, this is a simplified version that gets the tool response and converts it to streaming.
    """
    # First get the tool response using the existing method
    tool_response = await async_using_tools(
        messages, tools, model, temperature, max_tokens, client
    )
    
    # Convert the tool response to a streaming format
    async def tool_stream_generator():
        from ..core.types.chat import ChoiceStream, Delta, ChatResponseStream, Usage, ChatMessage
        
        # Create a streaming response from the tool response
        delta = Delta(
            role="assistant",
            content="",  # Tool calls don't have content, just the function call
            extra=tool_response.choices.extra,
        )
        
        choice_stream = ChoiceStream(delta=delta)
        
        # Create a proper ChatMessage for tool calls
        message = ChatMessage(
            role="assistant",
            content="",
            tool_calls=tool_response.choices.message.tool_calls
        )
        
        stream_response = ChatResponseStream(
            choices=[choice_stream],
            usage=None,
            message=message
        )
        
        yield stream_response
    
    return tool_stream_generator()

