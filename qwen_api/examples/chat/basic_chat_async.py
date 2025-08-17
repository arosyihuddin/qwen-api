"""
Basic Asynchronous Chat Example

This script demonstrates how to use the Qwen API asynchronously for basic chat
without any tools or special features.
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


async def main():
    """
    Main async function that demonstrates basic asynchronous chat usage.

    1. Creates a Qwen client instance
    2. Constructs a simple chat message
    3. Sends the request to the Qwen API using asynchronous methods
    4. Prints the response
    """
    # Initialize the Qwen client
    client = Qwen()

    try:
        # Create the chat messages
        messages = [
            ChatMessage(
                role="user",
                content="Ceritakan tentang sejarah Indonesia secara singkat",
                web_search=False,
                thinking=False,
            )
        ]

        # Send the request to the Qwen API using asynchronous methods
        print("Sending async request to Qwen API...")
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=False,
        )

        # Print the response from the API
        print("\n=== Response ===")
        print(f"Role: {response.choices.message.role}")
        print(f"Content: {response.choices.message.content}")

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
