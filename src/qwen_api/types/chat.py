from typing import List, Dict
from pydantic import BaseModel
from typing_extensions import Literal


class ChatCompletion(BaseModel):
    choices: List[Dict]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    chat_type: Literal["t2t", "search"] = "t2t"
    feature_config: Dict[str, bool] = {"thinking_enabled": False}
