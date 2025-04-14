from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError


def main():
    # Inisialisasi client
    client = Qwen()

    try:
        # Kirim pesan
        # response = client.send_message("halo", stream=True)
        response = client.chat.create(
            messages=[{"role": "user", "content": "Halo"}],
            model="qwen-max-latest",
            stream=True,
        )
        # Streaming response
        for chunk in response:
            print(chunk)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
