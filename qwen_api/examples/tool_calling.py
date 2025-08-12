"""
Basic Synchronous Usage Example

This script demonstrates a simple synchronous request to the Qwen API to answer
a question about the capital of Indonesia.
"""

from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


def main():
    """
    Main function that demonstrates basic synchronous usage of the Qwen API.

    1. Creates a Qwen client instance
    2. Constructs a chat message asking about the capital of Indonesia
    3. Sends the request to the Qwen API
    4. Prints the response
    """
    # Initialize the Qwen client
    client = Qwen()

    try:
        # Create the chat message
        messages = [
            ChatMessage(
                role="user",
                content="berapa 1+1?",
                web_search=False,
                thinking=False,
            )
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Useful for getting the result of a math expression. The input to this tool should be a valid mathematical expression that could be executed by a simple calculator.",
                    "parameters": {
                        "type": "object",
                        "properties": {"input": {"type": "string"}},
                    },
                },
            }
        ]

        # Send the request to the Qwen API
        response = client.chat.create(
            messages=messages,
            model="qwen3-coder-plus",
            stream=True,
            tools=tools,
        )

        for chunk in response:
            print(chunk)
            delta = chunk.choices[0].delta
            # Handle any web search information in the response
            if "extra" in delta and "web_search_info" in delta.extra:
                print("\nHasil pencarian:", delta.extra.web_search_info)
                print()

            # Print the content as it arrives
            print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
