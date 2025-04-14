import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError


async def main():
    client = Qwen()

    try:
        # Kirim pesan async
        response = await client.chat.acreate(
            messages=[{"role": "user", "content": "Halo"}],
            model="qwen-max-latest",
        )

        print(response)

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
