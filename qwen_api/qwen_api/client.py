import json
from typing import AsyncGenerator, Generator, List, Optional
import requests
import aiohttp
from sseclient import SSEClient
from pydantic import ValidationError
from .core.auth_manager import AuthManager
from .logger import setup_logger
from .core.types.chat import ChatResponse, ChatResponseStream, ChatMessage, MessageRole
from .resources.completions import Completion
from .utils.promp_system import WEB_DEVELOPMENT_PROMPT
from .core.exceptions import QwenAPIError
from .core.types.response.function_tool import ToolCall, Function


class Qwen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie: Optional[str] = None,
        base_url: str = "https://chat.qwen.ai",
        timeout: int = 600,
        log_level: str = "INFO",
        save_logs: bool = False,
    ):
        self.chat = Completion(self)
        self.timeout = timeout
        self.auth = AuthManager(token=api_key, cookie=cookie)
        self.logger = setup_logger(log_level=log_level, save_logs=save_logs)
        self.base_url = base_url
        self._active_sessions = []
        self._is_cancelled = False

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": self.auth.get_token(),
            "Cookie": self.auth.get_cookie(),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Host": "chat.qwen.ai",
            "Origin": "https://chat.qwen.ai",
        }

    def _build_payload(
        self,
        messages: List[ChatMessage],
        temperature: float,
        model: str,
        max_tokens: Optional[int],
    ) -> dict:
        validated_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                try:
                    validated_msg = ChatMessage(**msg)
                except ValidationError as e:
                    raise QwenAPIError(f"Error validating message: {e}")
            else:
                validated_msg = msg

            if validated_msg.role == "system":
                if (
                    validated_msg.web_development
                    and WEB_DEVELOPMENT_PROMPT not in validated_msg.content
                ):
                    updated_content = (
                        f"{validated_msg.content}\n\n{WEB_DEVELOPMENT_PROMPT}"
                    )
                    validated_msg = ChatMessage(
                        **{**validated_msg.model_dump(), "content": updated_content}
                    )

            validated_messages.append(
                {
                    "role": (
                        MessageRole.FUNCTION
                        if validated_msg.role == MessageRole.TOOL
                        else (
                            validated_msg.role
                            if validated_msg.role == MessageRole.SYSTEM
                            else MessageRole.USER
                        )
                    ),
                    "content": (
                        validated_msg.blocks[0].text
                        if len(validated_msg.blocks) == 1
                        and validated_msg.blocks[0].block_type == "text"
                        else [
                            (
                                {"type": "text", "text": block.text}
                                if block.block_type == "text"
                                else (
                                    {"type": "image", "image": str(block.url)}
                                    if block.block_type == "image"
                                    else {"type": block.block_type}
                                )
                            )
                            for block in validated_msg.blocks
                        ]
                    ),
                    "chat_type": (
                        "artifacts"
                        if getattr(validated_msg, "web_development", False)
                        else (
                            "search"
                            if getattr(validated_msg, "web_search", False)
                            else "t2t"
                        )
                    ),
                    "feature_config": {
                        "thinking_enabled": getattr(validated_msg, "thinking", False),
                        "thinking_budget": getattr(validated_msg, "thinking_budget", 0),
                        "output_schema": getattr(validated_msg, "output_schema", None),
                    },
                    "extra": {},
                }
            )

        return {
            "stream": True,
            "model": model,
            "incremental_output": True,
            "messages": validated_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _process_response(self, response: requests.Response) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        client = SSEClient(response)
        extra = None
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        extra_data = data["choices"][0]["delta"].get("extra")
                        if extra_data:
                            extra = Extra(**extra_data)
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        message = Message(role="assistant", content=text)
        choice = Choice(message=message, extra=extra)
        return ChatResponse(choices=choice)

    def _process_response_tool(self, response: requests.Response) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        client = SSEClient(response)
        extra = None
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        extra_data = data["choices"][0]["delta"].get("extra")
                        if extra_data:
                            extra = Extra(**extra_data)
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        try:
            self.logger.debug(f"text: {text}")
            parse_json = json.loads(text)
            if isinstance(parse_json["arguments"], str):
                parse_arguments = json.loads(parse_json["arguments"])
            else:
                parse_arguments = parse_json["arguments"]
            self.logger.debug(f"parse_json: {parse_json}")
            self.logger.debug(f"arguments: {parse_arguments}")
            function = Function(name=parse_json["name"], arguments=parse_arguments)
            message = Message(
                role="assistant", content="", tool_calls=[ToolCall(function=function)]
            )
            choice = Choice(message=message, extra=extra)
            return ChatResponse(choices=choice)
        except json.JSONDecodeError as e:
            return QwenAPIError(f"Error decoding JSON response: {e}")

    async def _process_aresponse(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        # Track this session
        self._active_sessions.append(session)

        try:
            extra = None
            text = ""
            async for line in response.content:
                # Check if cancelled
                if self._is_cancelled:
                    self.logger.info("Async response processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            extra_data = data["choices"][0]["delta"].get("extra")
                            if extra_data:
                                extra = Extra(**extra_data)
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            message = Message(role="assistant", content=text)
            choice = Choice(message=message, extra=extra)
            return ChatResponse(choices=choice)
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)
            await session.close()

    async def _process_aresponse_tool(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        # Track this session
        self._active_sessions.append(session)

        try:
            extra = None
            text = ""
            async for line in response.content:
                # Check if cancelled
                if self._is_cancelled:
                    self.logger.info("Async tool response processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            extra_data = data["choices"][0]["delta"].get("extra")
                            if extra_data:
                                extra = Extra(**extra_data)
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            try:
                self.logger.debug(f"text: {text}")
                parse_json = json.loads(text)
                if isinstance(parse_json["arguments"], str):
                    parse_arguments = json.loads(parse_json["arguments"])
                else:
                    parse_arguments = parse_json["arguments"]
                self.logger.debug(f"parse_json: {parse_json}")
                self.logger.debug(f"arguments: {parse_arguments}")
                function = Function(name=parse_json["name"], arguments=parse_arguments)
                message = Message(
                    role="assistant",
                    content="",
                    tool_calls=[ToolCall(function=function)],
                )
                choice = Choice(message=message, extra=extra)
                return ChatResponse(choices=choice)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON response: {e}")
                return QwenAPIError(f"Error decoding JSON response: {e}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)
            await session.close()

    def _process_stream(
        self, response: requests.Response
    ) -> Generator[ChatResponseStream, None, None]:
        client = SSEClient(response)
        content = ""
        for event in client.events():
            # Check if cancelled
            if self._is_cancelled:
                self.logger.info("Stream processing cancelled")
                break

            if event.data:
                try:
                    data = json.loads(event.data)
                    content += data["choices"][0]["delta"].get("content")
                    yield ChatResponseStream(
                        **data,
                        message=ChatMessage(
                            role=data["choices"][0]["delta"].get("role"),
                            content=content,
                        ),
                    )
                except json.JSONDecodeError:
                    continue

    async def _process_astream(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> AsyncGenerator[ChatResponseStream, None]:
        # Track this session
        self._active_sessions.append(session)

        try:
            content = ""
            import asyncio

            # Create a task for reading content
            async def read_content():
                async for line in response.content:
                    if self._is_cancelled:
                        break
                    yield line

            # Process stream with cancellation support
            async for line in read_content():
                # Check if cancelled before processing each line
                if self._is_cancelled:
                    self.logger.info("Async stream processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        content += data["choices"][0]["delta"].get("content")

                        # Yield the chunk
                        yield ChatResponseStream(
                            **data,
                            message=ChatMessage(
                                role=data["choices"][0]["delta"].get("role"),
                                content=content,
                            ),
                        )

                        # Give other coroutines a chance to run and check cancellation
                        await asyncio.sleep(0)

                    except json.JSONDecodeError:
                        continue

        except (aiohttp.ClientError, asyncio.CancelledError) as e:
            if isinstance(e, asyncio.CancelledError):
                self.logger.info("Stream was cancelled")
            else:
                self.logger.error(f"Client error: {e}")
            # Don't re-raise CancelledError, just clean up
            if not isinstance(e, asyncio.CancelledError):
                raise

        finally:
            self.logger.debug(f"Closing session")
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)

            # Force close the session immediately when cancelled
            if not session.closed:
                await session.close()

    def cancel(self):
        """
        Cancel all active requests and close connections.
        """
        self._is_cancelled = True
        self.logger.info("Cancelling all active requests...")

        # Close all active sessions aggressively
        for session in self._active_sessions[
            :
        ]:  # Copy list to avoid modification during iteration
            try:
                if hasattr(session, "close") and not session.closed:
                    # For aiohttp sessions, close immediately
                    if hasattr(session, "_connector") and session._connector:
                        # Force close connector immediately
                        session._connector._ssl_shutdown_timeout = 0.1
                        session._connector.close()

                    # Also try to close the session itself
                    import asyncio

                    if asyncio.iscoroutinefunction(session.close):
                        # Schedule session closure if we're in an async context
                        try:
                            loop = asyncio.get_running_loop()
                            task = loop.create_task(session.close())
                            # Cancel the task immediately to force close
                            task.cancel()
                        except RuntimeError:
                            # No running loop, can't close async session synchronously
                            pass

                    self.logger.debug(f"Session {id(session)} marked for closure")
            except Exception as e:
                # Suppress SSL shutdown timeout warnings as they're expected during cancellation
                if "SSL shutdown timed out" not in str(
                    e
                ) and "CancelledError" not in str(e):
                    self.logger.warning(f"Error closing session {id(session)}: {e}")

        # Clear the sessions list
        self._active_sessions.clear()
        self.logger.info("All active sessions cancelled")

    def close(self):
        """
        Close the client and clean up resources.
        """
        self.cancel()
        self.logger.info("Qwen client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
