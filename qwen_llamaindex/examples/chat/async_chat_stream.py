"""
Qwen LlamaIndex Asynchronous Streaming Chat Example

This script demonstrates using Qwen with LlamaIndex for asynchronous streaming chat-style interactions.
"""

from qwen_llamaindex import QwenLlamaIndex
from qwen_api.core.exceptions import QwenAPIError
from llama_index.core.base.llms.types import ChatMessage, MessageRole


async def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for asynchronous streaming chat-style interactions.

    1. Creates a QwenLlamaIndex instance
    2. Constructs a chat message asking about the capital of Indonesia
    3. Sends the request to the Qwen API via LlamaIndex with asynchronous streaming
    4. Processes and prints the streaming response in real-time
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Create the chat message as a dictionary
    messages = [{'role': 'user', 'content': 'Apa ibu kota Indonesia?'}]

    # Alternative format using ChatMessage class (commented out)
    # messages = [ChatMessage(role="user", content="Apa ibu kota Indonesia?")]

    print(messages)

    # Send the request to the Qwen API via LlamaIndex with asynchronous streaming
    response = await llm.astream_chat(messages=messages)

    # Process and print the streaming response in real-time
    async for chunk in response:
        print(chunk.delta, end="", flush=True)

if __name__ == "__main__":
    # Run the async main function
    import asyncio
    asyncio.run(main())
