from dataclasses import dataclass

@dataclass(frozen=True)
class EndpointApi:
    base: str = "https://chat.qwen.ai/api/chat"
    new: str = "https://chat.qwen.ai/api/v1/chats/new"
    completions: str = "https://chat.qwen.ai/api/chat/completions"
    completed: str = "https://chat.qwen.ai/api/chat/completed"