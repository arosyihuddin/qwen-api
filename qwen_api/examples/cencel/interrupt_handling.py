"""
Example showing how to handle KeyboardInterrupt (Ctrl+C) gracefully

This script demonstrates how to handle user interruption (Ctrl+C) during streaming
and ensure proper cleanup of resources.
"""

import signal
import sys
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock


# Global client reference for signal handler
client = None


def signal_handler(signum, frame):
    """
    Handle SIGINT (Ctrl+C) gracefully.
    """
    print("\n\n[RECEIVED INTERRUPT SIGNAL]")
    if client:
        print("[CANCELLING REQUEST...]")
        client.cancel()
        print("[CLOSING CLIENT...]")
        client.close()
    print("[SHUTDOWN COMPLETE]")
    sys.exit(0)


def streaming_with_interrupt_handler():
    """
    Example of streaming with proper interrupt handling.
    """
    global client

    print("=== Streaming with Interrupt Handler ===")
    print("Press Ctrl+C to cancel the request gracefully")
    print("-" * 50)

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize the Qwen client
    client = Qwen(log_level="INFO")

    try:
        # Create a long-running request
        messages = [
            ChatMessage(
                role="user",
                blocks=[
                    TextBlock(
                        block_type="text",
                        text="Write a very detailed and long story about a magical forest with many characters and adventures",
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

        # Process chunks
        for chunk in response:
            delta = chunk.choices[0].delta

            # Handle any web search information in the response
            if (
                hasattr(delta, "extra")
                and delta.extra
                and hasattr(delta.extra, "web_search_info")
            ):
                print(f"\n[SEARCH INFO: {delta.extra.web_search_info}]\n")

            # Print the content as it arrives
            print(delta.content, end="", flush=True)

        print("\n[STREAM COMPLETED SUCCESSFULLY]")

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")
    except KeyboardInterrupt:
        # This should be handled by signal handler, but just in case
        print("\n[KEYBOARD INTERRUPT DETECTED]")
        if client:
            client.cancel()
    finally:
        # Always close the client
        if client:
            client.close()
        print("\n[CLEANUP COMPLETE]")


def main():
    """
    Main function demonstrating interrupt handling.
    """
    print("Qwen API Interrupt Handling Example")
    print("=" * 40)
    print("This example shows how to handle Ctrl+C gracefully")
    print("during streaming requests.")
    print("")

    streaming_with_interrupt_handler()


if __name__ == "__main__":
    main()
