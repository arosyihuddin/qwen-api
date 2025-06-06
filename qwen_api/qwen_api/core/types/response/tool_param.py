
from __future__ import annotations

from typing import Union
from typing_extensions import TypeAlias
from .function_tool import FunctionToolParam

ToolParam: TypeAlias = Union[
    FunctionToolParam,
    # FileSearchToolParam,
    # WebSearchToolParam,
    # ComputerToolParam,
    # Mcp,
    # CodeInterpreter,
    # ImageGeneration,
    # LocalShell,
]