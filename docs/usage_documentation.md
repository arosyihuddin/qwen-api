# qwen-api Library Usage Documentation

## Installation

To install the qwen-api library, use pip:

```bash
pip install qwen-api
```

For development with Poetry:

```bash
poetry add oss2
```

## Setup and Authentication

To use the Qwen API, you need to obtain your authentication credentials from [https://chat.qwen.ai](https://chat.qwen.ai). You can set up your credentials in two ways:

1. **Using a `.env` file**  
   Create a `.env` file in your project root with these variables:

   ```env
   QWEN_AUTH_TOKEN=your_token_here  # No "Bearer" prefix
   QWEN_COOKIE="your_cookie_value"
   ```

2. **Setting in code**  
   Alternatively, set them directly in your code:

   ```python
   from qwen_api.client import Qwen

   client = Qwen()
   ```

````

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
````

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

## Streaming vs Non-Streaming

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

## Error Handling Best Practices

### Basic Error Handling

The SDK provides comprehensive error handling capabilities through custom exceptions defined in `qwen_api.core.exceptions`. Here's how to handle errors effectively:

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

### Retry Logic

Here's an example of implementing retry logic with exponential backoff:

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

### Rate Limit Handling

Here's how to handle rate limiting with intelligent backoff:

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
