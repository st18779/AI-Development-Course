import os
from typing import TypedDict, Annotated
from operator import add
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

MODEL = os.getenv("STUDIO_MODEL", "google_genai:gemini-flash-latest")
llm = init_chat_model(MODEL)


def _extract_text(response) -> str:
    if isinstance(response.content, str):
        return response.content
    return "".join(b["text"] for b in response.content if isinstance(b, dict) and b.get("type") == "text")


class PodcastState(TypedDict):
    topic: str
    subtopics: list[str]
    segments: Annotated[list[str], add]  # each parallel branch appends here
    script: str


class SegmentState(TypedDict):
    subtopic: str


def plan_subtopics(state: PodcastState) -> dict:
    """Node: breaks the topic into 3 parallel subtopics to research."""
    prompt = f"""Break down this podcast topic into exactly 3 distinct
subtopics/angles to research in parallel: "{state['topic']}"
Return just the 3 subtopics, one per line, no numbering."""
    response = llm.invoke(prompt)
    subtopics = [s.strip("- ").strip() for s in _extract_text(response).split("\n") if s.strip()]
    return {"subtopics": subtopics[:3]}


def fan_out(state: PodcastState):
    """Conditional edge that dispatches parallel work with Send."""
    return [Send("write_segment", {"subtopic": t}) for t in state["subtopics"]]


def write_segment(state: SegmentState) -> dict:
    """Node: writes one podcast segment for a single subtopic (runs in parallel)."""
    prompt = f"""Write a ~150-word podcast segment about: {state['subtopic']}
Conversational tone, as if two hosts are discussing it."""
    response = llm.invoke(prompt)
    return {"segments": [_extract_text(response)]}


def combine_script(state: PodcastState) -> dict:
    """Node: combines all parallel segments into one script."""
    script = "\n\n---\n\n".join(state["segments"])
    return {"script": script}


def build_podcast_graph():
    graph = StateGraph(PodcastState)
    graph.add_node("plan_subtopics", plan_subtopics)
    graph.add_node("write_segment", write_segment)
    graph.add_node("combine_script", combine_script)

    graph.add_edge(START, "plan_subtopics")
    graph.add_conditional_edges("plan_subtopics", fan_out, ["write_segment"])
    graph.add_edge("write_segment", "combine_script")
    graph.add_edge("combine_script", END)

    return graph