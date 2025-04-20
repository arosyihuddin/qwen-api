Below is the complete documentation in Markdown format (`.md`).

---

````markdown
# Qwen API Python SDK Documentation

This documentation provides a guide for using the `Qwen API` Python SDK. The SDK includes classes and methods to interact with the Qwen service for sending messages, receiving responses, and handling synchronous or asynchronous interactions.

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
````

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

## Exception Handling

The Qwen API SDK also handles the following exceptions:

- **QwenAPIError**: Raised when there is an error with the API.
- **RateLimitError**: Raised when the API rate limit is exceeded.

---

## Usage Example

Here is an example usage of the `Qwen` class to send a message and receive a response:

```python
from qwen_api import Qwen
from qwen_api.types.chat import ChatMessage

# Initialize the Qwen client
client = Qwen(api_key="your_api_key")

# Example of creating a chat response
messages = [ChatMessage(role="user", content="Apa ibu kota Indonesia?")]
response = client.chat.create(messages=messages)

# Print the response
print(response)
```

---

## Installation

To use the Qwen API Python SDK, you need to install the required dependencies:

```bash
pip install qwen_api
```

---

This documentation should guide you through using the provided Python classes for interacting with the Qwen API. Let me know if you need any further clarification or additional examples!

```

```
