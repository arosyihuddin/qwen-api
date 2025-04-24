from qwen_api.llama_index import QwenLlamaIndex
from qwen_api.types.chat import ChatMessage


def main():
    llm = QwenLlamaIndex()
    result = llm.chat([
        ChatMessage(role="user", content="Apa ibu kota Indonesia?")
    ])
    print(result)


if __name__ == "__main__":
    main()
