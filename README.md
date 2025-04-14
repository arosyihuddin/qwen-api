# qwen-api

[![PyPI version](https://badge.fury.io/py/qwen-api.svg)](https://pypi.org/project/qwen-api/)

Unofficial Python SDK for accessing [Qwen AI](https://chat.qwen.ai) API.

---

## ✨ Features

- Easy-to-use interface to interact with Qwen chat completions
- Support for both sync and async usage
- Streamed response handling
- Built-in auth manager via `.env`
- Fully typed models using `pydantic`

---

## 📦 Installation

```bash
pip install qwen-api
```

---

## 🚀 Usage

### Basic Usage

```python
from qwen_api.client import Qwen
from qwen_api.types.chat import ChatMessage

client = Qwen()
messages = [
    ChatMessage(role="user", content="Hello! What can you do?")
]

response = client.chat.create(messages=messages, model="qwen-max-latest")
print(response.choices)
```

### Async Usage

```python
import asyncio
from qwen_api.client import Qwen
from qwen_api.types.chat import ChatMessage

async def main():
    client = Qwen()
    messages = [
        ChatMessage(role="user", content="Tell me a joke.")
    ]
    response = await client.chat.acreate(messages=messages, model="qwen-max-latest")
    print(response.choices)

asyncio.run(main())
```

### Streaming

```python
for chunk in client.chat.create(messages=messages, model="qwen-max-latest", stream=True):
    print(chunk.choices)
```

---

## ⚙️ Environment Setup

Make sure you have a `.env` file in your root directory with:

```env
QWEN_AUTH_TOKEN=your_api_token
QWEN_COOKIE=your_cookie_value
```

---

## 📂 Examples

Check the `examples/` folder for more advanced usage.

---

## 📃 License

Copyright 2025 Ahmad Rosyihuddin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## 🙋‍♂️ Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/feature-name`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/feature-name`)
5. Open a Pull Request
