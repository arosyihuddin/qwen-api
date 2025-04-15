from typing import AsyncGenerator, Generator, List, Optional, Union
import requests
import aiohttp
from ..core.exceptions import QwenAPIError, RateLimitError
from ..types.chat import ChatResponseStream, ChatResponse, ChatMessage
from ..types.chat_model import ChatModel
from ..types.endpoint_api import EndpointApi

class Completion:
    def __init__(self, client):
        self._client = client

    def create(
        self,
        messages: List[ChatMessage],
        model: ChatModel = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
    ) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]:
        self._client.logger.debug(f"messages: {messages}")

        payload = self._client._build_payload(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens
        )

        response = requests.post(
            EndpointApi.completions,
            headers=self._client._build_headers(),
            json=payload,
            timeout=self._client.timeout,
            stream=stream
        )

        self._client.logger.info(f"Response: {response.status_code}")

        if not response.ok:
            error_text = response.text()
            self._client.logger.error(
                f"API Error: {response.status} {error_text}")
            raise QwenAPIError(f"API Error: {response.status} {error_text}")

        if response.status_code == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        if stream:
            return self._client._process_stream(response)
        
        return self._client._process_response(response)

    async def acreate(
        self,
        messages: List[ChatMessage],
        model: ChatModel = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]:
        self._client.logger.debug(f"messages: {messages}")

        payload = self._client._build_payload(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens
        )

        session = aiohttp.ClientSession()
        response = await session.post(
            EndpointApi.completions,
            headers=self._client._build_headers(),
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120)
        )

        self._client.logger.info(f"Response status: {response.status}")

        if not response.ok:
            error_text = await response.text()
            self._client.logger.error(
                f"API Error: {response.status} {error_text}")
            raise QwenAPIError(f"API Error: {response.status} {error_text}")

        if response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        if stream:
            return self._client._process_astream(response, session)

        try:
            return await self._client._process_aresponse(response, session)
            data = (await response.json()).get("choices", [])
            print(data)
            return ChatResponse(choices=data)
        finally:
            await session.close()
