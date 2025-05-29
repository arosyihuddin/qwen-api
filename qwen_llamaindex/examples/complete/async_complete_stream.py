"""
Qwen LlamaIndex Asynchronous Streaming Completion Example

This script demonstrates using Qwen with LlamaIndex for asynchronous streaming text completion tasks.
"""

from qwen_llamaindex import QwenLlamaIndex


async def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for asynchronous streaming text completion.

    1. Creates a QwenLlamaIndex instance
    2. Sends an asynchronous streaming completion request asking about the capital of Indonesia
    3. Processes and prints the streaming response in real-time
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Send an asynchronous streaming completion request
    response = await llm.astream_complete("Apa ibu kota Indonesia?")

    # Process and print the streaming response in real-time
    async for chunk in response:
        print(chunk.delta, end="", flush=True)

if __name__ == "__main__":
    # Run the async main function
    import asyncio
    asyncio.run(main())
