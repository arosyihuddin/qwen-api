"""
Basic Synchronous Streaming Usage Example

This script demonstrates how to use the Qwen API with streaming enabled to handle
partial results in real-time. It also includes an example of image upload and processing.
"""

from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, TextBlock, ImageBlock


def main():
    """
    Main function that demonstrates basic synchronous streaming usage of the Qwen API.

    1. Creates a Qwen client instance with debug logging enabled
    2. Uploads an image file to the Qwen API
    3. Constructs a chat message asking about the content of the uploaded image
    4. Sends the request to the Qwen API with streaming enabled
    5. Processes and prints the streaming response in real-time
    """
    # Initialize the Qwen client with debug logging
    client = Qwen(logging_level="DEBUG")

    try:
        # Upload an image file to the Qwen API
        getDataImage = client.chat.upload_file(
            file_path="/home/pstar7/Documents/Personal/Open Source Project/qwen-api/examples/tes_image.png"
        )

        # Create the chat message with both text and image content
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
                    url=getDataImage.file_url,
                    image_mimetype=getDataImage.image_mimetype
                )
            ]
        )]

        # Send the request to the Qwen API with streaming enabled
        response = client.chat.create(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process and print the streaming response in real-time
        for chunk in response:
            delta = chunk.choices[0].delta

            # Handle any web search information in the response
            if 'extra' in delta and 'web_search_info' in delta.extra:
                print("\nHasil pencarian:", delta.extra.web_search_info)
                print()

            # Print the content as it arrives
            print(delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
