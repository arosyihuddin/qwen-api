from qwen_api import Qwen

def stream_callback(chunk: str):
    """Callback untuk menangani streaming response"""
    print(chunk, end="", flush=True)

def main():
    client = Qwen()
    
    print("Mulai streaming...")
    full_response = client.send_message(
        "Buat puisi pendek tentang teknologi",
        stream=True
    )
    
    print("\n\nFull Response:")
    print(full_response)

if __name__ == "__main__":
    main()