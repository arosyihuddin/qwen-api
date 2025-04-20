from qwen_api.llama_index import QwenLlamaIndex

def main():
    llm = QwenLlamaIndex()
    response = llm.complete("Apa ibu kota Indonesia?")
    print(response.text)

if __name__ == "__main__":
    main()
