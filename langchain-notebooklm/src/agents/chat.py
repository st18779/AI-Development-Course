import os
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from core.store import SourceStore, store
from core.sources import format_docs
from firecrawl import Firecrawl

_CHECKPOINTER = InMemorySaver()

@dataclass
class Answer:
    text: str
    sources: list[str]
   


MODEL = os.getenv("NOTEBOOKLM_CHAT_MODEL", "google_genai:gemini-flash-latest")
SYSTEM_PROMPT = """You are a helpful research assistant for NotebookLM,
a tool that helps users understand and work with their source documents.

You have access to the following tools:
- search_sources: ALWAYS use this FIRST when the user asks any question 
  that could relate to their uploaded documents - even if you think you 
  already know the answer. The user's documents may contradict or override 
  your general knowledge, and answers must be grounded in their sources 
  whenever possible.
- list_sources: use this to see which sources are currently available.
- get_source: use this to retrieve the full content of a specific source,
  once you know its id.

If the sources don't contain relevant information, say so explicitly 
rather than falling back to your general knowledge silently.

Be concise and clear in your answers."""

FIRECRAWL_CLIENT = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))

def _make_tools(store: SourceStore):

    @tool
    def search_sources(query: str) -> str:
        """Find passages in the active sources that are relevant to a query.
        Use this whenever the user asks a question about the content of their documents."""
        docs = store.search(query=query)
        if not docs:
            return "No relevant documents found in the active sources"
        return format_docs(docs)

    @tool
    def list_sources() -> str:
        """List all available sources in the notebook, including their id, name and whether they are active."""
        sources = store.list()
        if not sources:
            return "No sources have been added yet"
        lines = [f"- id: {s.id}, name: {s.name}, active: {s.active}" for s in sources]
        return "\n".join(lines)

    @tool
    def get_source(source_id: str) -> str:
        """Get the full content of a specific source by its id.
        Use this when the user asks about a specific document by name or id."""
        source = store.get(source_id)
        if source is None:
            return f"No source found with id {source_id}"
        return f"(source: {source.name})\n{source.content}"

   
    @tool
    def web_search(query: str) -> str:
        """Search the web for information not found in the uploaded sources.
        Use this when the user asks about something that isn't covered by
        the documents they've uploaded, or asks for current/external information."""
        results = FIRECRAWL_CLIENT.search(query, limit=5)
        if not results.web:
            return "No web results found"
        blocks = []
        for i, r in enumerate(results.web, start=1):
            blocks.append(f"[{i}] {r.title}\n{r.url}\n{r.description}")
        return "\n\n".join(blocks)
    @tool
    def web_scrape(url: str) -> str:
        """Fetch the full text content of a specific web page by its URL.
        Use this after web_search, when you need the complete content of a
        specific result rather than just its summary."""
        try:
            result = FIRECRAWL_CLIENT.scrape(url, formats=["markdown"])
        except Exception as e:
            return f"Could not scrape {url}: {e}"
        if not result.markdown:
            return f"Could not extract content from {url}"
        return result.markdown
    @tool
    def web_crawl(url: str, limit: int = 5) -> str:
        """Crawl a website starting from a URL and extract content from multiple
        linked pages. Use this when the user wants a broad overview of an entire
        site or section, not just one page."""
        try:
            result = FIRECRAWL_CLIENT.crawl(url, limit=limit)
        except Exception as e:
            return f"Could not crawl {url}: {e}"
        if not result.data:
            return f"No pages found when crawling {url}"
        blocks = []
        for i, page in enumerate(result.data, start=1):
            title = page.metadata.get("title", "untitled") if page.metadata else "untitled"
            content = (page.markdown or "")[:1000]
            blocks.append(f"[{i}] {title}\n{content}")
        return "\n\n".join(blocks)
    
    return [search_sources, list_sources, get_source, web_search, web_scrape, web_crawl]   

def answer(question: str, thread_id: str) -> Answer:
    agent = create_agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=_CHECKPOINTER,
        tools=_make_tools(store),
    )

    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}, config=config
    )

    text = result["messages"][-1].text
    return Answer(text=text, sources=[])
