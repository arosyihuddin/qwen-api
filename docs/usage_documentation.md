# qwen-api Library Usage Documentation

## Installation

To install the qwen-api library, use pip:

```bash
pip install qwen-api
```

For LlamaIndex integration:

```bash
pip install qwen-llamaindex
```

## Setup and Authentication

To use the Qwen API, you need to obtain your authentication credentials from [https://chat.qwen.ai](https://chat.qwen.ai). You can set up your credentials in two ways:

1. **Using environment variables (recommended)**  
   Create a `.env` file in your project root with these variables:

   ```env
   QWEN_AUTH_TOKEN=your_token_here
   QWEN_COOKIE="your_cookie_value"
   ```

2. **Setting in code**  
   Alternatively, set them directly in your code:

   ```python
   from qwen_api.client import Qwen

   client = Qwen(api_key="your_token", cookie="your_cookie")
   ```

````

## Basic Usage Patterns

### Synchronous Usage

Here's an example of basic synchronous usage:

```python
from qwen_api.client import Qwen
from qwen_api.core.types.chat import ChatMessage

# Create a client instance
client = Qwen()

# Create a chat message
messages = [ChatMessage(
    role="user",
    content="Hello, how can I help you today?",
    web_search=False,
    thinking=False
)]

# Make a basic chat request
response = client.chat.create(
    messages=messages,
    model="qwen-max-latest"
)

# Print the response
print(response.choices.message.content)
````

### Asynchronous Usage

For asynchronous operations, you can use the async methods:

```python
import asyncio
from qwen_api.client import Qwen
from qwen_api.core.types.chat import ChatMessage

async def main():
    # Create an async client instance
    client = Qwen()

    # Create a chat message
    messages = [ChatMessage(
        role="user",
        content="Hello, how can I help you today?",
        web_search=False,
        thinking=False
    )]

    # Make an async chat request
    response = await client.chat.acreate(
        messages=messages,
        model="qwen-max-latest"
    )

    # Print the response
    print(response.choices.message.content)

# Run the async function
asyncio.run(main())
```

## Streaming vs Non-Streaming

### Streaming Implementation

Streaming allows you to process the response as it's being generated:

```python
from qwen_api.client import Qwen
from qwen_api.core.types.chat import ChatMessage

client = Qwen()

# Create a chat message
messages = [ChatMessage(
    role="user",
    content="Write a long story about a magical forest",
    web_search=False,
    thinking=False
)]

# Create a streaming chat request
stream = client.chat.create(
    messages=messages,
    model="qwen-max-latest",
    stream=True
)

# Process the stream
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Non-Streaming Implementation

Non-streaming waits for the complete response before returning:

```python
from qwen_api.client import Qwen
from qwen_api.core.types.chat import ChatMessage

client = Qwen()

# Create a chat message
messages = [ChatMessage(
    role="user",
    content="Write a short poem about springtime",
    web_search=False,
    thinking=False
)]

# Create a non-streaming chat request
response = client.chat.create(
    messages=messages,
    model="qwen-max-latest"
)

# Process the complete response
print(response.choices.message.content)
```

## Error Handling Best Practices

### Basic Error Handling

The SDK provides comprehensive error handling capabilities through custom exceptions defined in `qwen_api.core.exceptions`. Here's how to handle errors effectively:

```python
from qwen_api.client import Qwen
from qwen_api.core.exceptions import QwenAPIError, AuthError, RateLimitError
from qwen_api.core.types.chat import ChatMessage

try:
    client = Qwen()
    messages = [ChatMessage(
        role="user",
        content="This is a test request",
        web_search=False,
        thinking=False
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

except AuthError as e:
    print(f"Authentication error: {e}")
except RateLimitError as e:
    print(f"Rate limit error: {e}")
except QwenAPIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

Here's an example of implementing retry logic with exponential backoff:

```python
import time
from qwen_api.client import Qwen
from qwen_api.core.exceptions import QwenAPIError, RateLimitError
from qwen_api.core.types.chat import ChatMessage

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1

def create_chat_with_retry():
    client = Qwen()
    messages = [ChatMessage(
        role="user",
        content="This is a test request",
        web_search=False,
        thinking=False
    )]

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest"
            )
            return response  # Success, return response
        except RateLimitError as e:
            if attempt < MAX_RETRIES - 1:
                retry_delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"All attempts failed due to rate limiting: {e}")
                raise
        except QwenAPIError as e:
            if attempt < MAX_RETRIES - 1:
                retry_delay = INITIAL_RETRY_DELAY * (attempt + 1)
                print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"All attempts failed. Final error: {e}")
                raise
```

## Advanced Features

### File Upload and Image Processing

The Qwen API supports file uploads, particularly useful for image analysis:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock

def upload_and_analyze_image():
    client = Qwen()

    # Upload an image file
    file_result = client.chat.upload_file(
        file_path="/path/to/your/image.jpg"
    )

    # Create a message with both text and image
    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        blocks=[
            TextBlock(block_type="text", text="What do you see in this image?"),
            ImageBlock(
                block_type="image",
                url=file_result.file_url,
                image_mimetype=file_result.image_mimetype
            )
        ]
    )]

    # Get response with streaming
    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

upload_and_analyze_image()
```

### Tool Usage and Function Calling

The SDK supports tools for extended functionality:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def use_tools_example():
    client = Qwen()

    # Define a calculator tool
    calculator_tool = {
        'type': 'function',
        'function': {
            'name': 'calculator',
            'description': 'Perform mathematical calculations',
            'parameters': {
                'type': 'object',
                'properties': {
                    'expression': {'type': 'string', 'description': 'Mathematical expression to calculate'}
                },
                'required': ['expression']
            }
        }
    }

    messages = [ChatMessage(
        role="user",
        content="Calculate 15 * 7 + 23",
        web_search=False,
        thinking=False
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        tools=[calculator_tool]
    )

    print(response.choices.message.content)

use_tools_example()
```

### Web Search Integration

Enable web search for up-to-date information:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def web_search_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content="What are the latest developments in AI technology?",
        web_search=True,  # Enable web search
        thinking=False
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        stream=True
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        # Check for web search results
        if hasattr(delta, 'extra') and delta.extra and 'web_search_info' in delta.extra:
            print(f"\nWeb search results: {delta.extra.web_search_info}")
            print()

        if delta.content:
            print(delta.content, end="", flush=True)

web_search_example()
```

### Thinking Mode for Complex Reasoning

Enable thinking mode for step-by-step reasoning:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def thinking_mode_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content="Explain the process of photosynthesis in detail, including the chemical reactions involved",
        web_search=False,
        thinking=True  # Enable thinking mode
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

thinking_mode_example()
```

### Web Development Mode

Special mode for web development assistance:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock

def web_development_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        web_development=True,  # Enable web development mode
        blocks=[
            TextBlock(
                block_type="text",
                text="Create a responsive navigation bar with HTML, CSS, and JavaScript"
            )
        ]
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

web_development_example()
```

## LlamaIndex Integration

For users of the LlamaIndex framework, use the `qwen-llamaindex` package:

```python
from qwen_llamaindex import QwenLlamaIndex
from llama_index.core.base.llms.types import ChatMessage, MessageRole

# Initialize with LlamaIndex
llm = QwenLlamaIndex(
    model="qwen-max-latest",
    temperature=0.7,
    max_tokens=2000
)

# Use with LlamaIndex chat format
messages = [
    ChatMessage(role=MessageRole.USER, content="Hello, how are you?")
]

# Synchronous chat
response = llm.chat(messages)
print(response.message.content)

# Streaming chat
for chunk in llm.stream_chat(messages):
    print(chunk.message.content, end="")

# Completion
response = llm.complete("Write a poem about technology")
print(response.text)
```

## Configuration Options

### Client Configuration

```python
from qwen_api import Qwen

# Full configuration example
client = Qwen(
    api_key="your_api_key",           # API authentication token
    cookie="your_cookie",             # Authentication cookie
    base_url="https://chat.qwen.ai",  # API base URL
    timeout=600,                      # Request timeout in seconds
    log_level="INFO",                 # Logging level
    save_logs=False                   # Whether to save logs to file
)
```

### Request Parameters

```python
# Available parameters for chat.create()
response = client.chat.create(
    messages=messages,                # List of ChatMessage objects
    model="qwen-max-latest",          # Model to use
    stream=False,                     # Enable streaming
    temperature=0.7,                  # Creativity level (0.0-1.0)
    max_tokens=2048,                  # Maximum response tokens
    tools=None                        # Optional tools for function calling
)
```

## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Rate Limiting**: Implement retry logic with exponential backoff
3. **Streaming**: Use streaming for long responses to improve user experience
4. **Authentication**: Store credentials securely using environment variables
5. **Logging**: Enable appropriate logging levels for debugging
6. **Resource Management**: Close connections properly in async implementations

## Common Use Cases

### 1. Simple Q&A Chatbot

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def simple_chatbot():
    client = Qwen()

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        messages = [ChatMessage(
            role="user",
            content=user_input,
            web_search=False,
            thinking=False
        )]

        try:
            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest"
            )
            print(f"Bot: {response.choices.message.content}")
        except Exception as e:
            print(f"Error: {e}")

# Run the chatbot
simple_chatbot()
```

### 2. Document Analysis with Images

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock

def analyze_document():
    client = Qwen()

    # Upload document image
    file_result = client.chat.upload_file(
        file_path="/path/to/document.jpg"
    )

    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        blocks=[
            TextBlock(block_type="text", text="Extract all text from this document and summarize the key points"),
            ImageBlock(
                block_type="image",
                url=file_result.file_url,
                image_mimetype=file_result.image_mimetype
            )
        ]
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

analyze_document()
```

### 3. Research Assistant with Web Search

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def research_assistant(topic):
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content=f"Research the latest information about {topic} and provide a comprehensive summary",
        web_search=True,  # Enable web search for current information
        thinking=True     # Enable thinking for better analysis
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        stream=True
    )

    print(f"Researching: {topic}")
    print("=" * 50)

    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

# Example usage
research_assistant("artificial intelligence trends 2024")
```

This documentation provides comprehensive guidance for using the qwen-api library effectively. For more examples and advanced usage patterns, refer to the example files in the project repository.
