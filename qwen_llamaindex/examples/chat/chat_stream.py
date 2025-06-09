"""
Qwen LlamaIndex Streaming Chat Example

This script demonstrates using Qwen with LlamaIndex for streaming chat-style interactions.
"""

from qwen_llamaindex import QwenLlamaIndex
from qwen_api.core.exceptions import QwenAPIError
from llama_index.core.base.llms.types import ChatMessage


def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for streaming chat-style interactions.

    1. Creates a QwenLlamaIndex instance
    2. Constructs a chat message asking about the capital of Indonesia
    3. Sends the request to the Qwen API via LlamaIndex with streaming enabled
    4. Processes and prints the streaming response in real-time
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()
    
    # Create the chat message and send the streaming request
    response = llm.stream_chat(
        [ChatMessage(role="user", content="Apa ibu kota Indonesia?")]
    )

    # Process and print the streaming response in real-time
    for chunk in response:
        print(chunk.delta, end="", flush=True)


if __name__ == "__main__":
    main()
