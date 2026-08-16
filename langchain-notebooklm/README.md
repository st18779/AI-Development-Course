# 📓 langchain-notebooklm

A **NotebookLM-style grounded research assistant** — built as a learning project for
**LangChain v1**. The app lets you upload your own documents and chat with them using
Retrieval-Augmented Generation (RAG), and can also autonomously search, scrape, and
crawl the web when the answer isn't in your sources.

---

## ✨ What it does

This is a single conversational **Agent** that decides, on its own, how to answer each
question:

- If the answer is likely inside your uploaded documents → it searches your sources
  (RAG) and grounds its answer in them.
- If the answer requires external / up-to-date information → it autonomously searches
  the web, picks the most relevant result, and scrapes the full content before
  answering.
- It keeps track of the conversation using short-term memory, so it remembers earlier
  turns in the same chat.

---

## 🧠 Agent tools

The agent has access to six tools, and chooses which ones to use (and in what order)
for each question:

| Tool | Purpose |
|---|---|
| `search_sources` | Semantic search over the chunks of your uploaded documents |
| `list_sources` | Lists all sources currently available in the notebook |
| `get_source` | Retrieves the full content of a specific source by id |
| `web_search` | Searches the web for information not covered by your documents |
| `web_scrape` | Fetches the full text content of a specific web page |
| `web_crawl` | Crawls a website starting from a URL, extracting content from multiple pages |

---

## 🛠️ Stack

| Component | Technology |
|---|---|
| Agent framework | [LangChain](https://www.langchain.com/) v1 (`create_agent`) |
| Chat model | Google Gemini (`google_genai:gemini-flash-latest` by default) |
| Embeddings | Cohere (`embed-multilingual-v3.0`) |
| Vector store | LangChain `InMemoryVectorStore` |
| Web search / scrape / crawl | [Firecrawl](https://www.firecrawl.dev/) |
| Memory | LangGraph `InMemorySaver` (checkpointer) |
| Backend | FastAPI |
| Frontend | Static HTML/JS/CSS client, no build step |

Everything is provider-agnostic via environment variables — see [`.env.example`](.env.example).
To use a different chat or embedding model, just change the relevant variable — no code
changes needed.

---

## 📁 Project structure

```
notebooklm-starter/
├── client/                     # Web client — static HTML/JS/CSS
├── src/
│   ├── agents/
│   │   └── chat.py             # The conversational agent (tools + memory)
│   ├── core/
│   │   ├── store.py            # SourceStore — manages documents + vector index
│   │   └── sources.py          # Chunking and formatting helpers
│   ├── api/
│   │   ├── app.py              # FastAPI endpoints
│   │   ├── serve.py            # Server entry point
│   │   ├── services.py         # Service layer between API and agent
│   │   └── schemas.py          # Pydantic request/response models
│   └── app.py                  # CLI script to test the agent without the server
└── .env.example                # Environment variable template
```

---

## 🚀 Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Then fill in your API keys in `.env`:

```dotenv
# --- Chat model (Google Gemini) ---
GOOGLE_API_KEY=your-gemini-key-here

# --- Embeddings (Cohere) ---
COHERE_API_KEY=your-cohere-key-here

# --- Web search / scrape / crawl (Firecrawl) ---
FIRECRAWL_API_KEY=your-firecrawl-key-here
```

| Key | Where to get it |
|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| `COHERE_API_KEY` | [Cohere Dashboard](https://dashboard.cohere.com/) |
| `FIRECRAWL_API_KEY` | [Firecrawl Dashboard](https://www.firecrawl.dev/) |

### 3. Run the app

```bash
uv run notebooklm-serve
```

Then open **http://127.0.0.1:4040** in your browser.

### CLI (no server, quick sanity check)

```bash
uv run src/app.py
```

This runs a single hard-coded question through the agent and prints the answer to the
terminal — useful for confirming the model and tools are wired up correctly before
touching the UI.

---

## 💬 How to use it

1. **Add a source** — paste text or upload a `.txt` / `.md` file in the *Sources* panel.
2. **Toggle sources active/inactive** — retrieval is scoped to whichever sources are
   currently active.
3. **Ask a question** in the *Chat* panel:
   - Ask about your uploaded documents → the agent searches and grounds its answer in
     them.
   - Ask about something external (news, current events, general web content) → the
     agent autonomously searches, and scrapes the web for you.
4. **View or remove sources** any time from the *Sources* panel.

---

## 🧩 How the RAG pipeline works

1. **Chunking** — each source is split into overlapping chunks (`chunk_size=800`,
   `chunk_overlap=120`) using LangChain's `RecursiveCharacterTextSplitter`, preserving
   context across chunk boundaries.
2. **Embedding** — each chunk is embedded with Cohere's multilingual embedding model.
3. **Indexing** — embeddings are stored in an in-memory vector store, tagged with
   `source_id` so retrieval can be scoped to active sources only.
4. **Retrieval** — when the agent calls `search_sources`, it performs a semantic
   similarity search filtered to active sources, and formats the results with clear
   source attribution for the model to reason over.

---

## 🌐 How the web research pipeline works

1. `web_search` — searches the web and returns a list of ranked results (title, URL,
   short description).
2. The agent autonomously evaluates which result looks most relevant.
3. `web_scrape` — fetches the full text of the chosen page (converted to clean
   Markdown) so the agent can answer with real detail, not just a snippet.
4. `web_crawl` — for broader questions, the agent can crawl a whole site starting from
   a URL and pull content from multiple linked pages at once.

All three tools handle failures gracefully (e.g. a page that can't be scraped) and
report the issue back to the agent as plain text, so a single failed request doesn't
crash the app — the agent can simply try a different source instead.

---

## 📌 Notes on scope

This project was built in stages, following the course curriculum:

| Stage | Feature | Status |
|---|---|---|
| 1 | Basic conversational agent | ✅ Done |
| 2 | RAG over uploaded documents | ✅ Done |
| 3 | Web search / scrape / crawl via Firecrawl | ✅ Done |
| Bonus | Human-in-the-loop source approval | ⏳ Not implemented in this version |

---

## 📚 References

- [LangChain Docs](https://docs.langchain.com/)
- [`create_agent` in LangChain](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Firecrawl](https://www.firecrawl.dev/)