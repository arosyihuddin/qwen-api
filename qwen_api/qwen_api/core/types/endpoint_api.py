from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointAPI:
    new_chat: str = "/api/v1/chats/new"
    completions: str = "/api/chat/completions"
    completed: str = "/api/chat/completed"
    suggestions: str = "/api/task/suggestions/completions"
    upload_file: str = "/api/v1/files/getstsToken"
