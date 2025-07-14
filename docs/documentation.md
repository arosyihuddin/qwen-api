# Qwen API Python SDK Documentation

This documentation provides a comprehensive guide for using the `Qwen API` Python SDK. The SDK includes classes and methods to interact with the Qwen service for sending messages, receiving responses, handling synchronous or asynchronous interactions, file uploads, and tool usage.

## Getting Started

### Installation

To install the Qwen API Python SDK, use pip:

```bash
pip install qwen-api
```

For LlamaIndex integration, install the additional package:

```bash
pip install qwen-llamaindex
```

### Setup and Authentication

Before using the library, you need to set up your authentication credentials. You can obtain these from [https://chat.qwen.ai](https://chat.qwen.ai). You can set up your credentials in two ways:

1. **Using environment variables (recommended)** - Create a `.env` file in your project root:

```env
QWEN_AUTH_TOKEN=eyJhbGcxxxxx
QWEN_COOKIE="cna=lypxxxx; _bl_uid=atmxxx; cnaui=83axxx; aui=83a0xx; sca=9faxxx; token=eyJhbxxx; acw_tc=0a03exxx;..."
```

2. **Setting them directly in your code:**

```python
from qwen_api.client import Qwen

client = Qwen(api_key="your_token", cookie="your_cookie")
```

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
```

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

### Error Handling

The SDK provides comprehensive error handling capabilities through custom exceptions defined in `qwen_api.core.exceptions`. Here's how to handle errors effectively:

**Basic Error Handling**

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

**Retry Logic with Exponential Backoff**

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

### File Upload Tutorial

The Qwen API supports file uploads, including image files. Here's how to upload and use files:

**Basic File Upload**

```python
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock

def main():
    client = Qwen(log_level="DEBUG")

    try:
        # Upload an image file
        file_result = client.chat.upload_file(
            file_path="/path/to/your/image.png"
        )

        # Create a chat message with both text and image content
        messages = [ChatMessage(
            role="user",
            web_search=False,
            thinking=False,
            blocks=[
                TextBlock(
                    block_type="text",
                    text="What do you see in this image?"
                ),
                ImageBlock(
                    block_type="image",
                    url=file_result.file_url,
                    image_mimetype=file_result.image_mimetype
                )
            ]
        )]

        # Send the request with streaming
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True
        )

        # Process streaming response
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
```

**Upload with Base64 Data**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
import base64

def upload_base64_image():
    client = Qwen()

    # Read and encode image as base64
    with open("/path/to/your/image.png", "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Upload using base64 data
    file_result = client.chat.upload_file(base64_data=base64_data)

    # Use the uploaded file in a chat message
    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        blocks=[
            TextBlock(block_type="text", text="Describe this image"),
            ImageBlock(
                block_type="image",
                url=file_result.file_url,
                image_mimetype=file_result.image_mimetype
            )
        ]
    )]

    response = client.chat.create(messages=messages, model="qwen-max-latest")
    print(response.choices.message.content)
```

**Async File Upload**

```python
import asyncio
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock

async def async_upload_example():
    client = Qwen()

    # Upload file asynchronously
    file_result = await client.chat.async_upload_file(
        file_path="/path/to/your/image.png"
    )

    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        blocks=[
            TextBlock(block_type="text", text="What's in this image?"),
            ImageBlock(
                block_type="image",
                url=file_result.file_url,
                image_mimetype=file_result.image_mimetype
            )
        ]
    )]

    # Send async request with streaming
    response = await client.chat.acreate(
        messages=messages,
        model="qwen-max-latest",
        stream=True
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

# Run async function
asyncio.run(async_upload_example())
```

### Tools Usage

The Qwen API supports function calling through tools. Here's how to use tools:

**Basic Tool Usage**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def calculator_tool_example():
    client = Qwen()

    # Define a calculator tool
    calculator_tool = {
        'type': 'function',
        'function': {
            'name': 'calculator',
            'description': 'Useful for getting the result of a math expression. The input should be a valid mathematical expression.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'input': {'type': 'string'}
                },
                'additionalProperties': False,
                '$schema': 'http://json-schema.org/draft-07/schema#'
            }
        }
    }

    # Create a message that requires calculation
    messages = [ChatMessage(
        role="user",
        content="What is 15 + 27?",
        web_search=False,
        thinking=False
    )]

    # Send request with tools
    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        tools=[calculator_tool]
    )

    print(response.choices.message.content)

calculator_tool_example()
```

**Multiple Tools Example**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def multiple_tools_example():
    client = Qwen()

    # Define multiple tools
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'calculator',
                'description': 'Perform mathematical calculations',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'expression': {'type': 'string'}
                    },
                    'required': ['expression']
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'weather',
                'description': 'Get weather information for a location',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {'type': 'string'},
                        'unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
                    },
                    'required': ['location']
                }
            }
        }
    ]

    messages = [ChatMessage(
        role="user",
        content="Calculate 5 * 8 and then tell me the weather in Jakarta",
        web_search=False,
        thinking=False
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest",
        tools=tools
    )

    print(response.choices.message.content)

multiple_tools_example()
```

### Advanced Features

**Web Search Integration**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def web_search_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content="What's the latest news about AI developments?",
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
        # Check for web search information
        if hasattr(delta, 'extra') and delta.extra and 'web_search_info' in delta.extra:
            print(f"\nWeb search results: {delta.extra.web_search_info}")
            print()

        if delta.content:
            print(delta.content, end="", flush=True)

web_search_example()
```

**Thinking Mode**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

def thinking_mode_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content="Solve this complex problem step by step: How would you design a distributed system for handling 1 million concurrent users?",
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

**Web Development Mode**

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock

def web_dev_example():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        web_search=False,
        thinking=False,
        web_development=True,  # Enable web development mode
        blocks=[
            TextBlock(
                block_type="text",
                text="Create a responsive navigation bar with HTML and CSS"
            )
        ]
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

web_dev_example()
```

## Table of Contents

1. [Qwen Class](#qwen-class)
   - [Constructor](#constructor)
   - [Methods](#methods)
2. [Completion Class](#completion-class)
   - [Methods](#methods-1)
3. [QwenLlamaIndex Class](#qwenllamaindex-class)
   - [Constructor](#constructor-1)
   - [Methods](#methods-2)
4. [Exception Handling](#exception-handling)
5. [Usage Example](#usage-example)

---

## Qwen Class

The `Qwen` class is the main client for interacting with the Qwen API. It handles authentication, request processing, and response management for both synchronous and asynchronous operations.

### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    cookie: Optional[str] = None,
    base_url: str = "https://chat.qwen.ai",
    timeout: int = 600,
    log_level: str = "INFO",
    save_logs: bool = False,
)
```

#### Parameters:

- `api_key` (Optional[str]): Your API key for authentication. If not provided, will be read from environment variable `QWEN_AUTH_TOKEN`.
- `cookie` (Optional[str]): Cookie string for authentication. If not provided, will be read from environment variable `QWEN_COOKIE`.
- `base_url` (str): The base URL for the Qwen API (default: "https://chat.qwen.ai").
- `timeout` (int): Request timeout in seconds (default: 600).
- `log_level` (str): Logging level (default: "INFO"). Options: "DEBUG", "INFO", "WARNING", "ERROR".
- `save_logs` (bool): Whether to save logs to file (default: False).

#### Properties:

- `chat`: Instance of `Completion` class for chat operations.
- `timeout`: Request timeout value.
- `auth`: Authentication manager instance.
- `logger`: Logger instance.
- `base_url`: Base URL for API requests.

### Methods

#### Private Methods

#### 1. `_build_headers(self) -> dict`

- **Returns**: A dictionary containing headers for API requests, including authorization, cookie, and user-agent.

#### 2. `_build_payload(self, messages: List[ChatMessage], temperature: float, model: str, max_tokens: Optional[int]) -> dict`

- **Parameters**:
  - `messages`: List of `ChatMessage` objects representing the conversation.
  - `temperature`: Model creativity level (0.0 to 1.0).
  - `model`: Model name to use.
  - `max_tokens`: Maximum number of tokens in response.
- **Returns**: Dictionary payload for API requests.

#### 3. `_process_response(self, response: requests.Response) -> ChatResponse`

- **Parameters**:
  - `response`: HTTP response from the API.
- **Returns**: Processed `ChatResponse` object.

#### 4. `_process_aresponse(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse`

- **Parameters**:
  - `response`: Async HTTP response from the API.
  - `session`: aiohttp client session.
- **Returns**: Asynchronously processed `ChatResponse` object.

#### 5. `_process_stream(self, response: requests.Response) -> Generator[ChatResponseStream, None, None]`

- **Parameters**:
  - `response`: HTTP response from the API.
- **Returns**: Generator yielding `ChatResponseStream` objects for real-time streaming.

#### 6. `_process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatResponseStream, None]`

- **Parameters**:
  - `response`: Async HTTP response from the API.
  - `session`: aiohttp client session.
- **Returns**: Async generator yielding `ChatResponseStream` objects for real-time streaming.

---

## Completion Class

The `Completion` class handles chat operations including message creation, file uploads, and tool usage. It's accessed through the `chat` property of the `Qwen` client.

### Constructor

```python
def __init__(self, client)
```

#### Parameters:

- `client`: An instance of the `Qwen` class.

### Methods

#### 1. `create(self, messages: List[ChatMessage], model: ChatModel = 'qwen-max-latest', stream: bool = False, temperature: float = 0.7, max_tokens: Optional[int] = 2048, tools: Optional[Iterable[ToolParam]] = None) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]`

- **Parameters**:
  - `messages`: List of `ChatMessage` objects representing the conversation.
  - `model`: Model name to use (default: "qwen-max-latest").
  - `stream`: Whether to stream the response (default: False).
  - `temperature`: Model creativity level from 0.0 to 1.0 (default: 0.7).
  - `max_tokens`: Maximum number of tokens in response (default: 2048).
  - `tools`: Optional list of tools/functions for the model to use.
- **Returns**: Either a `ChatResponse` object or a generator of `ChatResponseStream` objects.

#### 2. `acreate(self, messages: List[ChatMessage], model: ChatModel = 'qwen-max-latest', stream: bool = False, temperature: float = 0.7, max_tokens: Optional[int] = 2048, tools: Optional[Iterable[ToolParam]] = None) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]`

- **Parameters**: Same as `create` method.
- **Returns**: Asynchronous version returning either a `ChatResponse` object or async generator of `ChatResponseStream` objects.

#### 3. `upload_file(self, file_path: str = None, base64_data: str = None) -> FileResult`

- **Parameters**:
  - `file_path`: Path to the file to upload.
  - `base64_data`: Base64 encoded file data (alternative to file_path).
- **Returns**: `FileResult` object containing the uploaded file URL and metadata.
- **Note**: Either `file_path` or `base64_data` must be provided.

#### 4. `async_upload_file(self, file_path: str = None, base64_data: str = None) -> FileResult`

- **Parameters**: Same as `upload_file`.
- **Returns**: Asynchronous version returning `FileResult` object.

### Supported Chat Message Features

The `ChatMessage` class supports several advanced features:

- **Basic text messages**: Simple text content
- **Block-based messages**: Using `TextBlock` and `ImageBlock` for rich content
- **Web search**: Set `web_search=True` to enable web search capabilities
- **Thinking mode**: Set `thinking=True` to enable step-by-step reasoning
- **Web development mode**: Set `web_development=True` for web development assistance
- **Tool usage**: Provide tools parameter for function calling

---

## QwenLlamaIndex Class

The `QwenLlamaIndex` class integrates the Qwen API with LlamaIndex framework, providing a seamless way to use Qwen models within LlamaIndex applications. This class extends the LlamaIndex `LLM` base class.

### Constructor

```python
def __init__(
    self,
    auth_token: Optional[str] = None,
    cookie: Optional[str] = None,
    model: str = 'qwen-max-latest',
    temperature: float = 0.7,
    max_tokens: Optional[int] = 1500,
    context_window: int = 6144,
    **kwargs: Any
)
```

#### Parameters:

- `auth_token` (Optional[str]): Your API token for authentication.
- `cookie` (Optional[str]): Your authentication cookie.
- `model` (str): The model to use for chat (default: "qwen-max-latest").
- `temperature` (float): Model creativity level (default: 0.7).
- `max_tokens` (Optional[int]): Maximum number of tokens in response (default: 1500).
- `context_window` (int): Context window size (default: 6144).
- `**kwargs`: Additional keyword arguments.

### Properties

- `context_window`: Size of the model's context window
- `is_chat_model`: Always True for Qwen models
- `supports_function_calling`: Always True for Qwen models

### Methods

#### 1. `chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse`

- **Parameters**:
  - `messages`: Sequence of LlamaIndex `ChatMessage` objects.
  - `**kwargs`: Additional keyword arguments.
- **Returns**: LlamaIndex `ChatResponse` object.

#### 2. `stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen`

- **Parameters**: Same as `chat` method.
- **Returns**: Generator yielding LlamaIndex `ChatResponse` objects for streaming.

#### 3. `complete(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**:
  - `prompt`: The input prompt for completion.
  - `**kwargs`: Additional keyword arguments.
- **Returns**: LlamaIndex `CompletionResponse` object.

#### 4. `stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen`

- **Parameters**: Same as `complete` method.
- **Returns**: Generator yielding LlamaIndex `CompletionResponse` objects for streaming.

#### 5. `achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse`

- **Parameters**: Same as `chat` method.
- **Returns**: Asynchronously processed LlamaIndex `ChatResponse` object.

#### 6. `astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseAsyncGen`

- **Parameters**: Same as `chat` method.
- **Returns**: Async generator yielding LlamaIndex `ChatResponse` objects.

#### 7. `acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**: Same as `complete` method.
- **Returns**: Asynchronously processed LlamaIndex `CompletionResponse` object.

#### 8. `astream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseAsyncGen`

- **Parameters**: Same as `complete` method.
- **Returns**: Async generator yielding LlamaIndex `CompletionResponse` objects.

### Usage Example with LlamaIndex

```python
from qwen_llamaindex import QwenLlamaIndex
from llama_index.core.base.llms.types import ChatMessage, MessageRole

# Initialize the LlamaIndex integration
llm = QwenLlamaIndex(
    auth_token="your_token",
    cookie="your_cookie",
    model="qwen-max-latest",
    temperature=0.7
)

# Use with LlamaIndex ChatMessage format
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
response = llm.complete("Write a poem about AI")
print(response.text)

# Async usage
import asyncio

async def async_example():
    response = await llm.achat(messages)
    print(response.message.content)

asyncio.run(async_example())
```

---

## Exception Handling

The Qwen API SDK provides a structured error handling system through custom exceptions defined in `qwen_api.core.exceptions`:

### Exception Hierarchy

- **QwenAPIError**: Base class for all API-related errors
  - **AuthError**: Raised when authentication fails
  - **RateLimitError**: Raised when the API rate limit is exceeded

### Exception Details

Each exception provides information about what went wrong:

```python
from qwen_api.core.exceptions import QwenAPIError, AuthError, RateLimitError

try:
    # Your API call here
    pass
except AuthError as e:
    print(f"Authentication failed: {e}")
    # Handle authentication error - check credentials
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Handle rate limiting - implement backoff
except QwenAPIError as e:
    print(f"General API error: {e}")
    # Handle other API errors
```

### Common Error Scenarios

1. **Authentication Errors**: Invalid or expired tokens/cookies
2. **Rate Limiting**: Too many requests in a short time period
3. **Network Errors**: Connection issues or timeouts
4. **Invalid Requests**: Malformed request data or unsupported operations

---

## Usage Example

Here is a comprehensive example demonstrating how to use the `Qwen` class with various features:

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock
from qwen_api.core.exceptions import QwenAPIError, AuthError, RateLimitError

def comprehensive_example():
    # Initialize the Qwen client
    client = Qwen(log_level="INFO")

    try:
        # Example 1: Basic text chat
        print("=== Basic Text Chat ===")
        messages = [ChatMessage(
            role="user",
            content="What is the capital of Indonesia?",
            web_search=False,
            thinking=False
        )]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest"
        )
        print(f"Response: {response.choices.message.content}")

        # Example 2: Web search enabled
        print("\n=== Web Search Example ===")
        messages = [ChatMessage(
            role="user",
            content="What's the latest news about climate change?",
            web_search=True,
            thinking=False
        )]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

        # Example 3: Tool usage
        print("\n\n=== Tool Usage Example ===")
        calculator_tool = {
            'type': 'function',
            'function': {
                'name': 'calculator',
                'description': 'Perform mathematical calculations',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'expression': {'type': 'string'}
                    },
                    'required': ['expression']
                }
            }
        }

        messages = [ChatMessage(
            role="user",
            content="Calculate 25 * 4 + 10",
            web_search=False,
            thinking=False
        )]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            tools=[calculator_tool]
        )
        print(f"Tool response: {response.choices.message.content}")

        # Example 4: File upload and image analysis
        print("\n=== File Upload Example ===")
        # Upload an image file
        file_result = client.chat.upload_file(
            file_path="/path/to/your/image.jpg"
        )

        # Create message with both text and image
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

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest"
        )
        print(f"Image analysis: {response.choices.message.content}")

    except AuthError as e:
        print(f"Authentication error: {e}")
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
    except QwenAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    comprehensive_example()
```

## Installation

To use the Qwen API Python SDK, install the required dependencies:

```bash
# Install main package
pip install qwen-api

# Install LlamaIndex integration (optional)
pip install qwen-llamaindex
```

## Project Structure

This SDK consists of two main packages:

1. **qwen-api**: Core SDK for direct API interaction
2. **qwen-llamaindex**: LlamaIndex integration for seamless use with LlamaIndex applications

Both packages are available on PyPI and can be installed independently or together.
