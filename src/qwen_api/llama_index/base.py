import os
from qwen_api.core.types.endpoint_api import EndpointAPI
from typing import Any, Dict, Optional, AsyncGenerator, Generator, Sequence, List
from llama_index.core.base.llms.types import (
    ChatResponse,
    CompletionResponse,
    CompletionResponseAsyncGen,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_chat_callback, llm_completion_callback
from llama_index.core.base.llms.generic_utils import get_from_param_or_env
from pydantic import Field, ConfigDict
import requests
import aiohttp
import json
from sseclient import SSEClient
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from qwen_api.logger import setup_logger
from qwen_api.core.exceptions import QwenAPIError, RateLimitError
from llama_index.core.llms.llm import LLM
from qwen_api.core.types.chat_model import ChatModel

logging = setup_logger("INFO", False)


DEFAULT_API_BASE = os.getenv(
    "QWEN_API_BASE", "https://chat.qwen.ai")
DEFAULT_MODEL = "qwen-max-latest"


class QwenLlamaIndex(LLM):
    cookie: Optional[str] = Field(
        default=None,
        description="Cookie authentication untuk Qwen API"
    )
    context_window: int = Field(
        default=6144,
        description="Ukuran context window model Qwen"
    )
    is_chat_model: bool = Field(
        default=True,
        description="Flag untuk model chat"
    )
    supports_function_calling: bool = Field(
        default=True,
        description="Flag untuk dukungan function calling"
    )
    model_config = ConfigDict(extra="allow")

    def __init__(
        self,
        auth_token: Optional[str] = None,
        cookie: Optional[str] = None,
        model: ChatModel = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1500,
        **kwargs: Any,
    ):
        auth_token = get_from_param_or_env(
            "auth_token", auth_token, "QWEN_AUTH_TOKEN")
        cookie = get_from_param_or_env("cookie", cookie, "QWEN_COOKIE")

        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=auth_token,
            **kwargs
        )
        self.cookie = cookie

    @classmethod
    def class_name(cls) -> str:
        return "QwenLlamaIndex"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.max_tokens or -1,
            is_chat_model=self.is_chat_model,
            model_name=self.model,
            is_function_calling_model=self.supports_function_calling,
        )

    def cencel(self) -> None:
        """
        Cancel the current request.
        """
        # Implement cancellation logic if needed
        pass

    def _get_headers(self) -> Dict[str, str]:
        api_key = self.api_key or os.getenv('QWEN_API_KEY')
        if not api_key:
            raise ValueError(
                "API Key tidak ditemukan. Harap set QWEN_API_KEY atau berikan auth_token.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Host": "chat.qwen.ai",
            "Origin": "https://chat.qwen.ai"
        }

        return headers

    def _get_request_payload(self, messages: List[ChatMessage], **kwargs: Any) -> Dict[str, Any]:
        """
        Prepare request payload for Qwen API while maintaining compatibility with LlamaIndex.

        The method ensures compatibility by handling both ChatMessage instances and dictionaries,
        and properly formatting the messages for the Qwen API.
        """
        # Convert messages to dictionary format if needed
        validated_messages = []
        for msg in messages:
            # If message is already a dictionary, add it directly
            if isinstance(msg, dict):
                validated_messages.append(msg)
            # If message is a ChatMessage instance, convert it to dictionary
            elif hasattr(msg, "to_dict") and callable(msg.to_dict):
                validated_messages.append(msg.to_dict())
            # If message is a BaseModel, use model_dump
            elif hasattr(msg, "model_dump") and callable(msg.model_dump):
                validated_messages.append(msg.model_dump())
            # If message is neither, try to convert using dict()
            elif hasattr(msg, "__dict__"):
                validated_messages.append(dict(msg))
            # If all else fails, raise type error
            else:
                raise TypeError(
                    f"Cannot convert message of type {type(msg)} to dictionary")

        # Ensure each message has the required fields
        result_messages = []
        for msg in validated_messages:
            # Create message with guaranteed fields
            safe_msg = {
                "role": str(msg.get("role", "user")),
                "content": str(msg.get("content", "")),
                "additional_kwargs": dict(msg.get("additional_kwargs", {})),
                "web_search": bool(msg.get("web_search", False)),
                "thinking": bool(msg.get("thinking", False)),
                "blocks": list(msg.get("blocks", []))
            }

            result_messages.append(safe_msg)

        return {
            "model": self.model,
            "messages": [{
                "role": msg["role"],
                "content": msg["content"],
                "chat_type": "search" if msg["web_search"] else "t2t",
                "feature_config": {
                    "thinking_enabled": msg["thinking"]
                }
            } for msg in result_messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
            "incremental_output": True
        }

    def _process_response(self, response: requests.Response) -> ChatResponse:
        client = SSEClient(response)
        message = {}
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        message["extra"] = (
                            data["choices"][0]["delta"].get("extra"))
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        message["message"] = {"role": "assistant", "content": text}
        return ChatResponse(message=ChatMessage(role="assistant", content=text), raw=data)

    def _process_stream_response(self, response: requests.Response) -> Generator[ChatResponse, None, None]:
        client = SSEClient(response)
        content = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    delta = data["choices"][0]["delta"]
                    content += delta.get("content")
                    chat_response = ChatResponse(
                        message=ChatMessage(
                            role=delta.get("role"),
                            content=content
                        ),
                        delta=delta.get("content"),
                        raw=data
                    )
                    yield chat_response

                except json.JSONDecodeError:
                    continue
                except KeyError:
                    continue

    async def _process_aresponse(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse:
        try:
            message = {}
            text = ""
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            message["extra"] = (
                                data["choices"][0]["delta"].get("extra"))
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            message["message"] = {
                "role": MessageRole.ASSISTANT, "content": text}
            return ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=text), raw=data)
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await session.close()

    async def _process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatResponse, None]:
        content = ""
        try:
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        delta = data["choices"][0]["delta"]
                        content += delta.get("content")
                        yield ChatResponse(
                            message=ChatMessage(
                                role=delta.get("role"),
                                content=content
                            ),
                            delta=delta.get("content"),
                            raw=data
                        )
                    except json.JSONDecodeError:
                        continue
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await session.close()

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        messages = [ChatMessage(role="user", content=prompt)]
        result = self.chat(messages=messages, **kwargs)
        return CompletionResponse(text=result.message.content, raw=result.raw)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs) -> CompletionResponse:
        messages = [ChatMessage(role="user", content=prompt)]
        response_generator = self.stream_chat(messages=messages, **kwargs)

        def gen() -> CompletionResponseGen:
            for chat_response in response_generator:
                completion_response = CompletionResponse(
                    text=chat_response.delta,
                    delta=chat_response.delta,
                    raw=chat_response.raw
                )
                yield completion_response
        return gen()

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        payload = self._get_request_payload(messages, **kwargs)
        response = requests.post(
            DEFAULT_API_BASE + EndpointAPI.completions,
            headers=self._get_headers(),
            json=payload,
            stream=True
        )
        logging.info(f"Response: {response.status_code}")
        return self._process_response(response)

    @llm_chat_callback()
    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs) -> ChatResponse:
        print(messages)
        payload = self._get_request_payload(messages, **kwargs)
        response = requests.post(
            DEFAULT_API_BASE + EndpointAPI.completions,
            headers=self._get_headers(),
            json=payload,
            stream=True
        )

        logging.info(f"Response: {response.status_code}")
        return self._process_stream_response(response)

    @llm_completion_callback()
    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        messages = [ChatMessage(role="user", content=prompt)]
        result = await self.achat(messages=messages, **kwargs)
        return CompletionResponse(text=result.message.content, raw=result.raw)

    @llm_completion_callback()
    async def astream_complete(self, prompt: str, **kwargs) -> CompletionResponse:
        messages = [ChatMessage(role="user", content=prompt)]
        response_generator = await self.astream_chat(messages=messages, **kwargs)

        async def async_gen() -> CompletionResponseAsyncGen:
            async for chat_response in response_generator:
                completion_response = CompletionResponse(
                    text=chat_response.delta,
                    delta=chat_response.delta,
                    raw=chat_response.raw
                )
                yield completion_response
        return async_gen()

    @llm_chat_callback()
    async def achat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResponse:
        payload = self._get_request_payload(messages, **kwargs)
        session = aiohttp.ClientSession()
        response = await session.post(
            DEFAULT_API_BASE + EndpointAPI.completions,
            headers=self._get_headers(),
            json=payload,
        )

        logging.info(f"Response: {response.status}")

        if not response.ok:
            error_text = await response.text()
            logging.error(
                f"API Error: {response.status} {error_text}")
            raise QwenAPIError(f"API Error: {response.status} {error_text}")

        if response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        return await self._process_aresponse(response, session)

    @llm_chat_callback()
    async def astream_chat(self, messages: Sequence[dict | ChatMessage], **kwargs: Any) -> AsyncGenerator[ChatResponse, None]:
        """
        Stream chat responses asynchronously.

        Converts input messages to standardized format for processing.
        Ensures compatibility with LlamaIndex and proper event tracking.
        """
        # Standardize all incoming messages to ChatMessage format
        payload = self._get_request_payload(messages, **kwargs)
        session = aiohttp.ClientSession()
        response = await session.post(
            DEFAULT_API_BASE + EndpointAPI.completions,
            headers=self._get_headers(),
            json=payload
        )
        response.raise_for_status()

        logging.info(f"Response: {response.status}")

        if not response.ok:
            error_text = await response.text()
            logging.error(
                f"API Error: {response.status} {error_text}")
            raise QwenAPIError(f"API Error: {response.status} {error_text}")

        if response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        return self._process_astream(response, session)
