import json
from typing import AsyncGenerator, Generator, List, Optional
import requests
import aiohttp
from sseclient import SSEClient
from .core.auth_manager import AuthManager
from .logger import setup_logger
from .types.chat import ChatCompletion, ChatMessage
from .resources.completions import Completion
from .types.chat_model import ChatModel


class Qwen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie: Optional[str] = None,
        timeout: int = 30,
        default_model: ChatModel = "qwen-max-latest",
        logging_level: str = "INFO",
        save_logs: bool = False,
    ):
        self.chat = Completion(self)
        self.timeout = timeout
        self.default_model = default_model
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
        model: str = "qwen-max-latest",
        stream: bool = False,
        thinking: Optional[bool] = False,
        max_tokens: Optional[int] = 2048
    ) -> dict:
        return {
            "stream": stream,
            "model": model,
            "incremental_output": True,
            "messages": [{
                "role": msg["role"],
                "content": msg["content"],
                "chat_type": "t2t",
                "feature_config": {"thinking_enabled": thinking},
                "extra": {}
            } for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _process_stream(self, response: requests.Response) -> Generator[ChatCompletion, None, None]:
        client = SSEClient(response)
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    yield ChatCompletion(**data)
                except json.JSONDecodeError:
                    continue

    async def _process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatCompletion, None]:
        try:
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        yield ChatCompletion(**data)
                    except json.JSONDecodeError:
                        continue
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await session.close()
