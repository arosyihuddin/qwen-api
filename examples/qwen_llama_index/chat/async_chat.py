from qwen_api.llama_index import QwenLlamaIndex
from qwen_api.types.chat import ChatMessage

async def main():
    llm = QwenLlamaIndex()
    result = await llm.achat([
        ChatMessage(role="user", content="Apa ibu kota Indonesia?")
    ])
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

