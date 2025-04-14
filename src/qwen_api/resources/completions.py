from typing import AsyncGenerator, Generator, List, Optional, Union
import requests
import aiohttp
from ..logger import logging
from ..core.exceptions import QwenAPIError, RateLimitError
from ..types.chat import ChatCompletion, ChatMessage
from ..types.chat_model import ChatModel
from ..types.endpoint_api import EndpointApi


class Completion:
    def __init__(self, client):
        self._client = client

    def create(
        self,
        messages: List[ChatMessage],
        model: ChatModel,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        thinking: bool = False
    ) -> Union[ChatCompletion, Generator[ChatCompletion, None, None]]:
        self._client.logger.debug(f"messages: {messages}")

        model = model or self._client.default_model
        payload = self._client._build_payload(
            messages=messages,
            model=model,
            stream=stream,
            thinking=thinking,
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
            self._client.logger.info("Streaming response")
            return self._client._process_stream(response)

        return ChatCompletion(choices=response.json().get("choices", []))

    async def acreate(
        self,
        messages: List[ChatMessage],
        model: ChatModel,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking: bool = False,
        stream: bool = False
    ) -> Union[ChatCompletion, AsyncGenerator[ChatCompletion, None]]:

        model = model or self._client.default_model
        payload = self._client._build_payload(
            messages=messages,
            model=model,
            stream=stream,
            thinking=thinking,
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

        if response.status_code == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        if stream:
            return self._client._process_astream(response, session)

        try:
            data = (await response.json()).get("choices", [])
            return ChatCompletion(choices=data)
        finally:
            await session.close()
