from qwen_api.llama_index import QwenLlamaIndex
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.types.chat import ChatMessage

# from llama_index.core.types import ChatMessage

def main():
    llm = QwenLlamaIndex()    
    response = llm.stream_chat([ChatMessage(role="user", content="Apa ibu kota Indonesia?")])
    for chunk in response:
        print(chunk.delta, end="", flush=True)
        
if __name__ == "__main__":
    main()
