from dataclasses import dataclass

@dataclass(frozen=True)
class EndpointApi:
    new_chat: str = "https://chat.qwen.ai/api/v1/chats/new"
    completions: str = "https://chat.qwen.ai/api/chat/completions"
    completed: str = "https://chat.qwen.ai/api/chat/completed"
    suggestions: str = "https://chat.qwen.ai/api/task/suggestions/completions"