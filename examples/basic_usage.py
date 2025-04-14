from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError


def main():
    # Inisialisasi client
    client = Qwen()

    try:
        response = client.chat.create(
            messages=[
                {"role": "user", "content": "siapa presiden indonesia saat ini?"}],
            model="qwen-max-latest",
        )

        print(response)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
