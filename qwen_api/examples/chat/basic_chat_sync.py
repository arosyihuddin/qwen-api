"""
Basic Synchronous Chat Example

This script demonstrates how to use the Qwen API synchronously for basic chat
without any tools or special features.
"""

from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


def main():
    """
    Main function that demonstrates basic synchronous chat usage.

    1. Creates a Qwen client instance
    2. Constructs a simple chat message
    3. Sends the request to the Qwen API using synchronous methods
    4. Prints the response
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

        # Send the request to the Qwen API using synchronous methods
        print("Sending request to Qwen API...")
        response = client.chat.create(
            messages=messages, model="qwen-max-latest", temperature=0.7, max_tokens=1024
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
    main()
