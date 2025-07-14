import requests
import aiohttp
from ..core.types.chat import ChatMessage
from ..utils.tool_prompt import CHOICE_TOOL_PROMPT, TOOL_PROMPT_SYSTEM, example
from ..core.types.endpoint_api import EndpointAPI
from ..core.exceptions import QwenAPIError, RateLimitError


def action_selection(messages, tools, model, temperature, max_tokens, stream, client):
    if messages[-1].role == "tool":
        return False

    # Pre-filter tools based on simple keyword matching to help the AI focus
    user_content = messages[-1].content.lower()
    
    # Simple keyword-based relevance scoring
    def is_tool_relevant(tool):
        tool_info = tool if isinstance(tool, dict) else tool.dict()
        tool_name = tool_info.get('function', {}).get('name', '').lower()
        tool_desc = tool_info.get('function', {}).get('description', '').lower()
        
        # Math-related keywords
        math_keywords = ['berapa', 'hitung', 'calculate', 'math', '+', '-', '*', '/', '=', 'tambah', 'kurang', 'kali', 'bagi']
        # HTTP-related keywords  
        http_keywords = ['request', 'api', 'http', 'get', 'post', 'fetch', 'url', 'endpoint']
        # Trading-related keywords
        trading_keywords = ['symbol', 'trading', 'binance', 'pair', 'market', 'crypto', 'bitcoin', 'ethereum']
        
        # Check if tool is relevant based on keywords
        if any(keyword in user_content for keyword in math_keywords) and 'calculator' in tool_name:
            return True
        if any(keyword in user_content for keyword in http_keywords) and ('http' in tool_name or 'request' in tool_name):
            return True
        if any(keyword in user_content for keyword in trading_keywords) and ('symbol' in tool_name or 'trading' in tool_desc):
            return True
        
        # Also check if keywords appear in tool description
        if any(keyword in tool_desc for keyword in math_keywords) and any(keyword in user_content for keyword in math_keywords):
            return True
        if any(keyword in tool_desc for keyword in http_keywords) and any(keyword in user_content for keyword in http_keywords):
            return True
        if any(keyword in tool_desc for keyword in trading_keywords) and any(keyword in user_content for keyword in trading_keywords):
            return True
            
        return False
    
    # Filter tools to only relevant ones, but keep all if none are specifically relevant
    relevant_tools = [tool for tool in tools if is_tool_relevant(tool)]
    
    # If no tools are specifically relevant, keep all tools (fallback)
    # But if we have relevant tools, use only those to avoid confusion
    tools_to_use = relevant_tools if relevant_tools else tools
    
    # If we have relevant tools, likely should use tools
    if relevant_tools:
        client.logger.debug(f"Found {len(relevant_tools)} relevant tools out of {len(tools)} total tools")
        return True
    
    # Fallback to original logic with all tools
    choice_messages = [
        ChatMessage(role="system", content=CHOICE_TOOL_PROMPT.format(list_tools=tools_to_use)),
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
    if messages[-1].role == "tool":
        return False

    # Pre-filter tools based on simple keyword matching to help the AI focus
    user_content = messages[-1].content.lower()
    
    # Simple keyword-based relevance scoring
    def is_tool_relevant(tool):
        tool_info = tool if isinstance(tool, dict) else tool.dict()
        tool_name = tool_info.get('function', {}).get('name', '').lower()
        tool_desc = tool_info.get('function', {}).get('description', '').lower()
        
        # Math-related keywords
        math_keywords = ['berapa', 'hitung', 'calculate', 'math', '+', '-', '*', '/', '=', 'tambah', 'kurang', 'kali', 'bagi']
        # HTTP-related keywords  
        http_keywords = ['request', 'api', 'http', 'get', 'post', 'fetch', 'url', 'endpoint']
        # Trading-related keywords
        trading_keywords = ['symbol', 'trading', 'binance', 'pair', 'market', 'crypto', 'bitcoin', 'ethereum']
        
        # Check if tool is relevant based on keywords
        if any(keyword in user_content for keyword in math_keywords) and 'calculator' in tool_name:
            return True
        if any(keyword in user_content for keyword in http_keywords) and ('http' in tool_name or 'request' in tool_name):
            return True
        if any(keyword in user_content for keyword in trading_keywords) and ('symbol' in tool_name or 'trading' in tool_desc):
            return True
        
        # Also check if keywords appear in tool description
        if any(keyword in tool_desc for keyword in math_keywords) and any(keyword in user_content for keyword in math_keywords):
            return True
        if any(keyword in tool_desc for keyword in http_keywords) and any(keyword in user_content for keyword in http_keywords):
            return True
        if any(keyword in tool_desc for keyword in trading_keywords) and any(keyword in user_content for keyword in trading_keywords):
            return True
            
        return False
    
    # Filter tools to only relevant ones, but keep all if none are specifically relevant
    relevant_tools = [tool for tool in tools if is_tool_relevant(tool)]
    
    # If no tools are specifically relevant, keep all tools (fallback)
    # But if we have relevant tools, use only those to avoid confusion
    tools_to_use = relevant_tools if relevant_tools else tools
    
    # If we have relevant tools, likely should use tools
    if relevant_tools:
        client.logger.debug(f"Found {len(relevant_tools)} relevant tools out of {len(tools)} total tools")
        return True
    
    # Fallback to original logic with all tools
    choice_messages = [
        ChatMessage(role="system", content=CHOICE_TOOL_PROMPT.format(list_tools=tools_to_use)),
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
