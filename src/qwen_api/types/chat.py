from typing import List, Dict, Optional
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing_extensions import Literal
from llama_index.core.base.llms.types import ChatMessage as OriginalChatMessage
from enum import Enum

class MessageRole(str, Enum):
    """Message role."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"
    CHATBOT = "chatbot"
    MODEL = "model"

class FunctionCall(BaseModel):
    name: str
    arguments: str

class WebSearchInfo(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    hostname: Optional[str] = None
    hostlogo: Optional[str] = None
    date: Optional[str] = None
    
class Extra(BaseModel):
    web_search_info: List[WebSearchInfo]

class Delta(BaseModel):
    role: str
    content: str
    name: Optional[str] = ""
    function_call: Optional[FunctionCall] = None
    extra: Optional[Extra] = None

class ChoiceStream(BaseModel):
    delta: Delta

class ChatResponseStream(BaseModel):
    choices: List[ChoiceStream]

class Message(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    message: Message
    extra: Optional[Extra] = None
    
class ChatResponse(BaseModel):
    choices: Choice

class ChatMessage(OriginalChatMessage):
    web_search: bool = Field(
        default=False,
        description="Flag untuk mengaktifkan web search",
        json_schema_extra={"example": False}
    )
    thinking: bool = Field(
        default=False,
        description="Flag untuk mengaktifkan thinking mode",
        json_schema_extra={"example": False}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Apa itu RAG?",
                "web_search": True,
                "thinking": False
            }
        }
    )