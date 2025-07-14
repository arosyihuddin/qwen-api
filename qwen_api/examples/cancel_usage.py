"""
Example showing how to cancel streaming requests

This script demonstrates how to use the cancel() method to stop ongoing requests
and close connections properly.
"""

import asyncio
import threading
import time
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock


def sync_streaming_with_cancel():
    """
    Example of synchronous streaming with manual cancellation.
    """
    print("=== Synchronous Streaming with Cancel ===")

    # Initialize the Qwen client
    client = Qwen(log_level="INFO")

    try:
        # Create a message
        messages = [
            ChatMessage(
                role="user",
                blocks=[
                    TextBlock(
                        block_type="text",
                        text="Write a very long story about a magical forest",
                    )
                ],
            )
        ]

        # Start streaming request
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process some chunks then cancel
        count = 0
        for chunk in response:
            print(chunk.choices[0].delta.content, end="", flush=True)
            count += 1

            # Cancel after 5 chunks
            if count >= 5:
                print("\n\n[CANCELLING REQUEST...]")
                client.cancel()
                break

        print("\n[REQUEST CANCELLED]")

    except QwenAPIError as e:
        print(f"Error: {str(e)}")
    finally:
        # Always close the client
        client.close()


async def async_streaming_with_cancel():
    """
    Example of asynchronous streaming with automatic cancellation using timeout.
    """
    print("\n=== Asynchronous Streaming with Cancel ===")

    # Initialize the Qwen client
    client = Qwen(log_level="INFO")

    # Create a streaming task that can be cancelled
    async def streaming_task():
        # Create a message
        messages = [
            ChatMessage(
                role="user",
                blocks=[
                    TextBlock(
                        block_type="text",
                        text="Write a very long story about a magical forest",
                    )
                ],
            )
        ]

        # Start streaming request
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process chunks
        count = 0
        async for chunk in response:
            print(chunk.choices[0].delta.content, end="", flush=True)
            count += 1

            # Break if cancelled
            if client._is_cancelled:
                print("\n[BREAKING DUE TO CANCELLATION]")
                break

        print("\n[STREAM COMPLETED]")

    try:
        # Create the streaming task
        task = asyncio.create_task(streaming_task())

        # Start a background task to cancel after 5 seconds
        async def cancel_after_delay():
            await asyncio.sleep(5)
            print("\n[CANCELLING REQUEST...]")
            client.cancel()

        cancel_task = asyncio.create_task(cancel_after_delay())

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [task, cancel_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for p in pending:
            p.cancel()

        # Check if streaming task was cancelled
        if task in done:
            try:
                await task
            except asyncio.CancelledError:
                print("[TASK CANCELLED]")
        else:
            print("[TASK CANCELLED DUE TO TIMEOUT]")

    except QwenAPIError as e:
        print(f"Error: {str(e)}")
    except asyncio.CancelledError:
        print("\n[ASYNC TASK CANCELLED]")
    finally:
        # Always close the client
        client.close()


async def cancel_after_delay(client, delay):
    """
    Cancel client after a delay.
    """
    await asyncio.sleep(delay)
    print("\n\n[CANCELLING REQUEST AFTER DELAY...]")
    client.cancel()


def context_manager_example():
    """
    Example using context manager for automatic cleanup.
    """
    print("\n=== Context Manager Example ===")

    try:
        # Using context manager ensures proper cleanup
        with Qwen(log_level="INFO") as client:
            messages = [
                ChatMessage(
                    role="user",
                    blocks=[
                        TextBlock(
                            block_type="text", text="What is the capital of Indonesia?"
                        )
                    ],
                )
            ]

            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest",
                stream=True,
            )

            for chunk in response:
                print(chunk.choices[0].delta.content, end="", flush=True)

            print("\n[STREAM COMPLETED]")

        # Client is automatically closed when exiting context
        print("[CLIENT AUTOMATICALLY CLOSED]")

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


def main():
    """
    Main function demonstrating different cancellation scenarios.
    """
    print("Qwen API Cancel Examples")
    print("=" * 40)

    # Example 1: Synchronous streaming with manual cancel
    sync_streaming_with_cancel()

    # Example 2: Asynchronous streaming with timeout cancel
    asyncio.run(async_streaming_with_cancel())

    # Example 3: Context manager with automatic cleanup
    context_manager_example()


if __name__ == "__main__":
    main()
