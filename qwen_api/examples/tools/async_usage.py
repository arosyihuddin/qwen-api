"""
Basic Asynchronous Usage Example

This script demonstrates how to use the Qwen API asynchronously to answer
a question about the capital of Indonesia.
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


async def main():
    """
    Main async function that demonstrates basic asynchronous usage of the Qwen API.

    1. Creates a Qwen client instance
    2. Constructs a chat message asking about the capital of Indonesia
    3. Sends the request to the Qwen API using asynchronous methods
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

        # Send the request to the Qwen API using asynchronous methods
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "description": "Useful for getting the result of a math expression. The input to this tool should be a valid mathematical expression that could be executed by a simple calculator.",
                        "parameters": {
                            "type": "object",
                            "properties": {"input": {"type": "string"}},
                            "additionalProperties": False,
                            "$schema": "http://json-schema.org/draft-07/schema#",
                        },
                    },
                }
            ],
        )

        # Print the response from the API
        print(response)

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
