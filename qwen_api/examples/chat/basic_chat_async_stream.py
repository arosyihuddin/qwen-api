"""
Basic Asynchronous Streaming Chat Example

This script demonstrates how to use the Qwen API asynchronously with streaming enabled for basic chat
without any tools or special features. The response is streamed in real-time.
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


async def main():
    """
    Main async function that demonstrates basic asynchronous streaming chat usage.

    1. Creates a Qwen client instance
    2. Constructs a simple chat message
    3. Sends the request to the Qwen API using asynchronous methods with streaming
    4. Processes and prints the streaming response in real-time
    """
    # Initialize the Qwen client
    client = Qwen()

    try:
        # Create the chat messages
        messages = [
            ChatMessage(
                role="user",
                content="Jelaskan apa itu kecerdasan buatan dalam bahasa yang mudah dipahami",
                web_search=False,
                thinking=False,
            )
        ]

        # Send the request to the Qwen API using asynchronous methods with streaming
        print("Sending async streaming request to Qwen API...")
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
            temperature=0.7,
            max_tokens=1024,
        )

        # Process and print the streaming response in real-time
        print("\n=== Streaming Response ===")
        full_content = ""
        async for chunk in response:
            delta = chunk.choices[0].delta
            # Handle any web search information in the response
            if (
                delta.extra
                and hasattr(delta.extra, "web_search_info")
                and delta.extra.web_search_info
            ):
                print("\nHasil pencarian:", delta.extra.web_search_info)
                print()

            # Print the content as it arrives
            if delta.content:
                print(delta.content, end="", flush=True)
                full_content += delta.content

        print("\n\n=== Full Response ===")
        print(f"Content: {full_content}")

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
