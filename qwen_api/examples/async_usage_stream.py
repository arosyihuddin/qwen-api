"""
Basic Asynchronous Streaming Usage Example

This script demonstrates how to use the Qwen API asynchronously with streaming enabled
to handle partial results in real-time.
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage, ImageBlock, TextBlock


async def main():
    """
    Main async function that demonstrates basic asynchronous streaming usage of the Qwen API.

    1. Creates a Qwen client instance
    2. Uploads an image file to the Qwen API using async upload method
    3. Constructs a chat message asking about the content of the uploaded image
    4. Sends the request to the Qwen API using asynchronous streaming
    5. Processes and prints the streaming response in real-time
    """
    # Initialize the Qwen client
    client = Qwen()

    try:
        # Upload an image file to the Qwen API using async upload method
        getdataImage = await client.chat.async_upload_file(
            base64_data="data:image/webp;base64,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"
        )

        # Create the chat message
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
                    url=getdataImage.file_url,
                    image_mimetype=getdataImage.image_mimetype
                )
            ]
        )]

        # Send the request to the Qwen API using asynchronous streaming
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            stream=True,
        )

        # Process and print the streaming response in real-time
        async for chunk in response:
            if chunk.choices[0].delta.extra:
                print("Hasil pencarian:",
                      chunk.choices[0].delta.extra.web_search_info)
                print()

            print(chunk.choices[0].delta.content, end="", flush=True)

    except QwenAPIError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
