from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError

def main():
    client = Qwen(timeout=0.1)  # Timeout sangat pendek untuk testing
    
    try:
        # Request yang akan timeout
        response = client.send_message("Jelaskan black hole")
        print(response)
        
    except QwenAPIError as e:
        print(f"Terjadi error:")
        print(f"Type: {type(e).__name__}")
        print(f"Detail: {str(e)}")

if __name__ == "__main__":
    main()