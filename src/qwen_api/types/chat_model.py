from typing_extensions import Literal, TypeAlias

ChatModel: TypeAlias = Literal[
    "qwen-max-latest",
    "qwen-plus-latest",
    "qwq-32b",
    "qwen-turbo-latest",
    "qwen2.5-omni-7b",
    "qvq-72b-preview-0310",
    "qwen2.5-vl-32b-instruct",
    "qwen2.5-14b-instruct-1m",
    "qwen2.5-coder-32b-instruct",
    "qwen2.5-72b-instruct"
]
