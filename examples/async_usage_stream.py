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
            file_path="/home/pstar7/Documents/Personal/Open Source Project/qwen-api/examples/tes_image.png"
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
