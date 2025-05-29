from qwen_llamaindex import QwenLlamaIndex
from llama_index.core.base.llms.types import ChatMessage

async def main():
    llm = QwenLlamaIndex()
    result = await llm.achat([
        ChatMessage(role="user", content="Apa ibu kota Indonesia?")
    ])
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

