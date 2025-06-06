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
        messages = [ChatMessage(
            role="user",
            content="berapa 1+1?",
            web_search=True,
            thinking=False,
        )]

        # Send the request to the Qwen API
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            tools=[
                {'type': 'function', 
                 'function': {
                     'name': 'calculator', 
                     'description': 'Useful for getting the result of a math expression. The input to this tool should be a valid mathematical expression that could be executed by a simple calculator.', 
                     'parameters': {
                         'type': 'object', 
                         'properties': {
                             'input': {'type': 'string'}}, 
                         'additionalProperties': False, 
                         '$schema': 'http://json-schema.org/draft-07/schema#'
                         }
                     }
                 }
            ]
        )

        # Print the response from the API
        print(response)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
