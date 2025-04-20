from qwen_api.llama_index import QwenLlamaIndex

def main():
    llm = QwenLlamaIndex()
    response = llm.stream_complete("Apa ibu kota Indonesia?")
    for chunk in response:
        print(chunk.delta, end="", flush=True)

if __name__ == "__main__":
    main()
