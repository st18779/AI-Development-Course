import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

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

postprocessor = SimilarityPostprocessor(similarity_cutoff=0.35)

llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")
response_synthesizer = get_response_synthesizer(llm=llm)


# ============================================================
# Events - כל אחד מייצג "תוצר" ברור של Step מסוים
# ============================================================
from llama_index.core.workflow import (
    Workflow, step, StartEvent, StopEvent, Event, Context
)


class RetrieveEvent(Event):
    nodes: list
    question: str


class PostprocessEvent(Event):
    nodes: list
    question: str


class RetryRetrieveEvent(Event):
    # מסמן: "תחזרי ל-retrieve, אבל הפעם עם top_k גדול יותר"
    question: str
    top_k: int


# ============================================================
# Workflow עם ולידציות וניתוב
# ============================================================
class RAGWorkflow(Workflow):

    @step
    async def retrieve(
        self, ctx: Context, ev: StartEvent | RetryRetrieveEvent
    ) -> RetrieveEvent | StopEvent:

        # --- קריאת השאלה: מ-StartEvent בפעם הראשונה, או מ-RetryRetrieveEvent בניסיון חוזר ---
        question = getattr(ev, "question", None)
        top_k = getattr(ev, "top_k", 3)

        # --- ולידציה 1: קלט ריק ---
        if not question or not question.strip():
            return StopEvent(result="השאלה ריקה - אנא כתבי שאלה תקינה.")

        # שומרות את השאלה ב-State הגלובלי (Context) - כדי שתהיה נגישה גם ל-Step האחרון (synthesize)
        await ctx.store.set("question", question)

        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(question)

        # --- ולידציה 2: אין שום תוצאה כבר בשלב החיפוש עצמו ---
        if not nodes:
            return StopEvent(result="לא נמצא מידע רלוונטי בקבצי התיעוד.")

        return RetrieveEvent(nodes=nodes, question=question)

    @step
    async def postprocess(
        self, ctx: Context, ev: RetrieveEvent
    ) -> PostprocessEvent | RetryRetrieveEvent | StopEvent:

        filtered = postprocessor.postprocess_nodes(ev.nodes)

        # --- ולידציה 3: confidence נמוך מדי - postprocessing סינן הכל ---
        if not filtered:
            retry_count = await ctx.store.get("retry_count", default=0)
            current_top_k = len(ev.nodes)

            if retry_count == 0 and current_top_k < 6:
                # --- ניתוב: ננסה שוב מ-retrieve, עם top_k רחב יותר ---
                await ctx.store.set("retry_count", retry_count + 1)
                return RetryRetrieveEvent(question=ev.question, top_k=current_top_k + 3)

            # כבר הרחבנו וגם זה לא הספיק - עוצרים בצורה מבוקרת, לא ממשיכים ל-LLM עם כלום
            return StopEvent(result="לא נמצא מידע רלוונטי מספיק גם אחרי חיפוש מורחב.")

        return PostprocessEvent(nodes=filtered, question=ev.question)

    @step
    async def synthesize(self, ctx: Context, ev: PostprocessEvent) -> StopEvent:
        response = response_synthesizer.synthesize(ev.question, nodes=ev.nodes)
        return StopEvent(result=str(response))


# ============================================================
# חיבור ה-Workflow לממשק Gradio
# ============================================================
import gradio as gr

workflow = RAGWorkflow(timeout=60, verbose=False)


async def _run_workflow(question):
    return await workflow.run(question=question)


def answer_question_workflow(question):
    result = asyncio.run(_run_workflow(question))
    return str(result)


demo = gr.Interface(
    fn=answer_question_workflow,
    inputs=gr.Textbox(label="שאלה", placeholder="לדוגמה: What database was chosen for the project?"),
    outputs=gr.Textbox(label="תשובה"),
    title="RAG על קבצי התיעוד של הפרויקט (Event-Driven Workflow)",
    description="שאלי שאלה על התיעוד. המערכת בנויה כ-Workflow עם ולידציות וניתוב אוטומטי בין שלבים.",
)

if __name__ == "__main__":
    demo.launch()