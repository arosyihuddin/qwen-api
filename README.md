# Qwen API Python SDK

[![PyPI version](https://badge.fury.io/py/qwen-api.svg)](https://pypi.org/project/qwen-api/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qwen-api)](https://pypi.org/project/qwen-api/)
[![Downloads](https://static.pepy.tech/badge/qwen-api)](https://pepy.tech/project/qwen-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Unofficial Python SDK for accessing [Qwen AI](https://chat.qwen.ai) API with comprehensive features and seamless integration.

---

## ✨ Features

- **🤖 Multiple Model Support**  
  Supports various Qwen models including: `qwen-max-latest`, `qwen-plus-latest`, `qwq-32b`, `qwen-turbo-latest`, `qwen2.5-omni-7b`, `qvq-72b-preview-0310`, `qwen2.5-vl-32b-instruct`, `qwen2.5-14b-instruct-1m`, `qwen2.5-coder-32b-instruct`, and `qwen2.5-72b-instruct`.

- **⚡ Real-time Streaming**  
  Get token-by-token output in real-time for interactive applications with both sync and async support.

- **🔄 Async & Sync Support**  
  Seamless integration for both synchronous and asynchronous workflows with the same intuitive API.

- **🔍 Web Search Integration**  
  Enhance responses with real-time information using built-in web search capabilities.

- **📁 File Upload Support**  
  Upload and process files including images, documents, and other media types.

- **🛠️ Function Calling (Tools)**  
  Extend functionality with custom tools and function calling capabilities.

- **🧠 Advanced Reasoning Modes**

  - **Thinking Mode**: Step-by-step reasoning for complex problems
  - **Web Development Mode**: Specialized assistance for web development tasks

- **🔗 LlamaIndex Integration**  
  Native support for LlamaIndex framework with dedicated package.

- **🎯 Type Safety**  
  Fully typed with Pydantic models for better development experience.

---

## 📦 Installation

### Core Package

```bash
pip install qwen-api
```

### LlamaIndex Integration

```bash
pip install qwen-llamaindex
```

### Development Installation

```bash
git clone https://github.com/arosyihuddin/qwen-api.git
cd qwen-api
pip install -e .
```

---

## 🚀 Quick Start

### Basic Usage

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

# Initialize client
client = Qwen()

# Create a simple chat message
messages = [ChatMessage(
    role="user",
    content="What is artificial intelligence?",
    web_search=False,
    thinking=False
)]

# Get response
response = client.chat.create(
    messages=messages,
    model="qwen-max-latest"
)

print(response.choices.message.content)
```

### Streaming Response

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

client = Qwen()

messages = [ChatMessage(
    role="user",
    content="Write a story about AI",
    web_search=False,
    thinking=False
)]

# Stream the response
stream = client.chat.create(
    messages=messages,
    model="qwen-max-latest",
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Async Usage

```python
import asyncio
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

async def main():
    client = Qwen()

    messages = [ChatMessage(
        role="user",
        content="Explain quantum computing",
        web_search=True,
        thinking=True
    )]

    response = await client.chat.acreate(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

asyncio.run(main())
```

## 🎯 Advanced Examples

### File Upload and Image Analysis

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock

client = Qwen()

# Upload an image
file_result = client.chat.upload_file(
    file_path="path/to/your/image.jpg"
)

# Create message with image
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

# Get response
response = client.chat.create(
    messages=messages,
    model="qwen-max-latest",
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Function Calling with Tools

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

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
                'expression': {
                    'type': 'string',
                    'description': 'Mathematical expression to calculate'
                }
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
```

### Web Search Integration

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

client = Qwen()

messages = [ChatMessage(
    role="user",
    content="What are the latest AI developments in 2024?",
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

    # Handle web search results
    if hasattr(delta, 'extra') and delta.extra and 'web_search_info' in delta.extra:
        print(f"\n📚 Web Search Results:")
        for result in delta.extra.web_search_info:
            print(f"  • {result.title}: {result.url}")
        print()

    if delta.content:
        print(delta.content, end="", flush=True)
```

### Advanced Reasoning with Thinking Mode

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage

client = Qwen()

messages = [ChatMessage(
    role="user",
    content="Solve this step by step: A company's revenue increased by 25% in Q1, decreased by 15% in Q2, and increased by 30% in Q3. If the Q3 revenue is $169,000, what was the initial revenue?",
    web_search=False,
    thinking=True  # Enable thinking mode for step-by-step reasoning
)]

response = client.chat.create(
    messages=messages,
    model="qwen-max-latest"
)

print(response.choices.message.content)
```

### Web Development Mode

```python
from qwen_api import Qwen
from qwen_api.core.types.chat import ChatMessage, TextBlock

client = Qwen()

messages = [ChatMessage(
    role="user",
    web_search=False,
    thinking=False,
    web_development=True,  # Enable web development mode
    blocks=[
        TextBlock(
            block_type="text",
            text="Create a responsive navigation bar with HTML, CSS, and JavaScript that includes a mobile hamburger menu"
        )
    ]
)]

response = client.chat.create(
    messages=messages,
    model="qwen-max-latest"
)

print(response.choices.message.content)
```

## 🔗 LlamaIndex Integration

For seamless integration with LlamaIndex applications:

```python
from qwen_llamaindex import QwenLlamaIndex
from llama_index.core.base.llms.types import ChatMessage, MessageRole

# Initialize LlamaIndex integration
llm = QwenLlamaIndex(
    model="qwen-max-latest",
    temperature=0.7,
    max_tokens=2000
)

# Chat with LlamaIndex format
messages = [
    ChatMessage(role=MessageRole.USER, content="Explain machine learning")
]

# Synchronous chat
response = llm.chat(messages)
print(response.message.content)

# Streaming chat
for chunk in llm.stream_chat(messages):
    print(chunk.message.content, end="")

# Completion
response = llm.complete("Write a Python function to calculate fibonacci numbers")
print(response.text)
```

```python
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock


def main():
    client = Qwen(logging_level="DEBUG")

    try:
        # Upload an image file
        getdataImage  = client.chat.upload_file(
            file_path="tes_image.png"
        )

        # Create a chat message with both text and image content
        messages = [ChatMessage(
            role="user",
            web_search=False,
            thinking=False,
            blocks=[
                TextBlock(
                    block_type="text",
                    text="What's in this image?"
                ),
                ImageBlock(
                    block_type="image",
                    url=getdataImage   .file_url,
                    image_mimetype=getdataImage.image_mimetype
                )
            ]
        )]

        # Get a streaming response
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process the stream
        for chunk in response:
            delta = chunk.choices[0].delta
            if 'extra' in delta and 'web_search_info' in delta.extra:
                print("\nSearch results:", delta.extra.web_search_info)
                print()

            print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
```

### Async Usage

```python
import asyncio
from qwen_api.client import Qwen
from qwen_api.types.chat import ChatMessage

async def main():
    # Create a client instance
    client = Qwen()

    # Create a chat message
    messages = [
        ChatMessage(
            role="user",
            content="what is LLM?",
            web_search=True,
            thinking=False,
        )
    ]

    # Get a response from the API
    response = await client.chat.acreate(
        messages=messages,
        model="qwen-max-latest",
    )

    # Print the response
    print(response)

asyncio.run(main())
```

### Asynchronous File Upload Example

Here's how to perform file upload asynchronously:

```python
import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock


async def main():
    client = Qwen()

    try:
        # Upload an image file asynchronously
        getdataImage  = await client.chat.async_upload_file(
            file_path="tes_image.png"
        )

        # Create a chat message with both text and image content
        messages = [ChatMessage(
            role="user",
            web_search=False,
            thinking=False,
            blocks=[
                TextBlock(
                    block_type="text",
                    text="What's in this image?"
                ),
                ImageBlock(
                    block_type="image",
                    url=getdataImage   .file_url,
                    image_mimetype=getdataImage
                )
            ]
        )]

        # Get a streaming response
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process the stream
        async for chunk in response:
            delta = chunk.choices[0].delta
            if 'extra' in delta and 'web_search_info' in delta.extra:
                print("\nSearch results:", delta.extra.web_search_info)
                print()

            print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**

```
choices=Choice(message=Message(role='assistant', content='A Large Language Model (LLM) is a type of artificial intelligence model that utilizes machine learning techniques to understand and generate human language [[2]]. It is designed for natural language processing tasks such as language generation [[1]]. LLMs are highly effective at generating the most plausible text in response to an input, which is the primary task they were built for [[5]]. These models are trained on vast datasets and consist of very large deep learning models that are pre-trained on extensive amounts of data [[4]]. Additionally, LLMs are a subset of generative AI that focuses specifically on generating text [[6]].'), extra=Extra(web_search_info=[WebSearchInfo(url='https://en.wikipedia.org/wiki/Large_language_model', title='Large language model - Wikipedia', snippet='A large language model (LLM) is a type of machine learning model designed for natural language processing tasks such as language generation.', hostname=None, hostlogo=None, date=''), WebSearchInfo(url='https://www.redhat.com/en/topics/ai/what-are-large-language-models', title='What are large language models? - Red Hat', snippet='A large language model (LLM) is a type of artificial intelligence model that utilizes machine learning techniques to understand and generate human language.', hostname='红帽', hostlogo='https://img.alicdn.com/imgextra/i2/O1CN01fvSs6e1d0HjVt2Buc_!!6000000003673-73-tps-48-48.ico', date=' (2023-09-26)'), WebSearchInfo(url='https://www.sap.com/resources/what-is-large-language-model', title='What is a large language model (LLM)? - SAP', snippet='A large language model (LLM) is a type of artificial intelligence (AI) that excels at processing, understanding, and generating human language.', hostname='思爱普SAP', hostlogo='https://img.alicdn.com/imgextra/i2/O1CN01egAMx022rHxuPkTZz_!!6000000007173-73-tps-48-48.ico', date=' (2024-07-01)'), WebSearchInfo(url='https://aws.amazon.com/what-is/large-language-model/', title='What is LLM? - Large Language Models Explained - AWS', snippet='Large language models, also known as LLMs, are very large deep learning models that are pre-trained on vast amounts of data. The underlying transformer is a', hostname='亚马逊', hostlogo='https://img.alicdn.com/imgextra/i4/O1CN01WOsM1L1YEPsOe7ywI_!!6000000003027-73-tps-48-48.ico', date=''), WebSearchInfo(url='https://developers.google.com/machine-learning/resources/intro-llms', title='Introduction to Large Language Models | Machine Learning', snippet='LLMs are highly effective at the task they were built for, which is generating the most plausible text in response to an input. They are even', hostname=None, hostlogo=None, date=' (2024-09-06)'), WebSearchInfo(url='https://medium.com/@meenn396/differences-between-llm-deep-learning-machine-learning-and-ai-3c7eb1c87ef8', title='Differences between LLM, Deep learning, Machine learning, and AI', snippet='A Large Language Model (LLM) is a subset of generative AI that focuses on generating text. The LLM is trained on a vast dataset and consists of', hostname=None, hostlogo=None, date=' (2024-09-30)'), WebSearchInfo(url='https://maddevs.io/glossary/large-language-model/', title='What Is a Large Language Model (LLM) | Machine Learing Glossary', snippet='A Large Language Model (LLM) is an AI system that understands and generates human language by analyzing vast amounts of text data. LLMs and Generative', hostname=None, hostlogo=None, date=''), WebSearchInfo(url='https://medium.com/@marketing_novita.ai/ml-vs-llm-what-is-the-difference-between-machine-learning-and-large-language-model-1d2ffa8756a6', title='ML vs LLM: What is the difference between Machine Learning and ', snippet="Initially, it's essential to recognize that Large Language Models (LLMs) are a subset of Machine Learning (ML). Machine Learning encompasses a", hostname=None, hostlogo=None, date=' (2024-05-08)'), WebSearchInfo(url='https://medium.com/@siladityaghosh/ai-machine-learning-llm-and-nlp-d09ae7b65582', title='AI, Machine Learning, LLM, and NLP | by Siladitya Ghosh - Medium', snippet='Large Language Models (LLM):. Definition: LLM involves training models on vast datasets to comprehend and generate human-like text, facilitating', hostname=None, hostlogo=None, date=' (2024-01-08)'), WebSearchInfo(url='https://github.com/Hannibal046/Awesome-LLM', title='Awesome-LLM: a curated list of Large Language Model - GitHub', snippet='Here is a curated list of papers about large language models, especially relating to ChatGPT. It also contains frameworks for LLM training, tools to deploy LLM', hostname='GitHub', hostlogo='https://img.alicdn.com/imgextra/i1/O1CN01Pzz5rH1SIBQeVFb7w_!!6000000002223-55-tps-32-32.svg', date='')]))
```

### Streaming

```python
# Create a client instance
client = Qwen()

# Create a chat message
messages = [
   ChatMessage(
      role="user",
      content="what is LLM?",
      web_search=True,
      thinking=False,
   )
]

# Get a streaming response from the API
response = client.chat.create(
   messages=messages,
   model="qwen-max-latest",
   stream=True,
)

# Process the stream
for chunk in response:
   print(chunk.model_dump())
```

**Output:**

```
{'choices': [{'delta': {'role': 'assistant', 'content': '', 'name': '', 'function_call': {'name': 'web_search', 'arguments': ''}, 'extra': None}}]}
{'choices': [{'delta': {'role': 'function', 'content': '', 'name': 'web_search', 'function_call': None, 'extra': {'web_search_info': [{'url': 'https://en.wikipedia.org/wiki/Large_language_model', 'title': 'Large language model - Wikipedia', 'snippet': 'A large language model (LLM) is a type of machine learning model designed for natural language processing tasks such as language generation.', 'hostname': None, 'hostlogo': None, 'date': ''}, {'url': 'https://www.redhat.com/en/topics/ai/what-are-large-language-models', 'title': 'What are large language models? - Red Hat', 'snippet': 'A large language model (LLM) is a type of artificial intelligence model that utilizes machine learning techniques to understand and generate human language.', 'hostname': '红帽', 'hostlogo': 'https://img.alicdn.com/imgextra/i2/O1CN01fvSs6e1d0HjVt2Buc_!!6000000003673-73-tps-48-48.ico', 'date': ' (2023-09-26)'}, {'url': 'https://www.sap.com/resources/what-is-large-language-model', 'title': 'What is a large language model (LLM)? - SAP', 'snippet': 'A large language model (LLM) is a type of artificial intelligence (AI) that excels at processing, understanding, and generating human language.', 'hostname': '思爱普SAP', 'hostlogo': 'https://img.alicdn.com/imgextra/i2/O1CN01egAMx022rHxuPkTZz_!!6000000007173-73-tps-48-48.ico', 'date': ' (2024-07-01)'}, {'url': 'https://aws.amazon.com/what-is/large-language-model/', 'title': 'What is LLM? - Large Language Models Explained - AWS', 'snippet': 'Large language models, also known as LLMs, are very large deep learning models that are pre-trained on vast amounts of data. The underlying transformer is a', 'hostname': '亚马逊', 'hostlogo': 'https://img.alicdn.com/imgextra/i4/O1CN01WOsM1L1YEPsOe7ywI_!!6000000003027-73-tps-48-48.ico', 'date': ''}, {'url': 'https://developers.google.com/machine-learning/resources/intro-llms', 'title': 'Introduction to Large Language Models | Machine Learning', 'snippet': 'LLMs are highly effective at the task they were built for, which is generating the most plausible text in response to an input. They are even', 'hostname': None, 'hostlogo': None, 'date': ' (2024-09-06)'}, {'url': 'https://medium.com/@meenn396/differences-between-llm-deep-learning-machine-learning-and-ai-3c7eb1c87ef8', 'title': 'Differences between LLM, Deep learning, Machine learning, and AI', 'snippet': 'A Large Language Model (LLM) is a subset of generative AI that focuses on generating text. The LLM is trained on a vast dataset and consists of', 'hostname': None, 'hostlogo': None, 'date': ' (2024-09-30)'}, {'url': 'https://maddevs.io/glossary/large-language-model/', 'title': 'What Is a Large Language Model (LLM) | Machine Learing Glossary', 'snippet': 'A Large Language Model (LLM) is an AI system that understands and generates human language by analyzing vast amounts of text data. LLMs and Generative', 'hostname': None, 'hostlogo': None, 'date': ''}, {'url': 'https://medium.com/@marketing_novita.ai/ml-vs-llm-what-is-the-difference-between-machine-learning-and-large-language-model-1d2ffa8756a6', 'title': 'ML vs LLM: What is the difference between Machine Learning and ', 'snippet': "Initially, it's essential to recognize that Large Language Models (LLMs) are a subset of Machine Learning (ML). Machine Learning encompasses a", 'hostname': None, 'hostlogo': None, 'date': ' (2024-05-08)'}, {'url': 'https://medium.com/@siladityaghosh/ai-machine-learning-llm-and-nlp-d09ae7b65582', 'title': 'AI, Machine Learning, LLM, and NLP | by Siladitya Ghosh - Medium', 'snippet': 'Large Language Models (LLM):. Definition: LLM involves training models on vast datasets to comprehend and generate human-like text, facilitating', 'hostname': None, 'hostlogo': None, 'date': ' (2024-01-08)'}, {'url': 'https://github.com/Hannibal046/Awesome-LLM', 'title': 'Awesome-LLM: a curated list of Large Language Model - GitHub', 'snippet': 'Here is a curated list of papers about large language models, especially relating to ChatGPT. It also contains frameworks for LLM training, tools to deploy LLM', 'hostname': 'GitHub', 'hostlogo': 'https://img.alicdn.com/imgextra/i1/O1CN01Pzz5rH1SIBQeVFb7w_!!6000000002223-55-tps-32-32.svg', 'date': '')]))
```

## � Error Handling

```python
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError, AuthError, RateLimitError
from qwen_api.core.types.chat import ChatMessage

try:
    client = Qwen()
    messages = [ChatMessage(
        role="user",
        content="Hello, world!",
        web_search=False,
        thinking=False
    )]

    response = client.chat.create(
        messages=messages,
        model="qwen-max-latest"
    )

    print(response.choices.message.content)

except AuthError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except QwenAPIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## ⚙️ Configuration Options

### Client Configuration

```python
from qwen_api import Qwen

# Full configuration
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

## 📚 Documentation

For complete documentation, visit:

- [**Complete API Documentation**](docs/documentation.md) - Comprehensive guide with all features
- [**Usage Documentation**](docs/usage_documentation.md) - Practical examples and best practices

## 🚀 Project Structure

This repository contains two main packages:

1. **`qwen-api`** - Core SDK for direct API interaction
2. **`qwen-llamaindex`** - LlamaIndex integration for seamless use with LlamaIndex applications

Both packages are available on PyPI and can be installed independently.

## ⚙️ Environment Setup

To use `qwen-api`, you need to obtain your `AUTH TOKEN` and `COOKIE` from [https://chat.qwen.ai](https://chat.qwen.ai). Follow these steps:

### 🔑 Getting Authentication Credentials

1. **Sign Up or Log In**  
   Visit [https://chat.qwen.ai](https://chat.qwen.ai) and sign up or log in to your account.

2. **Open Developer Tools**

   - Right-click anywhere on the page and select `Inspect`, or
   - Use the shortcut: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
   - Navigate to the `Network` tab

3. **Send a Message**  
   Go back to [https://chat.qwen.ai](https://chat.qwen.ai) and send a message in the chat.

4. **Find the `completions` Request**  
   In the `Network` tab, filter by `Fetch/XHR` and locate a request named `completions`.

5. **Copy the Authorization Token and Cookie**

   - Click the `completions` request and go to the `Headers` tab.
   - Look for the `Authorization` header that starts with `Bearer`, and copy **only the token part** (without the word "Bearer").

     Example:

     ```
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```

   - Scroll down and find the `Cookie` header. Copy the entire value.

     Example (partial):

     ```
     Cookie: cna=lyp6INOXADYCAbb9MozTsTcp; cnaui=83a0f88d-86d8-...; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```

### 🔧 Setting Up Environment Variables

6. **Save in `.env` File**  
   Create a `.env` file in the root directory of your project and paste the following:

   ```env
   QWEN_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # no "Bearer" prefix
   QWEN_COOKIE="cna=lyp6INOXADYCA...; cnaui=83a0f88d-86d8-...; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

### 🛠️ Additional Dependencies

For file upload functionality with Alibaba Cloud OSS:

```bash
pip install oss2
```

### ⚠️ Important Notes

- **Never share your token or cookie publicly**
- **Tokens and cookies may expire** - If authentication fails, repeat the steps above to obtain new credentials
- **Store credentials securely** - Use environment variables or secure credential management systems
- **Use HTTPS only** - Always ensure you're using secure connections

## 📂 Examples

Explore the `examples/` directory for comprehensive usage examples:

### 📋 Available Examples

- **[Basic Usage](qwen_api/examples/basic_usage.py)** - Simple synchronous chat requests
- **[Async Usage](qwen_api/examples/async_usage.py)** - Asynchronous chat operations
- **[Streaming](qwen_api/examples/basic_usage_stream.py)** - Real-time response streaming
- **[Async Streaming](qwen_api/examples/async_usage_stream.py)** - Asynchronous streaming responses
- **[File Upload](qwen_api/examples/basic_usage_stream.py)** - Image upload and analysis
- **[Function Calling](qwen_api/examples/basic_usage.py)** - Using tools with the API
- **[Cancellation](qwen_api/examples/cancel_usage.py)** - Request cancellation handling
- **[Interrupt Handling](qwen_api/examples/interrupt_handling.py)** - Graceful interrupt handling
- **[LlamaIndex Integration](qwen_llamaindex/examples/)** - Complete LlamaIndex examples

### � Running Examples

```bash
# Clone the repository
git clone https://github.com/arosyihuddin/qwen-api.git
cd qwen-api

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env  # Edit with your credentials

# Run examples
python qwen_api/examples/basic_usage.py
python qwen_api/examples/async_usage.py
python qwen_api/examples/basic_usage_stream.py
```

## 🧪 Testing

Run tests to ensure everything works correctly:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run specific test
pytest tests/test_client.py -v
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🚀 Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/qwen-api.git
   cd qwen-api
   ```

2. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

### 📝 Contribution Guidelines

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with proper tests and documentation

3. **Run tests and linting**

   ```bash
   pytest
   black .
   mypy .
   ```

4. **Commit your changes**

   ```bash
   git commit -m "Add: your feature description"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### 🐛 Bug Reports

When reporting bugs, please include:

- Python version and operating system
- Qwen-api version
- Complete error traceback
- Minimal code example to reproduce the issue

### 💡 Feature Requests

For feature requests, please:

- Check if the feature already exists in the documentation
- Provide a clear use case and rationale
- Include example code showing how you'd like to use the feature

## 📊 Project Statistics

- **Total Downloads**: [![Downloads](https://static.pepy.tech/badge/qwen-api)](https://pepy.tech/project/qwen-api)
- **GitHub Stars**: [![GitHub Stars](https://img.shields.io/github/stars/arosyihuddin/qwen-api?style=social)](https://github.com/arosyihuddin/qwen-api)
- **Issues**: [![GitHub Issues](https://img.shields.io/github/issues/arosyihuddin/qwen-api)](https://github.com/arosyihuddin/qwen-api/issues)
- **License**: [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Support

If you find this project helpful, please consider:

- ⭐ **Starring** the repository
- 🐛 **Reporting issues** you encounter
- 💡 **Suggesting new features**
- 🤝 **Contributing** to the codebase
- 📢 **Sharing** with others who might benefit

## 🔗 Links

- **PyPI Package**: [qwen-api](https://pypi.org/project/qwen-api/)
- **GitHub Repository**: [arosyihuddin/qwen-api](https://github.com/arosyihuddin/qwen-api)
- **Documentation**: [docs/documentation.md](docs/documentation.md)
- **Issue Tracker**: [GitHub Issues](https://github.com/arosyihuddin/qwen-api/issues)
- **Official Qwen**: [https://chat.qwen.ai](https://chat.qwen.ai)

## 📃 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Ahmad Rosyihuddin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact

**Ahmad Rosyihuddin**

- GitHub: [@arosyihuddin](https://github.com/arosyihuddin)
- Email: rosyihuddin.dev@gmail.com

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/arosyihuddin">Ahmad Rosyihuddin</a></p>
  <p>
    <a href="https://github.com/arosyihuddin/qwen-api">⭐ Star this repository</a> if you find it helpful!
  </p>
</div>
