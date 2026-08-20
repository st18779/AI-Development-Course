from dotenv import load_dotenv
load_dotenv()

from langgraph.checkpoint.sqlite import SqliteSaver
from agent import build_graph
from tts import text_to_speech

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = build_graph().compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "talk-1"}}
    state = {
        "topic": "Why sleep matters for creativity",
        "plan": "", "context": "", "talk": "",
        "critique": "", "needs_revision": False, "revision_count": 0,
    }

    result = graph.invoke(state, config=config)

    if "__interrupt__" in result:
        print("\n=== WAITING FOR APPROVAL ===")
        print(result["__interrupt__"][0].value["talk"])
        answer = input("\nApprove? (y/n): ")
        if answer.lower() == "y":
            from langgraph.types import Command
            final = graph.invoke(Command(resume=True), config=config)
            print("\n=== FINAL TALK ===")
            print(final.get("talk", ""))
            text_to_speech(final["talk"], "ted_talk.mp3")
            print("Saved to ted_talk.mp3")
        else:
            print("Not approved - stopping.")