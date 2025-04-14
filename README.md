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

To use `qwen-api`, you need to obtain your `AUTH TOKEN` and `COOKIE` from [https://chat.qwen.ai](https://chat.qwen.ai). Follow these steps:

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

6. **Save in `.env` File**  
   Create a `.env` file in the root directory of your project and paste the following:

   ```env
   QWEN_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # no "Bearer"
   QWEN_COOKIE="cna=lyp6INOXADYCA...; cnaui=83a0f88d-86d8-...; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

⚠️ **Note**:

- Never share your token or cookie publicly.
- Tokens and cookies may expire. If authentication fails, repeat the steps above to obtain a new one.

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
