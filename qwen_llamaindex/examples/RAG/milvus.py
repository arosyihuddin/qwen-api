from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core import Settings
from qwen_llamaindex import QwenLlamaIndex

embeddings = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-base")
llm = QwenLlamaIndex()
print(llm.metadata)
Settings.llm = llm
Settings.embed_model = embeddings

vector_store = MilvusVectorStore(
    uri="http://localhost:19530",
    collection_name="test",
    dim=768,
    index_config={
        "metric_type": "IP",  
        "index_type": "IVF_FLAT", 
        "params": {"nlist": 128}, 
    },
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)
documents = [
    Document(text="Ahmad Rosyihuddin adalah seorang mahasiswa universitas trunojoyo madura"),
    Document(text="Milvus adalah database vektor open-source."),
]

storage = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage, show_progress=True)

chat_engine = index.as_chat_engine(verbose=True, chat_mode="react")
result = chat_engine.chat("siapa ahmad rosyihuddin")
print(result)