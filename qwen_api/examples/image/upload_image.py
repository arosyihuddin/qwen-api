"""
Image Upload Example

This script demonstrates how to upload and use images with the Qwen API.
It shows both file path and base64 upload methods.
"""

import asyncio
import base64
import os
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


async def upload_and_analyze_image(
    client, image_path=None, base64_data=None, description="image"
):
    """Helper function to upload and analyze an image"""
    try:
        print(f"\n=== Uploading {description} ===")

        # Upload the image
        if image_path:
            print(f"Uploading from file: {image_path}")
            file_result = await client.chat.async_upload_file(file_path=image_path)
        elif base64_data:
            print("Uploading from base64 data")
            file_result = await client.chat.async_upload_file(base64_data=base64_data)
        else:
            raise ValueError("Either image_path or base64_data must be provided")

        print(f"✅ Upload successful!")
        print(f"File ID: {file_result.file_id}")
        print(f"File URL: {file_result.file_url}")
        print(f"MIME Type: {file_result.image_mimetype}")

        # Use the uploaded image in a chat
        print("\n--- Analyzing the image ---")
        messages = [
            ChatMessage(
                role="user",
                content="Jelaskan apa yang kamu lihat di gambar ini secara detail",
                web_search=False,
                thinking=False,
            )
        ]

        # Add the image to the message
        messages[0].blocks = [
            {
                "block_type": "image",
                "image": {
                    "file_id": file_result.file_id,
                    "file_url": file_result.file_url,
                },
            }
        ]

        response = await client.chat.acreate(
            messages=messages,
            model="qwen-vl-max",  # Use vision model for image analysis
            temperature=0.7,
            max_tokens=1024,
        )

        print(f"✅ Analysis complete!")
        print(f"Response: {response.choices.message.content}")

        return file_result

    except Exception as e:
        print(f"❌ Error with {description}: {str(e)}")
        return None


def create_sample_base64_image():
    """Create a simple base64 encoded image for demonstration"""
    # This is a tiny 1x1 pixel PNG image encoded as base64
    # In real usage, you would have actual image data
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    return f"data:image/png;base64,{tiny_png_base64}"


async def main():
    """
    Main async function that demonstrates image upload and analysis.

    1. Creates a Qwen client instance
    2. Tests file path upload (if image exists)
    3. Tests base64 upload
    4. Analyzes uploaded images with vision model
    """
    # Initialize the Qwen client
    client = Qwen()

    print("Starting image upload and analysis demo...")

    try:
        # Check if the test image exists
        test_image_path = "examples/tes_image.png"

        if os.path.exists(test_image_path):
            # Test 1: Upload from file path
            await upload_and_analyze_image(
                client, image_path=test_image_path, description="test image from file"
            )
        else:
            print(f"⚠️  Test image not found at {test_image_path}")

        # Test 2: Upload from base64 data
        base64_image = create_sample_base64_image()
        await upload_and_analyze_image(
            client, base64_data=base64_image, description="sample base64 image"
        )

        # Test 3: Synchronous upload (for comparison)
        print("\n=== Synchronous Upload Test ===")
        try:
            base64_image_simple = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            sync_result = client.chat.upload_file(
                base64_data=f"data:image/png;base64,{base64_image_simple}"
            )
            print(f"✅ Sync upload successful!")
            print(f"File ID: {sync_result.file_id}")
            print(f"File URL: {sync_result.file_url}")
        except Exception as e:
            print(f"❌ Sync upload error: {str(e)}")

        print("\n" + "=" * 50)
        print("IMAGE UPLOAD DEMO COMPLETED")
        print("=" * 50)
        print("📝 Summary:")
        print("- Demonstrated async file upload from path")
        print("- Demonstrated async base64 upload")
        print("- Demonstrated sync base64 upload")
        print("- Showed image analysis with vision model")
        print("- Displayed upload results and metadata")

    except QwenAPIError as e:
        print(f"\nQwen API Error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
