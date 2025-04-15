from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError

def main():
    client = Qwen(timeout=0.1) 
    
    try:
        response = client.send_message("what is LLM")
        print(response)
        
    except QwenAPIError as e:
        print(f"Terjadi error:")
        print(f"Type: {type(e).__name__}")
        print(f"Detail: {str(e)}")

if __name__ == "__main__":
    main()