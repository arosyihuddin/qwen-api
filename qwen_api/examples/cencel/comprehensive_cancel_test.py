"""
Comprehensive Cancel and Connection Management Examples

This script demonstrates all the cancel and connection management features
of the Qwen API client.
"""

import asyncio
import signal
import sys
import time
import threading
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock


def test_basic_cancel():
    """Test basic cancel functionality."""
    print("1. Testing Basic Cancel")
    print("-" * 30)

    client = Qwen(log_level="INFO")

    try:
        messages = [
            ChatMessage(
                role="user",
                blocks=[TextBlock(block_type="text", text="Count from 1 to 100")],
            )
        ]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        count = 0
        for chunk in response:
            print(f"Chunk {count + 1}: {chunk.choices[0].delta.content[:50]}...")
            count += 1

            if count >= 3:
                print("\n🛑 Cancelling after 3 chunks...")
                client.cancel()
                break

        print("✅ Basic cancel test completed\n")

    except QwenAPIError as e:
        print(f"❌ Error: {e}\n")
    finally:
        client.close()


def test_context_manager():
    """Test context manager automatic cleanup."""
    print("2. Testing Context Manager")
    print("-" * 30)

    try:
        with Qwen(log_level="INFO") as client:
            messages = [
                ChatMessage(
                    role="user",
                    blocks=[TextBlock(block_type="text", text="Hello, world!")],
                )
            ]

            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest",
                stream=True,
            )

            for chunk in response:
                print(chunk.choices[0].delta.content, end="", flush=True)

        print("\n✅ Context manager test completed (auto-closed)\n")

    except QwenAPIError as e:
        print(f"❌ Error: {e}\n")


async def test_async_cancel():
    """Test async cancel functionality."""
    print("3. Testing Async Cancel")
    print("-" * 30)

    client = Qwen(log_level="INFO")

    try:
        messages = [
            ChatMessage(
                role="user",
                blocks=[TextBlock(block_type="text", text="Write a long poem")],
            )
        ]

        # Schedule cancellation after 2 seconds
        async def cancel_later():
            await asyncio.sleep(2)
            print("\n🛑 Auto-cancelling after 2 seconds...")
            client.cancel()

        cancel_task = asyncio.create_task(cancel_later())

        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        chunk_count = 0
        async for chunk in response:
            print(chunk.choices[0].delta.content, end="", flush=True)
            chunk_count += 1

            # Break if cancelled
            if client._is_cancelled:
                break

        await cancel_task
        print(f"\n✅ Async cancel test completed ({chunk_count} chunks)\n")

    except QwenAPIError as e:
        print(f"❌ Error: {e}\n")
    finally:
        client.close()


def test_multiple_requests():
    """Test cancelling multiple concurrent requests."""
    print("4. Testing Multiple Requests Cancel")
    print("-" * 30)

    async def make_request(client, request_id):
        """Make a single request."""
        try:
            messages = [
                ChatMessage(
                    role="user",
                    blocks=[
                        TextBlock(
                            block_type="text",
                            text=f"Request {request_id}: Tell me a story",
                        )
                    ],
                )
            ]

            response = await client.chat.acreate(
                messages=messages,
                model="qwen-max-latest",
                stream=True,
            )

            chunk_count = 0
            async for chunk in response:
                chunk_count += 1
                if chunk_count <= 3:  # Only show first 3 chunks
                    print(f"[Req{request_id}] {chunk.choices[0].delta.content[:30]}...")

                if client._is_cancelled:
                    break

            print(f"[Req{request_id}] Completed with {chunk_count} chunks")

        except QwenAPIError as e:
            print(f"[Req{request_id}] Error: {e}")

    async def run_multiple():
        client = Qwen(log_level="INFO")

        try:
            # Start multiple requests
            tasks = [asyncio.create_task(make_request(client, i)) for i in range(1, 4)]

            # Cancel after 3 seconds
            await asyncio.sleep(3)
            print("\n🛑 Cancelling all requests...")
            client.cancel()

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            print("✅ Multiple requests cancel test completed\n")

        finally:
            client.close()

    asyncio.run(run_multiple())


def test_graceful_shutdown():
    """Test graceful shutdown with signal handling."""
    print("5. Testing Graceful Shutdown")
    print("-" * 30)
    print("Press Ctrl+C within 5 seconds to test signal handling...")

    client = None

    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal!")
        if client:
            client.cancel()
            client.close()
        print("✅ Graceful shutdown completed")
        sys.exit(0)

    # Set up signal handler
    original_handler = signal.signal(signal.SIGINT, signal_handler)

    try:
        client = Qwen(log_level="INFO")

        messages = [
            ChatMessage(
                role="user",
                blocks=[TextBlock(block_type="text", text="Tell me a very long story")],
            )
        ]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        print("Starting stream (press Ctrl+C to test interrupt)...")

        for chunk in response:
            print(".", end="", flush=True)
            time.sleep(0.1)  # Slow down to allow interrupt

        print("\n✅ Graceful shutdown test completed (no interrupt)\n")

    except KeyboardInterrupt:
        print("\n✅ Graceful shutdown test completed (interrupted)\n")
    except QwenAPIError as e:
        print(f"❌ Error: {e}\n")
    finally:
        if client:
            client.close()
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_handler)


def test_session_tracking():
    """Test session tracking functionality."""
    print("6. Testing Session Tracking")
    print("-" * 30)

    async def run_session_test():
        client = Qwen(log_level="INFO")

        try:
            print(f"Initial active sessions: {len(client._active_sessions)}")

            messages = [
                ChatMessage(
                    role="user",
                    blocks=[TextBlock(block_type="text", text="Short response please")],
                )
            ]

            # Start async request
            response = await client.chat.acreate(
                messages=messages,
                model="qwen-max-latest",
                stream=True,
            )

            print(f"Active sessions during request: {len(client._active_sessions)}")

            chunk_count = 0
            async for chunk in response:
                chunk_count += 1
                if chunk_count <= 2:
                    print(
                        f"Chunk {chunk_count}: {chunk.choices[0].delta.content[:30]}..."
                    )

            print(f"Active sessions after completion: {len(client._active_sessions)}")
            print("✅ Session tracking test completed\n")

        finally:
            client.close()

    asyncio.run(run_session_test())


def main():
    """Run all cancel and connection management tests."""
    print("🧪 Qwen API Cancel & Connection Management Tests")
    print("=" * 50)
    print()

    # Run all tests
    test_basic_cancel()
    test_context_manager()
    asyncio.run(test_async_cancel())
    test_multiple_requests()
    test_graceful_shutdown()
    test_session_tracking()

    print("🎉 All tests completed!")


if __name__ == "__main__":
    main()
