"""
Qwen LlamaIndex Basic Chat Example

This script demonstrates using Qwen with LlamaIndex for basic chat-style interactions.
"""

from qwen_api.llama_index import QwenLlamaIndex
from llama_index.core.base.llms.types import ChatMessage


def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for basic chat-style interactions.

    1. Creates a QwenLlamaIndex instance
    2. Constructs a chat message asking about the capital of Indonesia
    3. Sends the request to the Qwen API via LlamaIndex
    4. Prints the response
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Create the chat message and send the request
    result = llm.chat([
        ChatMessage(role="user", content="Apa ibu kota Indonesia?")
    ])

    # Print the response from the API
    print(result)


if __name__ == "__main__":
    main()
