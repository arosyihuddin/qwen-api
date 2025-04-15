from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.types.chat import ChatMessage

def main():
    # Inisialisasi client
    client = Qwen()

    try:
        messages = [ChatMessage(
            role="user", 
            content="what is LLM?",
            web_search=True,
            thinking=False,
        )]
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
        )

        print(response)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
