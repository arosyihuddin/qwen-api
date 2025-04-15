import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.types.chat import ChatMessage


async def main():
    client = Qwen()

    try:
        messages = [ChatMessage(
            role="user", 
            content="Apa itu LLM?",
            web_search=True,
            thinking=False,
        )]
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
        )

        print(response)

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
