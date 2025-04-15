import json
from typing import AsyncGenerator, Generator, List, Optional
import requests
import aiohttp
from sseclient import SSEClient
from .core.auth_manager import AuthManager
from .logger import setup_logger
from .types.chat import ChatResponse,  ChatResponseStream, ChatMessage
from .resources.completions import Completion
from pydantic import ValidationError


class Qwen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie: Optional[str] = None,
        timeout: int = 30,
        logging_level: str = "INFO",
        save_logs: bool = False,
    ):
        self.chat = Completion(self)
        self.timeout = timeout
        self.auth = AuthManager(token=api_key, cookie=cookie)
        self.logger = setup_logger(
            logging_level=logging_level, save_logs=save_logs)

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": self.auth.get_token(),
            "Cookie": self.auth.get_cookie(),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        }

    def _build_payload(
        self,
        messages: List[ChatMessage],
        temperature: float,
        model: str,
        stream: bool,
        max_tokens: Optional[int] 
    ) -> dict:
        validated_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                try:
                    validated_msg = ChatMessage(**msg)
                except ValidationError as e:
                    raise ValueError(f"Error validating message: {e}")
            else:
                validated_msg = msg  
            validated_messages.append(validated_msg)
        return {
            "stream": True,
            "model": model,
            "incremental_output": True,
            "messages": [{
                "role": msg.role,
                "content": msg.content,
                "chat_type": msg.web_search,
                "feature_config": {"thinking_enabled": msg.thinking},
                "extra": {}
            } for msg in validated_messages],
            "temperature": temperature,
            "max_tokens": max_tokens
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
                        message["extra"] = (data["choices"][0]["delta"].get("extra"))
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        message["message"] = {"role": "assistant","content": text}
        return ChatResponse(choices=message)
    
    async def _process_aresponse(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse:
        try:
            message = {}
            text = ""
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            message["extra"] = (data["choices"][0]["delta"].get("extra"))
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            message["message"] = {"role": "assistant","content": text}
            return ChatResponse(choices=message)
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await session.close()

    def _process_stream(self, response: requests.Response) -> Generator[ChatResponseStream, None, None]:
        client = SSEClient(response)
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    yield ChatResponseStream(**data)
                except json.JSONDecodeError:
                    continue

    async def _process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatResponseStream, None]:
        try:
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        yield ChatResponseStream(**data)
                    except json.JSONDecodeError:
                        continue
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await session.close()
