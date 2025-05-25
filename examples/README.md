# Qwen API Examples

This directory contains various examples demonstrating how to use the Qwen API Python library.

## Table of Contents

1. [Basic Usage](#basic-usage)

   - [Synchronous](#synchronous-basic-usage)
   - [Asynchronous](#asynchronous-basic-usage)
   - [Streaming](#streaming-basic-usage)

2. [Qwen LlamaIndex Integration](#qwen-llamaindex-integration)

   - [Chat Examples](#chat-examples)
   - [Completion Examples](#completion-examples)

3. [File Handling](#file-handling)
   - [Image Upload](#image-upload)

## Basic Usage

### Synchronous Basic Usage

`basic_usage.py` demonstrates a simple synchronous request to the Qwen API to answer a question about the capital of Indonesia.

### Asynchronous Basic Usage

`async_usage.py` shows how to use the Qwen API asynchronously to achieve the same result.

### Streaming Basic Usage

`basic_usage_stream.py` demonstrates streaming responses from the Qwen API, showing how to handle partial results in real-time.

## Qwen LlamaIndex Integration

### Chat Examples

The chat examples demonstrate using Qwen with LlamaIndex for chat-style interactions:

- `chat.py`: Basic synchronous chat example
- `chat_stream.py`: Streaming chat example
- `async_chat.py`: Asynchronous chat example
- `async_chat_stream.py`: Asynchronous streaming chat example

### Completion Examples

The completion examples demonstrate using Qwen with LlamaIndex for text completion tasks:

- `complete.py`: Basic synchronous completion example
- `complete_stream.py`: Streaming completion example
- `async_complete.py`: Asynchronous completion example
- `async_complete_stream.py`: Asynchronous streaming completion example

## File Handling

### Image Upload

Some examples demonstrate image upload functionality using the Qwen API's file handling capabilities.

## Getting Started

To run these examples, you'll need to:

1. Install the library: `pip install qwen-api`
2. Set up your API credentials (either in code or via .env file)
3. Run the example files individually

For more detailed documentation, please refer to the [usage documentation](../docs/usage_documentation.md).
