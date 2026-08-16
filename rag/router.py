import os
import json
from dotenv import load_dotenv
load_dotenv()

from llama_index.llms.cohere import Cohere
from llama_index.core.llms import ChatMessage

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")


# ============================================================
# שלב 1: טעינת הנתונים המובנים שחילצנו קודם ב-extract.py
# ============================================================
with open("data/extracted_data.json", "r", encoding="utf-8") as f:
    extracted_data = json.load(f)


# ============================================================
# שלב 2: הגדרת מבנה ה"שאילתה" שה-LLM יבנה - בהתאם לסכמה שהגדרנו
# ============================================================
from pydantic import BaseModel, Field
from typing import Literal, Optional
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser


class RouteQuery(BaseModel):
    route: Literal["structured", "semantic"] = Field(
        description="structured = the question asks for a list/count/all items. "
                    "semantic = the question asks about a specific fact or reason."
    )
    category: Literal["decisions", "rules", "warnings", "all"] = Field(
        description="Relevant only if route=structured. Which item type the question is about. "
                    "Use 'all' if not specific to one type."
    )
    keyword: Optional[str] = Field(
        default=None,
        description="Relevant only if route=structured. A single keyword to filter items by "
                    "(matched against their text), or null if the question wants everything in the category."
    )


query_prompt = """\
Analyze the following question about a software project's documentation, and build
a query object according to the schema, to decide how to retrieve the answer.

Question: {question}

{format_instructions}
"""

output_parser = PydanticOutputParser(RouteQuery)

query_program = LLMTextCompletionProgram.from_defaults(
    output_parser=output_parser,
    prompt_template_str=query_prompt,
    llm=llm,
)


def generate_query(question):
    return query_program(
        question=question,
        format_instructions=output_parser.get_format_string(),
    )


# ============================================================
# שלב 3: הרצת השאילתה בפועל - סינון פשוט על הנתונים המובנים
# ============================================================
def run_query(query: RouteQuery):
    if query.category == "all":
        categories = extracted_data.keys()
    else:
        categories = [query.category]

    matched_items = []
    for cat in categories:
        for item in extracted_data.get(cat, []):
            if query.keyword:
                item_text = json.dumps(item, ensure_ascii=False).lower()
                if query.keyword.lower() not in item_text:
                    continue
            matched_items.append({"category": cat, **item})

    return matched_items


# ============================================================
# שלב 4: ניסוח תשובה סופית - מובנה או סמנטי
# ============================================================
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.schema import TextNode, NodeWithScore

response_synthesizer = get_response_synthesizer(llm=llm)


def answer_structured(question, matched_items):
    if not matched_items:
        return "לא נמצאו פריטים מתאימים בנתונים המובנים לשאלה זו."

    items_text = "\n".join(json.dumps(item, ensure_ascii=False) for item in matched_items)
    node = TextNode(text=items_text)
    node_with_score = NodeWithScore(node=node, score=1.0)

    response = response_synthesizer.synthesize(question, nodes=[node_with_score])
    return str(response)


from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor

embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY,
    model_name="embed-english-v3.0",
    input_type="search_query",
)

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
pinecone_index = pc.Index("rag-course-project")
pinecone_vector_store = PineconeVectorStore(pinecone_index=pinecone_index, namespace="claude-code-docs")
index = VectorStoreIndex.from_vector_store(vector_store=pinecone_vector_store, embed_model=embed_model)

retriever = index.as_retriever(similarity_top_k=3)
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.35)


def answer_semantic(question):
    nodes = retriever.retrieve(question)
    filtered = postprocessor.postprocess_nodes(nodes)
    if not filtered:
        return "לא נמצא מידע רלוונטי מספיק בקבצי התיעוד."
    response = response_synthesizer.synthesize(question, nodes=filtered)
    return str(response)


# ============================================================
# שלב 5: ה-Router המלא - קריאת LLM אחת בלבד לכל שאלה
# ============================================================
def answer_question(question):
    query = generate_query(question)
    print(f"[Router] route={query.route} category={query.category} keyword={query.keyword}")

    if query.route == "structured":
        matched_items = run_query(query)
        return answer_structured(question, matched_items)
    else:
        return answer_semantic(question)


if __name__ == "__main__":
    print("\n--- שאלה מובנית עם קטגוריה וסינון ---")
    print(answer_question("What rules are related to caching?"))