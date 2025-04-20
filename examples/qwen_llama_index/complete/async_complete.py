from qwen_api.llama_index import QwenLlamaIndex

async def main():
    llm = QwenLlamaIndex()
    response = await llm.acomplete("Apa ibu kota Indonesia?")
    print(response.text)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
