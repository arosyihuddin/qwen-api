from typing_extensions import Literal, TypeAlias

ChatModel: TypeAlias = Literal[
    "qwen-max-latest",
    "qwen-plus-latest",
    "qwq-32b",
    "qwen-turbo-latest",
    "qwen2.5-omni-7b",
]
