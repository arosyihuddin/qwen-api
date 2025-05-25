"""
Qwen LlamaIndex Asynchronous Completion Example

This script demonstrates using Qwen with LlamaIndex for asynchronous text completion tasks.
"""

from qwen_api.llama_index import QwenLlamaIndex


async def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for asynchronous text completion.

    1. Creates a QwenLlamaIndex instance
    2. Sends an asynchronous completion request asking about the capital of Indonesia
    3. Prints the response
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Send an asynchronous completion request
    response = await llm.acomplete("Apa ibu kota Indonesia?")

    # Print the response from the API
    print(response.text)

if __name__ == "__main__":
    # Run the async main function
    import asyncio
    asyncio.run(main())
