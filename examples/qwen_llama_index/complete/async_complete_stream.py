from qwen_api.llama_index import QwenLlamaIndex


async def main():
    llm = QwenLlamaIndex()
    response = await llm.astream_complete("Apa ibu kota Indonesia?")
    async for chunk in response:
        print(chunk.delta, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
