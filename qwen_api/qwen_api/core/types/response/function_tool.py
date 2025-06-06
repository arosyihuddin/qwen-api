from pydantic import BaseModel

class FunctionDetail(BaseModel):
    name: str
    description: str
    parameters: dict

class FunctionToolParam(BaseModel):
    type: str
    function: FunctionDetail
    
class Function(BaseModel):
    name: str
    arguments: dict

class ToolCall(BaseModel):
    function: Function