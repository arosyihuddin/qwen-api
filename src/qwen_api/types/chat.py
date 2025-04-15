from typing import List, Dict, Optional
from pydantic import BaseModel, field_validator
from typing_extensions import Literal

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

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    web_search: bool = False
    thinking: bool = False
    
    @field_validator("web_search")
    def validate_web_search(cls, v):
        return "search" if v else "t2t"  
