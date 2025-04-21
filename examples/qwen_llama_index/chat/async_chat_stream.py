from qwen_api.llama_index import QwenLlamaIndex
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.types.chat import ChatMessage


async def main():
    llm = QwenLlamaIndex()
    response = await llm.astream_chat([ChatMessage(role="user", content="Apa ibu kota Indonesia?")])
    async for chunk in response:
        print(chunk.delta, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
