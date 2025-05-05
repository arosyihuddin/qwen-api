import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.types.chat import ChatMessage


async def main():
    client = Qwen()

    try:
        messages = [ChatMessage(
            role="user",
            content="Apa ibu kota Indonesia?",
            web_search=False,
            thinking=False,
        )]
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            # model="qwq-32b",
            # model="qwen3-32b",
            # model="qwen3-30b-a3b",
            # model="qwen3-235b-a22b",
            # model="qwen2.5-vl-32b-instruct",
            # model="qwen2.5-omni-7b",
            # model="qwen2.5-coder-32b-instruct",
            # model="qwen2.5-72b-instruct",
            # model="qwen2.5-14b-instruct-1m",
            # model="qwen-turbo-2025-02-11",
            # model="qwen-plus-2025-01-25",
            # model="qvq-72b-preview-0310",
            stream=True,

        )

        async for chunk in response:
            if chunk.choices[0].delta.extra:
                print("Hasil pencarian:",
                      chunk.choices[0].delta.extra.web_search_info)
                print()

            print(chunk.choices[0].delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
