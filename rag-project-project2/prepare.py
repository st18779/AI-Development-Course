import os
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# שלב 1: LOADING
# ============================================================
from llama_index.core import SimpleDirectoryReader
 
reader = SimpleDirectoryReader(input_dir="docs_sources/claude_code")
documents = reader.load_data()
 
for doc in documents:
    doc.metadata["tool"] = "claude_code"
 
print(len(documents))
 


# ============================================================
# שלב 2: chunking
# ============================================================


from llama_index.core.node_parser import SentenceSplitter

node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

nodes = node_parser.get_nodes_from_documents(
    documents =documents, show_progress=True
)
print("Number of chunks (nodes):", len(nodes))

for doc in documents:
    print(doc.metadata.get("file_name"), "-", len(doc.text), "characters")


# ============================================================
# שלב 3: embedding
# ============================================================

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
from llama_index.embeddings.cohere import CohereEmbedding

embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY,
    model_name="embed-english-v3.0",
    input_type="search_document",
)




# ============================================================
# שלב 4: Indexing and Saving
# ============================================================

from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("rag-course-project")
pinecone_vector_store = PineconeVectorStore(pinecone_index=pinecone_index, namespace="claude-code-docs")

storage_context = StorageContext.from_defaults(vector_store=pinecone_vector_store)
index = VectorStoreIndex(
    nodes,
    storage_context=storage_context,
    embed_model=embed_model,
)