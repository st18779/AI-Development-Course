from dotenv import load_dotenv
load_dotenv()

from podcast_agent import build_podcast_graph
from tts import text_to_speech

graph = build_podcast_graph().compile()
result = graph.invoke({"topic": "The future of remote work", "subtopics": [], "segments": [], "script": ""})

print(result["script"])
text_to_speech(result["script"], "podcast.mp3")