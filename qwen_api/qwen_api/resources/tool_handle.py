import requests
import aiohttp
from ..core.types.chat import ChatMessage
from ..utils.tool_prompt import CHOICE_TOOL_PROMPT, TOOL_PROMPT_SYSTEM, example
from ..core.types.endpoint_api import EndpointAPI
from ..core.exceptions import QwenAPIError, RateLimitError


def action_selection(messages, tools, model, temperature, max_tokens, stream, client):
    if messages[-1].role == "tool":
        return False

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
    messages, tools, model, temperature, max_tokens, stream, client
):
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
    return True if (result.choices.message.content) == "tools" else False


async def async_using_tools(
    messages, tools, model, temperature, max_tokens, stream, client
):
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
