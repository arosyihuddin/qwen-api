"""
Qwen LlamaIndex Basic Completion Example

This script demonstrates using Qwen with LlamaIndex for basic text completion tasks.
"""

from qwen_api.llama_index import QwenLlamaIndex


def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for basic text completion.

    1. Creates a QwenLlamaIndex instance
    2. Sends a completion request asking about the capital of Indonesia
    3. Prints the response
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Send a completion request
    response = llm.complete("Apa ibu kota Indonesia?")

    # Print the response from the API
    print(response.text)


if __name__ == "__main__":
    main()
