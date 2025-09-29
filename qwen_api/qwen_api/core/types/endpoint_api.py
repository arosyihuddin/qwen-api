from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointAPI:
    new_chat: str = "/api/v1/chats/new"
    completions: str = "/api/v2/chat/completions"
    completed: str = "/api/v2/chat/completed"
    suggestions: str = "/api/v2/task/suggestions/completions"
    upload_file: str = "/api/v1/files/getstsToken"
