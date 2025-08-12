import os
import mimetypes
import datetime as dt
import aiohttp
import requests
import asyncio
import json
import re  # diperlukan untuk regex di streaming & parser
from ..core.types.response.function_tool import (
    Function,
    ToolCall,
)  # unified import path
from ..utils.tool_prompt import TOOLS_PROMPT_SYSTEM  # corrected relative import
from sseclient import SSEClient
from oss2.utils import http_date
from oss2.utils import content_type_by_name
from oss2 import Auth, Bucket
from typing import AsyncGenerator, Dict, Generator, List, Optional, Union, Iterable
from ..core.types.upload_file import FileResult
from ..core.exceptions import QwenAPIError, RateLimitError
from ..core.types.chat import (
    ChatResponseStream,
    ChatResponse,
    ChatMessage,
    Choice,
    ChoiceStream,
    Delta,
    Message,
    Usage,
)
from ..core.types.chat_model import ChatModel
from ..core.types.endpoint_api import EndpointAPI
from ..core.types.response.tool_param import ToolParam


class Completion:
    def __init__(self, client):
        self._client = client

    def _detect_tool_call_pattern(self, text: str) -> bool:
        txt = text or ""
        if '{"name"' in txt or '{ "name"' in txt:
            if '"arguments"' in txt:
                return True
        return False

    def _extract_tool_json(self, text: str) -> Optional[str]:
        """Find a JSON object (or list) that looks like a tool call inside text, even if preceded by prose.
        Returns the JSON substring or None."""
        if not text:
            return None
        # Look for first '{' followed by "name"
        start_idx = None
        for marker in ['{"name"', '{ "name"']:
            idx = text.find(marker)
            if idx != -1:
                brace_search = text.rfind("{", 0, idx + 1)
                start_idx = brace_search if brace_search != -1 else idx
                break
        if start_idx is None:
            return None
        # Simple brace matching to extract JSON
        brace_count = 0
        in_string = False
        escape = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    candidate = text[start_idx : i + 1].strip()
                    if '"name"' in candidate and '"arguments"' in candidate:
                        return candidate
                    return None
        return None

    def _parse_tool_call_json(
        self, text: str, tools: Optional[Iterable] = None
    ) -> Optional[List[ToolCall]]:
        """
        Parse text as tool call(s) with improved robustness.
        Accept single dict or list of dicts and validate against provided tools.
        """
        if not text:
            return None

        # Clean up the input text
        raw = text.strip()

        # Remove code fences
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"```\s*$", "", raw)

        # Remove any trailing characters like '%' that might be added by the model
        raw = re.sub(r"[%\s]*$", "", raw)

        # Find the start of JSON
        start_idx = None
        for i, char in enumerate(raw):
            if char in "[{":
                start_idx = i
                break

        if start_idx is None:
            return None

        raw = raw[start_idx:]

        # Try to parse as JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            try:
                # Fix unescaped quotes in string values
                fixed = re.sub(r'(?<!\\)"(?=[^"]*"[^"]*$)', '\\"', raw)
                data = json.loads(fixed)
            except json.JSONDecodeError:
                return None

        # Normalize to list
        items = data if isinstance(data, list) else [data]

        # Validate against allowed tools if provided
        allowed_names = None
        if tools:
            allowed_names = set()
            for t in tools:
                t_dict = (
                    t if isinstance(t, dict) else getattr(t, "model_dump", lambda: {})()
                )
                name = (
                    t_dict.get("function", {}).get("name")
                    if isinstance(t_dict, dict)
                    else None
                )
                if name:
                    allowed_names.add(name)

        # Parse tool calls
        parsed = []
        for obj in items:
            if not isinstance(obj, dict):
                continue

            name = obj.get("name")
            arguments = obj.get("arguments", {})

            if not isinstance(name, str):
                continue

            # Validate tool name if tools are provided
            if allowed_names is not None and name not in allowed_names:
                self._client.logger.warning(f"Tool '{name}' not found in allowed tools")
                continue

            # Handle arguments
            if not isinstance(arguments, dict):
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {"value": arguments}
                else:
                    arguments = {"value": str(arguments)}

            parsed.append(ToolCall(function=Function(name=name, arguments=arguments)))

        return parsed if parsed else None

    def create(
        self,
        messages: List[ChatMessage],
        model: ChatModel | str = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        tools: Optional[Iterable[ToolParam]] | List[Dict] = None,
    ) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]:
        # Prepare messages for tool calling if tools are provided
        if tools:
            # Convert tools to proper format
            tool_list = [
                tool if isinstance(tool, dict) else tool.model_dump() for tool in tools
            ]
            tools_str = "\n".join([str(tool["function"]) for tool in tool_list])

            # system_content = TOOLS_PROMPT_SYSTEM.format(list_tools=tools_str)
            system_content = TOOLS_PROMPT_SYSTEM.replace("{list_tools}", tools_str)

            # Replace or add system message
            modified_messages = []
            has_system = False

            for msg in messages:
                if msg.role == "system":
                    # Update existing system message with tool instructions
                    modified_messages.append(
                        ChatMessage(
                            role="system", content=f"{msg.content}\n\n{system_content}"
                        )
                    )
                    has_system = True
                else:
                    modified_messages.append(msg)

            if not has_system:
                # Add system message at the beginning
                modified_messages.insert(
                    0, ChatMessage(role="system", content=system_content)
                )

            messages = modified_messages

        # Build payload
        payload = self._client._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = requests.post(
            url=self._client.base_url + EndpointAPI.completions,
            headers=self._client._build_headers(),
            json=payload,
            timeout=self._client.timeout,
            stream=stream,
        )
        if not response.ok:
            error_text = response.json()
            self._client.logger.error(f"API Error: {response.status_code} {error_text}")
            raise QwenAPIError(f"API Error: {response.status_code} {error_text}")
        if response.status_code == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")
        self._client.logger.info(f"Response: {response.status_code}")
        tools_for_validation = tools
        if stream:
            return self._process_tool_calling_stream(response, tools_for_validation)
        try:
            result = self._client._process_response(response)
            if tools_for_validation and hasattr(result, "choices") and result.choices:
                choice_obj = result.choices  # ChatResponse.choices is a Choice
                if hasattr(choice_obj, "message") and choice_obj.message.content:
                    tcs = self._parse_tool_call_json(
                        choice_obj.message.content, tools_for_validation
                    )
                    if tcs:
                        return ChatResponse(
                            choices=Choice(
                                message=Message(
                                    role="tool_calls", content="", tool_calls=tcs
                                ),
                                extra=None,
                            )
                        )
            return result
        except Exception as e:
            self._client.logger.error(f"Error: {e}")
            raise

    async def acreate(
        self,
        messages: List[ChatMessage],
        model: ChatModel | str = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        tools: Optional[Iterable[ToolParam]] | List[Dict] = None,
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]:
        session = None
        try:
            # Prepare messages for tool calling if tools are provided
            if tools:
                # Convert tools to proper format
                tool_list = [
                    tool if isinstance(tool, dict) else tool.model_dump()
                    for tool in tools
                ]
                tools_str = "\n".join([str(tool["function"]) for tool in tool_list])

                # system_content = TOOLS_PROMPT_SYSTEM.format(list_tools=tools_str)
                system_content = TOOLS_PROMPT_SYSTEM.replace("{list_tools}", tools_str)

                # Replace or add system message
                modified_messages = []
                has_system = False

                for msg in messages:
                    if msg.role == "system":
                        # Update existing system message with tool instructions
                        modified_messages.append(
                            ChatMessage(
                                role="system",
                                content=f"{msg.content}\n\n{system_content}",
                            )
                        )
                        has_system = True
                    else:
                        modified_messages.append(msg)

                if not has_system:
                    # Add system message at the beginning
                    modified_messages.insert(
                        0, ChatMessage(role="system", content=system_content)
                    )

                messages = modified_messages

            # Build payload
            payload = self._client._build_payload(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            session = aiohttp.ClientSession()
            self._client._active_sessions.append(session)
            response = await session.post(
                url=self._client.base_url + EndpointAPI.completions,
                headers=self._client._build_headers(),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._client.timeout),
            )
            if not response.ok:
                error_text = await response.text()
                self._client.logger.error(f"API Error: {response.status} {error_text}")
                raise QwenAPIError(f"API Error: {response.status} {error_text}")
            if response.status == 429:
                self._client.logger.error("Too many requests")
                raise RateLimitError("Too many requests")
            self._client.logger.info(f"Response status: {response.status}")
            tools_for_validation = tools
            if stream:
                return self._process_hybrid_stream(
                    response, session, tools_for_validation
                )
            try:
                result = await self._client._process_aresponse(response, session)
                if (
                    tools_for_validation
                    and hasattr(result, "choices")
                    and result.choices
                ):
                    choice_obj = result.choices
                    if hasattr(choice_obj, "message") and choice_obj.message.content:
                        tcs = self._parse_tool_call_json(
                            choice_obj.message.content, tools_for_validation
                        )
                        if tcs:
                            return ChatResponse(
                                choices=Choice(
                                    message=Message(
                                        role="tool_calls", content="", tool_calls=tcs
                                    ),
                                    extra=None,
                                )
                            )
                return result
            except Exception as e:
                self._client.logger.error(f"Error: {e}")
                raise
        except Exception as e:
            self._client.logger.error(f"Error in acreate: {e}")
            if session and not session.closed:
                if session in self._client._active_sessions:
                    self._client._active_sessions.remove(session)
                try:
                    await asyncio.wait_for(session.close(), timeout=1.0)
                except (asyncio.TimeoutError, Exception) as cleanup_error:
                    if "APPLICATION_DATA_AFTER_CLOSE_NOTIFY" not in str(cleanup_error):
                        self._client.logger.debug(
                            f"Session cleanup error: {cleanup_error}"
                        )
            raise

    async def _process_hybrid_stream(
        self,
        response: aiohttp.ClientResponse,
        session: aiohttp.ClientSession,
        tools: Optional[Iterable] = None,
    ) -> AsyncGenerator[ChatResponseStream, None]:
        """
        Streaming processor with 10-token buffering for tool call detection.
        """
        token_buffer = []
        content_buffer = ""
        tool_detected = False
        tool_completed = False
        BUFFER_SIZE = 10

        # Pastikan session tercatat untuk cleanup
        if session not in self._client._active_sessions:
            self._client._active_sessions.append(session)

        def is_potential_tool_call(text: str) -> bool:
            """Check if text contains patterns indicating tool call."""
            patterns = [
                r'\[\s*{[^}]*"name"[^}]*"arguments"',  # Array format
                r'{\s*"name"[^}]*"arguments"',  # Object format
                r'```json\s*\[?\s*{[^}]*"name"',  # Fenced format
                r'{"name"',  # Simple object start
                r'\[{.*"name"',  # Array with name
            ]
            return any(
                re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                for pattern in patterns
            )

        def extract_complete_tool_calls(text: str) -> Optional[str]:
            """Extract complete tool call JSON from text."""
            text = text.strip()

            # Remove code fences if present
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"```\s*$", "", text)

            # Find JSON boundaries
            start_idx = None
            for i, char in enumerate(text):
                if char in "[{":
                    start_idx = i
                    break

            if start_idx is None:
                return None

            # Count braces/brackets to find complete JSON
            brace_count = bracket_count = 0
            in_string = False
            escape = False

            for i in range(start_idx, len(text)):
                char = text[i]

                if escape:
                    escape = False
                    continue

                if char == "\\":
                    escape = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if in_string:
                    continue

                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                elif char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1

                # Check if we have complete JSON
                if (
                    brace_count == 0
                    and bracket_count == 0
                    and (brace_count + bracket_count) == 0
                ):
                    if i > start_idx:  # Ensure we have some content
                        return text[start_idx : i + 1]

            return None

        async def emit_tokens(tokens: List[str]):
            """Emit tokens as streaming content."""
            for token in tokens:
                yield ChatResponseStream(
                    choices=[
                        ChoiceStream(delta=Delta(role="assistant", content=token))
                    ],
                    usage=Usage(),
                    message=ChatMessage(role="assistant", content=token),
                )

        try:
            async for line in response.content:
                if self._client._is_cancelled:
                    break

                line_str = line.decode("utf-8", errors="ignore").strip()
                if not line_str or not line_str.startswith("data:"):
                    continue

                if line_str == "data: [DONE]":
                    break

                json_str = line_str[5:].strip()
                if not json_str:
                    continue

                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    continue

                if "choices" not in data or not data["choices"]:
                    continue

                delta_dict = data["choices"][0].get("delta", {})
                content_piece = delta_dict.get("content", "")

                if content_piece is None:
                    content_piece = ""

                if content_piece == "":
                    continue

                # Add to buffers
                token_buffer.append(content_piece)
                content_buffer += content_piece

                # Check buffer every 10 tokens or when tool already detected
                if len(token_buffer) >= BUFFER_SIZE or tool_detected:

                    # Join current buffer for analysis
                    buffer_text = "".join(token_buffer)

                    # Check for tool call patterns if not already detected
                    if not tool_detected and is_potential_tool_call(content_buffer):
                        tool_detected = True
                        self._client.logger.debug(
                            "Tool call pattern detected in buffer"
                        )
                        # Don't emit tokens when tool call is detected, wait for complete JSON
                        continue

                    if tool_detected and not tool_completed:
                        # Try to extract complete tool calls from full content buffer
                        complete_json = extract_complete_tool_calls(content_buffer)

                        if complete_json:
                            # Parse tool calls
                            tool_calls = self._parse_tool_call_json(
                                complete_json, tools
                            )

                            if tool_calls:
                                # Emit tool calls instead of buffered content
                                delta_obj = Delta(
                                    role="assistant", content="", tool_calls=tool_calls
                                )
                                yield ChatResponseStream(
                                    choices=[ChoiceStream(delta=delta_obj)],
                                    usage=Usage(),
                                    message=ChatMessage(
                                        role="assistant",
                                        content="",
                                        tool_calls=tool_calls,
                                    ),
                                )
                                tool_completed = True
                                self._client.logger.debug(
                                    f"Emitted {len(tool_calls)} tool calls from buffer"
                                )
                                # Clear buffers after successful tool call
                                token_buffer.clear()
                                continue
                        else:
                            # If we can't extract complete JSON yet, continue buffering
                            continue

                    # If no tool call detected or already completed, emit buffered tokens
                    if not tool_detected or tool_completed:
                        async for stream_chunk in emit_tokens(token_buffer):
                            yield stream_chunk
                        token_buffer.clear()

            # Handle any remaining tokens in buffer
            if token_buffer:
                if tool_detected and not tool_completed:
                    # Final attempt to parse tool calls
                    tool_calls = self._parse_tool_call_json(content_buffer, tools)
                    if tool_calls:
                        delta_obj = Delta(
                            role="assistant", content="", tool_calls=tool_calls
                        )
                        yield ChatResponseStream(
                            choices=[ChoiceStream(delta=delta_obj)],
                            usage=Usage(),
                            message=ChatMessage(
                                role="assistant",
                                content="",
                                tool_calls=tool_calls,
                            ),
                        )
                    else:
                        # Emit remaining tokens as regular content
                        async for stream_chunk in emit_tokens(token_buffer):
                            yield stream_chunk
                else:
                    # Emit remaining tokens as regular content
                    async for stream_chunk in emit_tokens(token_buffer):
                        yield stream_chunk

        except (aiohttp.ClientError, asyncio.CancelledError) as e:
            if isinstance(e, asyncio.CancelledError):
                self._client.logger.info("Stream was cancelled")
            else:
                self._client.logger.error(f"Client error in stream: {e}")
            if not isinstance(e, asyncio.CancelledError):
                raise
        finally:
            try:
                if session in self._client._active_sessions:
                    self._client._active_sessions.remove(session)
                if not session.closed:
                    if hasattr(response, "close") and not response.closed:
                        response.close()
                    await asyncio.sleep(0.05)
                    try:
                        await asyncio.wait_for(session.close(), timeout=1.0)
                    except asyncio.TimeoutError:
                        pass
            except Exception as e:
                if "APPLICATION_DATA_AFTER_CLOSE_NOTIFY" not in str(e):
                    self._client.logger.debug(f"Error during cleanup: {e}")

    def _process_tool_calling_stream(
        self,
        response: requests.Response,
        tools: Optional[Iterable] = None,
    ) -> Generator[ChatResponseStream, None, None]:
        """
        Synchronous streaming with 10-token buffering for tool call detection.
        """
        try:
            client = SSEClient(response)  # type: ignore[arg-type]
        except Exception as e:
            self._client.logger.error(f"Failed to init SSEClient: {e}")
            raise

        token_buffer = []
        content_buffer = ""
        tool_detected = False
        tool_completed = False
        BUFFER_SIZE = 10

        def is_potential_tool_call(text: str) -> bool:
            """Check if text contains patterns indicating tool call."""
            patterns = [
                r'\[\s*{[^}]*"name"[^}]*"arguments"',  # Array format
                r'{\s*"name"[^}]*"arguments"',  # Object format
                r'```json\s*\[?\s*{[^}]*"name"',  # Fenced format
                r'{"name"',  # Simple object start
                r'\[{.*"name"',  # Array with name
            ]
            return any(
                re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                for pattern in patterns
            )

        def extract_complete_tool_calls(text: str) -> Optional[str]:
            """Extract complete tool call JSON from text."""
            text = text.strip()

            # Remove code fences if present
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"```\s*$", "", text)

            # Find JSON boundaries
            start_idx = None
            for i, char in enumerate(text):
                if char in "[{":
                    start_idx = i
                    break

            if start_idx is None:
                return None

            # Count braces/brackets to find complete JSON
            brace_count = bracket_count = 0
            in_string = False
            escape = False

            for i in range(start_idx, len(text)):
                char = text[i]

                if escape:
                    escape = False
                    continue

                if char == "\\":
                    escape = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if in_string:
                    continue

                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                elif char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1

                # Check if we have complete JSON
                if (
                    brace_count == 0
                    and bracket_count == 0
                    and (brace_count + bracket_count) == 0
                ):
                    if i > start_idx:  # Ensure we have some content
                        return text[start_idx : i + 1]

            return None

        def emit_tokens(tokens: List[str]):
            """Emit tokens as streaming content."""
            for token in tokens:
                yield ChatResponseStream(
                    choices=[
                        ChoiceStream(delta=Delta(role="assistant", content=token))
                    ],
                    usage=Usage(),
                    message=ChatMessage(role="assistant", content=token),
                )

        try:
            for event in client.events():
                if event.data == "[DONE]":
                    break

                try:
                    data = json.loads(event.data)
                except json.JSONDecodeError:
                    continue

                if "choices" not in data or not data["choices"]:
                    continue

                delta_dict = data["choices"][0].get("delta", {})
                content_piece = delta_dict.get("content", "")

                if content_piece is None:
                    content_piece = ""

                if content_piece == "":
                    continue

                # Add to buffers
                token_buffer.append(content_piece)
                content_buffer += content_piece

                # Check buffer every 10 tokens or when tool already detected
                if len(token_buffer) >= BUFFER_SIZE or tool_detected:

                    # Join current buffer for analysis
                    buffer_text = "".join(token_buffer)

                    # Check for tool call patterns if not already detected
                    if not tool_detected and is_potential_tool_call(content_buffer):
                        tool_detected = True
                        self._client.logger.debug(
                            "Tool call pattern detected in buffer"
                        )
                        # Don't emit tokens when tool call is detected, wait for complete JSON
                        continue

                    if tool_detected and not tool_completed:
                        # Try to extract complete tool calls from full content buffer
                        complete_json = extract_complete_tool_calls(content_buffer)

                        if complete_json:
                            # Parse tool calls
                            tool_calls = self._parse_tool_call_json(
                                complete_json, tools
                            )

                            if tool_calls:
                                # Emit tool calls instead of buffered content
                                delta_obj = Delta(
                                    role="assistant", content="", tool_calls=tool_calls
                                )
                                yield ChatResponseStream(
                                    choices=[ChoiceStream(delta=delta_obj)],
                                    usage=Usage(),
                                    message=ChatMessage(
                                        role="assistant",
                                        content="",
                                        tool_calls=tool_calls,
                                    ),
                                )
                                tool_completed = True
                                self._client.logger.debug(
                                    f"Emitted {len(tool_calls)} tool calls from buffer"
                                )
                                # Clear buffers after successful tool call
                                token_buffer.clear()
                                continue
                        else:
                            # If we can't extract complete JSON yet, continue buffering
                            continue

                    # If no tool call detected or already completed, emit buffered tokens
                    if not tool_detected or tool_completed:
                        for stream_chunk in emit_tokens(token_buffer):
                            yield stream_chunk
                        token_buffer.clear()

            # Handle any remaining tokens in buffer
            if token_buffer:
                if tool_detected and not tool_completed:
                    # Final attempt to parse tool calls
                    tool_calls = self._parse_tool_call_json(content_buffer, tools)
                    if tool_calls:
                        delta_obj = Delta(
                            role="assistant", content="", tool_calls=tool_calls
                        )
                        yield ChatResponseStream(
                            choices=[ChoiceStream(delta=delta_obj)],
                            usage=Usage(),
                            message=ChatMessage(
                                role="assistant",
                                content="",
                                tool_calls=tool_calls,
                            ),
                        )
                    else:
                        # Emit remaining tokens as regular content
                        for stream_chunk in emit_tokens(token_buffer):
                            yield stream_chunk
                else:
                    # Emit remaining tokens as regular content
                    for stream_chunk in emit_tokens(token_buffer):
                        yield stream_chunk

        except Exception as e:
            self._client.logger.error(f"Error in sync stream: {e}")
            raise
