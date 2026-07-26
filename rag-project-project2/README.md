# 📚 RAG System for Agentic Coding Documentation

A Retrieval-Augmented Generation (RAG) system that indexes markdown documentation
produced by AI coding tools (Claude Code) and answers natural-language questions
about it — combining semantic search with a structured data layer for accurate,
comprehensive answers.

## 🎯 Overview

AI coding tools like Claude Code, Cursor, and Kiro continuously generate
documentation (`.md` files) while working: architecture decisions, rules,
warnings, and plans. This project unifies that documentation into a single
knowledge base, allowing developers — especially new team members — to quickly
understand a project's context and the reasoning behind its technical decisions.

## ✨ Features

- **Semantic search** over project documentation using vector embeddings
- **Event-driven workflow** architecture with validation and automatic retry
- **Structured data extraction** (decisions, rules, warnings) for full-coverage,
  list-style queries
- **Smart routing** that automatically chooses between semantic search and
  structured retrieval based on the question
- **Interactive chat UI** built with Gradio

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| RAG Framework | [LlamaIndex](https://www.llamaindex.ai/) |
| Embeddings & LLM | [Cohere](https://cohere.com/) (`embed-english-v3.0`, `command-r-08-2024`) |
| Vector Database | [Pinecone](https://www.pinecone.io/) |
| UI | [Gradio](https://www.gradio.app/) |
| Data Validation | [Pydantic](https://docs.pydantic.dev/) |

## 📁 Project Structure

```
rag-project/
├── docs_sources/
│   └── claude_code/        # Source markdown files
├── data/
│   └── extracted_data.json # Structured data extracted in stage 3
├── prepare.py               # Stage 1 — Loading, chunking, embedding, indexing
├── agent.py                  # Stage 1 — Gradio interface (MVP)
├── workflow_agent.py         # Stage 2 — Event-driven workflow + Gradio
├── extract.py                 # Stage 3 — Structured data extraction
├── router.py                  # Stage 3 — Routing between search strategies
├── pyproject.toml
└── .env.example
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Cohere API key](https://dashboard.cohere.com/) (free trial available)
- [Pinecone API key](https://app.pinecone.io/) (free tier available)

### Installation

```bash
uv add llama-index python-dotenv llama-index-embeddings-cohere \
       llama-index-vector-stores-pinecone pinecone-client cohere \
       llama-index-llms-cohere gradio pydantic
```

### Configuration

Create a `.env` file (see `.env.example`):

```env
COHERE_API_KEY=your_cohere_key
PINECONE_API_KEY=your_pinecone_key
```

### Build the knowledge base

Run once to prepare the data:

```bash
uv run prepare.py    # builds the vector index in Pinecone
uv run extract.py    # extracts structured data into data/extracted_data.json
```

### Run the app

```bash
uv run workflow_agent.py
```

Open the local URL printed in the terminal (default: `http://127.0.0.1:7860`).

You can also run `agent.py` for the basic MVP version (no workflow), or
`router.py` directly to test the routing layer from the terminal.

## 💬 Example Questions

**Factual questions (semantic search):**
- "What database was chosen for the project?"
- "Why was MongoDB chosen for the product catalog?"
- "How is the system tested?"

**List-style questions (structured data layer):**
- "List all the technical decisions made in the project."
- "What rules are related to caching?"

**Edge cases:**
- Empty questions are rejected immediately without an API call.
- Questions unrelated to the documentation trigger an expanded retry search,
  and return an honest "not found" message instead of a hallucinated answer.

## 🏗️ Architecture

The project was built in three progressive stages:

1. **Semantic MVP** — Loading → Chunking → Embedding → Indexing, with a
   Retrieve → Postprocess → Synthesize query flow.
2. **Event-Driven Workflow** — the same capability rebuilt as a Workflow with
   discrete Steps and Events, including input validation and automatic
   retry routing.
3. **Structured Extraction + Routing** — a structured JSON layer extracted
   from the documentation, with an LLM-powered router that builds a query
   against the schema and chooses the right retrieval strategy per question.