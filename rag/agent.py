import os
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# התחברות לאינדקס הקיים (לא בונים מחדש - רק מתחברים למה שכבר יש)
# ============================================================
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.cohere import Cohere
from llama_index.core.response_synthesizers import get_response_synthesizer

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]

embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY,
    model_name="embed-english-v3.0",
    input_type="search_query",
)

pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("rag-course-project")
pinecone_vector_store = PineconeVectorStore(
    pinecone_index=pinecone_index, namespace="claude-code-docs"
)

index = VectorStoreIndex.from_vector_store(
    vector_store=pinecone_vector_store,
    embed_model=embed_model,
)

retriever = index.as_retriever(similarity_top_k=3)
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.35)

llm = Cohere(
    api_key=COHERE_API_KEY,
    model="command-r-08-2024",
)
response_synthesizer = get_response_synthesizer(llm=llm)


# ============================================================
# פונקציה אחת שעוטפת את כל התהליך: Retrieve -> Postprocess -> Synthesize
# ============================================================
def answer_question(question):
    results = retriever.retrieve(question)
    filtered_results = postprocessor.postprocess_nodes(results)

    if not filtered_results:
        return "לא נמצא מידע רלוונטי מספיק בקבצי התיעוד כדי לענות על השאלה."

    response = response_synthesizer.synthesize(question, nodes=filtered_results)
    return str(response)


# ============================================================
# ממשק Gradio
# ============================================================
import gradio as gr

demo = gr.Interface(
    fn=answer_question,
    inputs=gr.Textbox(label="שאלה", placeholder="לדוגמה: What database was chosen for the project?"),
    outputs=gr.Textbox(label="תשובה"),
    title="RAG על קבצי התיעוד של הפרויקט",
    description="שאלי שאלה על התיעוד (ADR, README, SETUP_GUIDE ועוד) והמערכת תענה בהתבסס על הקבצים בפועל.",
)

if __name__ == "__main__":
    demo.launch()