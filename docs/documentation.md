# Qwen API Python SDK Documentation

This documentation provides a guide for using the `Qwen API` Python SDK. The SDK includes classes and methods to interact with the Qwen service for sending messages, receiving responses, and handling synchronous or asynchronous interactions.

## Getting Started

### Installation

To install the Qwen API Python SDK, use pip:

```bash
pip install qwen-api
```

### Setup and Authentication

Before using the library, you need to set up your authentication credentials. You can do this by either:

1. Creating a `.env` file in your project root with the following variables:

```python
QWEN_AUTH_TOKEN=eyJhbGcxxxxx
QWEN_COOKIE="cna=lypxxxx; _bl_uid=atmxxx; cnaui=83axxx; aui=83a0xx; sca=9faxxx; token=eyJhbxxx; acw_tc=0a03exxx;..."
```

2. Or setting them directly in your code:

```python
from qwen_api.client import Qwen

client = Qwen()
```

## Basic Usage Patterns

### Synchronous Usage

Here's an example of basic synchronous usage:

```python
from qwen_api.client import Qwen

# Create a client instance
client = Qwen()

# Make a basic completion request
response = client.completion.create(
    model="qwen-max",
    prompt="Hello, how can I help you today?"
)

# Print the response
print(response.choices[0].text)
```

### Asynchronous Usage

For asynchronous operations, you can use the async methods:

```python
import asyncio
from qwen_api.client import Qwen

async def main():
    # Create an async client instance
    client = Qwen()

    # Make an async completion request
    response = await client.completion.acreate(
        model="qwen-max",
        prompt="Hello, how can I help you today?"
    )

    # Print the response
    print(response.choices[0].text)

# Run the async function
asyncio.run(main())
```

### Streaming Implementation

Streaming allows you to process the response as it's being generated:

```python
from qwen_api.client import Qwen

client = Qwen()

# Create a streaming completion
stream = client.completion.create(
    model="qwen-max",
    prompt="Write a long story about a magical forest",
    stream=True
)

# Process the stream
for chunk in stream:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

### Non-Streaming Implementation

Non-streaming waits for the complete response before returning:

```python
from qwen_api.client import Qwen

client = Qwen()

# Create a non-streaming completion
response = client.completion.create(
    model="qwen-max",
    prompt="Write a short poem about springtime"
)

# Process the complete response
print(response.choices[0].text)
```

### Error Handling

The SDK provides comprehensive error handling capabilities through custom exceptions defined in `qwen_api.core.exceptions`. Here's how to handle errors effectively:

**Basic Error Handling**

```python
from qwen_api.client import Qwen
from qwen_api.core.exceptions import QwenAPIError

try:
    client = Qwen()
    response = client.completion.create(
        model="qwen-max",
        prompt="This is a test request"
    )
except QwenAPIError as e:
    print(f"An API error occurred: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response body: {e.body}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

**Retry Logic with Exponential Backoff**

```python
import time
from qwen_api.client import Qwen
from qwen_api.core.exceptions import QwenAPIError

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1

for attempt in range(MAX_RETRIES):
    try:
        client = Qwen()
        response = client.completion.create(
            model="qwen-max",
            prompt="This is a test request"
        )
        break  # Success, exit retry loop
    except QwenAPIError as e:
        if attempt < MAX_RETRIES - 1:
            retry_delay = INITIAL_RETRY_DELAY * (attempt + 1)
            print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"All attempts failed. Final error: {e}")
```

**Rate Limit Handling**

```python
import time
from qwen_api.client import Qwen
from qwen_api.core.exceptions import QwenAPIError

for attempt in range(MAX_RETRIES):
    try:
        client = Qwen()
        response = client.completion.create(
            model="qwen-max",
            prompt="This is a test request"
        )
        break
    except QwenAPIError as e:
        if e.status_code == 429:  # Rate limit exceeded
            retry_after = getattr(e, 'retry_after', INITIAL_RETRY_DELAY * (attempt + 1))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
        elif attempt < MAX_RETRIES - 1:
            print(f"Attempt {attempt + 1} failed. Retrying...")
            time.sleep(INITIAL_RETRY_DELAY * (attempt + 1))
        else:
            print(f"Final error: {e}")
```

### File Upload Tutorial

The Qwen API also supports file uploads, including image files. Here's an example from the basic_usage_stream.py file:

```python
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock


def main():
    client = Qwen(logging_level="DEBUG")

    try:
        getUrl = client.chat.upload_file(
            file_path="/home/pstar7/Documents/Personal/Open Source Project/qwen-api/examples/tes_image.png"
        )
        messages = [ChatMessage(
            role="user",
            web_search=False,
            thinking=False,
            blocks=[
                TextBlock(
                    block_type="text",
                    text="ini gambar apa?"
                ),
                ImageBlock(
                    block_type="image",
                    url=getUrl.file_url,
                    image_mimetype="image/jpeg"
                )
            ]
        )]

        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if 'extra' in delta and 'web_search_info' in delta.extra:
                print("\nHasil pencarian:", delta.extra.web_search_info)
                print()

            print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
```

This example shows how to upload an image file and include it in a chat request. The process involves:

1. Uploading the file using `upload_file`
2. Creating a chat message with both text and image content
3. Using the `create` method with `stream=True` to get a streaming response

For more detailed examples of specific use cases, please refer to the README in the examples folder.

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

The `Qwen` class is designed to handle API calls to the Qwen service, including message sending, response processing, and error handling. It supports both synchronous and asynchronous chat interactions.

### Constructor

```python
def __init__(self, api_key: Optional[str] = None, cookie: Optional[str] = None, timeout: int = 30, logging_level: str = "INFO", save_logs: bool = False)
```

#### Parameters:

- `api_key` (Optional): Your API key for authentication.
- `cookie` (Optional): Cookie for authentication.
- `timeout`: The timeout for API requests (default: 30 seconds).
- `logging_level`: Logging level (default: `'INFO'`).
- `save_logs`: Boolean flag to save logs (default: `False`).

#### Description:

- Initializes the `Qwen` object with the specified authentication parameters, timeout, and logging settings.

---

### Methods

#### 1. `_build_headers(self) -> dict`

- **Returns**: A dictionary containing headers for the API request, including authorization and cookie details.

#### 2. `_build_payload(self, messages: List[ChatMessage], temperature: float, model: str, max_tokens: Optional[int]) -> dict`

- **Parameters**:
  - `messages`: A list of `ChatMessage` objects representing the conversation.
  - `temperature`: The creativity of the model (default is 0.7).
  - `model`: The model to use (default is `"qwen-max-latest"`).
  - `max_tokens`: The maximum number of tokens for the response.
- **Returns**: A dictionary payload that can be sent in a request to the API.

#### 3. `_process_response(self, response: requests.Response) -> ChatResponse`

- **Parameters**:
  - `response`: The HTTP response from the API.
- **Returns**: A `ChatResponse` object containing the processed response from the API.

#### 4. `_process_aresponse(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse`

- **Parameters**:
  - `response`: The asynchronous HTTP response from the API.
  - `session`: The aiohttp client session.
- **Returns**: A `ChatResponse` object asynchronously processed from the API.

#### 5. `_process_stream(self, response: requests.Response) -> Generator[ChatResponseStream, None, None]`

- **Parameters**:
  - `response`: The HTTP response from the API.
- **Returns**: A generator that yields `ChatResponseStream` objects in real-time as they are streamed from the API.

#### 6. `_process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatResponseStream, None]`

- **Parameters**:
  - `response`: The asynchronous HTTP response from the API.
  - `session`: The aiohttp client session.
- **Returns**: An asynchronous generator that yields `ChatResponseStream` objects in real-time.

---

## Completion Class

The `Completion` class is used to handle the creation of messages and completion responses from the Qwen API.

### Constructor

```python
def __init__(self, client)
```

#### Parameters:

- `client`: An instance of the `Qwen` class.

---

### Methods

#### 1. `create(self, messages: List[ChatMessage], model: ChatModel = 'qwen-max-latest', stream: bool = False, temperature: float = 0.7, max_tokens: Optional[int] = 2048) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]`

- **Parameters**:
  - `messages`: A list of `ChatMessage` objects representing the conversation.
  - `model`: The model to use (default is `"qwen-max-latest"`).
  - `stream`: Whether to stream the response (default is `False`).
  - `temperature`: The creativity of the model (default is 0.7).
  - `max_tokens`: The maximum number of tokens for the response.
- **Returns**: Either a `ChatResponse` object or a generator of `ChatResponseStream` objects depending on whether streaming is enabled.

#### 2. `acreate(self, messages: List[ChatMessage], model: ChatModel = 'qwen-max-latest', stream: bool = False, temperature: float = 0.7, max_tokens: Optional[int] = 2048) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]`

- **Parameters**: Same as the `create` method but asynchronously processed.
- **Returns**: Either a `ChatResponse` object or an asynchronous generator of `ChatResponseStream` objects depending on whether streaming is enabled.

---

## QwenLlamaIndex Class

The `QwenLlamaIndex` class integrates the Qwen API with the Llama Index, enabling more complex interactions and handling of responses.

### Constructor

```python
def __init__(self, auth_token: Optional[str] = None, cookie: Optional[str] = None, model: str = 'qwen-max-latest', temperature: float = 0.7, max_tokens: Optional[int] = 1500, **kwargs: Any)
```

#### Parameters:

- `auth_token`: Your API token for authentication.
- `cookie`: Your authentication cookie.
- `model`: The model to use for chat (default: `"qwen-max-latest"`).
- `temperature`: The creativity of the model (default is 0.7).
- `max_tokens`: The maximum number of tokens for the response (default is 1500).

#### Description:

- Initializes the `QwenLlamaIndex` class, allowing you to interact with the Qwen API using the Llama Index framework.

---

### Methods

#### 1. `chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse`

- **Parameters**:
  - `messages`: A sequence of `ChatMessage` objects.
- **Returns**: A `ChatResponse` object containing the response from the API.

#### 2. `stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse`

- **Parameters**: Same as `chat`, but returns a stream of responses.
- **Returns**: A generator yielding `ChatResponseStream` objects.

#### 3. `complete(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**:
  - `prompt`: The input message for the completion.
- **Returns**: A `CompletionResponse` object containing the completion result.

#### 4. `stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**: Same as `complete`, but returns a stream of completions.

- **Returns**: A generator yielding `CompletionResponse` objects.

#### 5. `acreate(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**: Same as `complete`, but asynchronously processed.

- **Returns**: A `CompletionResponse` object asynchronously processed.

#### 6. `astream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponse`

- **Parameters**: Same as `stream_complete`, but asynchronously processed.

- **Returns**: An asynchronous generator yielding `CompletionResponse` objects.

---

## Error Handling

The Qwen API SDK provides robust error handling through a hierarchy of exception classes:

- **QwenAPIError**: Base class for all API-related errors
  - **QwenAPIStatusError**: Base class for HTTP status code errors
    - **QwenAPIStatus4xxError**: Base class for client-side errors (400-499)
      - **QwenAuthenticationError**: Raised when authentication fails
      - **QwenInvalidRequestError**: Raised when the request is invalid
    - **QwenAPIStatus5xxError**: Base class for server-side errors (500-599)
  - **QwenConnectionError**: Raised when there's a network connection issue
  - **QwenTimeoutError**: Raised when a request times out
  - **RateLimitError**: Raised when the API rate limit is exceeded
  - **QwenInternalError**: Raised when there's an internal SDK error

Each error includes detailed information about what went wrong, including:

- HTTP status code
- Response headers and body
- Request details
- Timestamps

---

## Usage Example

Here is a practical example demonstrating how to use the `Qwen` class to send a message and process the response:

```python
from qwen_api import Qwen
from qwen_api.types.chat import ChatMessage

# Initialize the Qwen client with API credentials
client = Qwen(api_key="your_api_key")

# Create a chat message from the user
messages = [ChatMessage(
    role="user",
    content="What is the capital of Indonesia?"
)]

# Get a response from the API
try:
    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )
    # Print the successful response
    print("Model response:", response.choices[0].message.content)

except QwenAPIError as e:
    print(f"API error occurred: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Error details: {e.body}")
```

---

## Installation

To use the Qwen API Python SDK, you need to install the required dependencies:

```bash
pip install qwen_api
```

---

This documentation should guide you through using the provided Python classes for interacting with the Qwen API. Let me know if you need any further clarification or additional examples!
