"""
Qwen LlamaIndex Streaming Completion Example

This script demonstrates using Qwen with LlamaIndex for streaming text completion tasks.
"""

from qwen_llamaindex import QwenLlamaIndex


def main():
    """
    Main function that demonstrates using Qwen with LlamaIndex for streaming text completion.

    1. Creates a QwenLlamaIndex instance
    2. Sends a streaming completion request asking about the capital of Indonesia
    3. Processes and prints the streaming response in real-time
    """
    # Initialize the QwenLlamaIndex instance
    llm = QwenLlamaIndex()

    # Send a streaming completion request
    response = llm.stream_complete("Apa ibu kota Indonesia?")

    # Process and print the streaming response in real-time
    for chunk in response:
        print(chunk.delta, end="", flush=True)


if __name__ == "__main__":
    main()
