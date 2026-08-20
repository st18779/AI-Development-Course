import os
from typing import TypedDict, Literal
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from pydantic import BaseModel, Field


MODEL = os.getenv("STUDIO_MODEL", "google_genai:gemini-flash-latest")
llm = init_chat_model(MODEL)


class TalkState(TypedDict):
    topic: str
    plan: str
    context: str
    talk: str
    critique: str
    needs_revision: bool
    revision_count: int


class CritiqueResult(BaseModel):
    """Structured feedback on a talk draft."""
    needs_revision: bool = Field(description="True if the talk needs another revision pass")
    feedback: str = Field(description="Specific, actionable feedback for improving the talk")


def _extract_text(response) -> str:
    if isinstance(response.content, str):
        return response.content
    parts = []
    for block in response.content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block["text"])
        elif isinstance(block, str):
            parts.append(block)
    return "".join(parts)


def plan_talk(state: TalkState) -> dict:
    """Node: creates a rough outline/plan for the talk based on the topic."""
    prompt = f"""You are planning a TED talk on the topic: "{state['topic']}"

Create a brief outline (3-5 bullet points) covering the key angles this talk
should explore. Keep it concise - this is just a planning step."""
    response = llm.invoke(prompt)
    return {"plan": _extract_text(response)}


def gather_context(state: TalkState) -> dict:
    """Node: gathers supporting facts/context for the talk, based on the plan."""
    prompt = f"""You are researching background material for a TED talk.

Topic: "{state['topic']}"
Outline: {state['plan']}

Provide relevant facts, examples, or supporting details for each point in the
outline. Be specific and concrete - this will be used as raw material for
writing the talk."""
    response = llm.invoke(prompt)
    return {"context": _extract_text(response)}


def write_talk(state: TalkState) -> dict:
    """Node: writes (or rewrites) a draft of the talk."""
    if state.get("critique"):
        # This is a revision pass - incorporate the feedback
        prompt = f"""Revise this TED talk script based on the feedback below.

Current script:
{state['talk']}

Feedback to address:
{state['critique']}

Write the full, improved script (around 500-700 words)."""
    else:
        prompt = f"""You are writing a TED talk script.

Topic: "{state['topic']}"
Outline: {state['plan']}
Supporting material: {state['context']}

Write a complete first-draft script for this talk (around 500-700 words).
Give it a strong opening hook, a clear structure following the outline, and
a memorable closing line. Write it as if it will be spoken aloud."""
    response = llm.invoke(prompt)
    return {"talk": _extract_text(response)}


def critique_script(state: TalkState) -> dict:
    """Node: critiques the current draft and decides if it needs revision."""
    structured_llm = llm.with_structured_output(CritiqueResult)
    prompt = f"""You are a professional TED talk script editor. Review this draft:

{state['talk']}

Judge whether it needs another revision pass. Only ask for revision for real
issues (weak hook, unclear structure, pacing problems) - do not nitpick minor
wording. If it's good, mark needs_revision as False."""
    result: CritiqueResult = structured_llm.invoke(prompt)
    revision_count = state.get("revision_count", 0)
    return {
        "critique": result.feedback,
        # Cap revisions at 2 rounds so it can't loop forever
        "needs_revision": result.needs_revision and revision_count < 2,
        "revision_count": revision_count + 1,
    }


def approve_for_audio(state: TalkState) -> dict:
    """Node: pauses and waits for human approval before generating audio."""
    decision = interrupt({
        "question": "Approve this talk for audio generation?",
        "talk": state["talk"],
    })
    return {}  # the resume value is handled by the caller; nothing to update here


def route_after_critique(state: TalkState) -> Literal["write_talk", "approve_for_audio"]:
    """Conditional edge: loop back to writing if revision is needed, else proceed."""
    if state.get("needs_revision"):
        return "write_talk"
    return "approve_for_audio"


def build_graph():
    graph = StateGraph(TalkState)

    graph.add_node("plan_talk", plan_talk)
    graph.add_node("gather_context", gather_context)
    graph.add_node("write_talk", write_talk)
    graph.add_node("critique_script", critique_script)
    graph.add_node("approve_for_audio", approve_for_audio)

    graph.add_edge(START, "plan_talk")
    graph.add_edge("plan_talk", "gather_context")
    graph.add_edge("gather_context", "write_talk")
    graph.add_edge("write_talk", "critique_script")
    graph.add_conditional_edges("critique_script", route_after_critique)
    graph.add_edge("approve_for_audio", END)

    return graph