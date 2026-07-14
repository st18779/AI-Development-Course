# 🖥️ Natural Language to Windows CMD Agent

An iterative, safety-conscious AI Agent built with Python, Google GenAI SDK, and Gradio. This project demonstrates the power of systematic Prompt Engineering by evolving a simple text-to-terminal model into a robust, structured, and secure Windows Command Prompt (CMD) assistant.

---

## 📊 Experiment Tracking & Evaluation

The complete prompt engineering process, including test cases, model outputs, and evaluation metrics across all three iterations, is documented in detail:

👉 **[Click Here to View the Google Sheet Evaluation Document](https://docs.google.com/spreadsheets/d/1vCSapzUc_zQjFzzgU0N59mlLizsLtVPbvErIHKeWk_M/edit?gid=299312748#gid=299312748)**

---

## 🚀 Evolving Prompt Iterations

### 🔹 Iteration 1: Baseline (MVP)
* **Goal:** A simple prototype to map natural language to CLI commands.
* **Findings:** Exposed formatting issues (e.g., unnecessary explanations, wrapping code in markdown code blocks) and OS syntax mismatches (mixing Linux and Windows commands).

### 🔹 Iteration 2: Windows CMD Focus & Few-Shot Learning
* **Goal:** Force strict Windows CMD syntax (e.g., `dir` instead of `ls`) on a single line, with zero extra conversational text.
* **Method:** Structured rules and few-shot examples in Hebrew and English.

### 🔹 Iteration 3: Safety Guardrails & Structured JSON Output
* **Goal:** Address security vulnerabilities and non-terminal requests while maintaining a reliable output format.
* **Method:** Configured the LLM (`gemini-2.5-flash`) to output structured JSON with safe/unsafe categorizations. Irreversible destructive commands (like `format` or `del *`) are flagged or blocked, requiring confirmation prior to presentation, with safety reasons provided in Hebrew.

---

## 🛠️ Project Structure

```text
Prompt Engineering-project1/
├── .env-example          # Template for environment variables
├── .gitignore            # Tells git which files to ignore (like your secret .env)
├── .python-version       # Managed Python version
├── main.py               # The core Gradio application & SDK integration
├── pyproject.toml        # Project dependencies managed by uv
├── README.md             # This documentation file
└── uv.lock               # Lockfile for precise package versioning
```

---

## ⚙️ Setup & Installation

This project is built and managed using `uv`, an extremely fast Python package and project manager.

### 1. Clone the repository

```bash
git clone https://github.com/st18779/AI-Development-Course.git
cd AI-Development-Course/Prompt Engineering-project1
```

### 2. Configure Environment Variables

Copy the template `.env-example` to create your local `.env` file and insert your Google Gemini API key:

```bash
cp .env-example .env
```

Open the `.env` file and set your key:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Run the Application

Using `uv`, you can spin up the Gradio interface instantly without manually managing virtual environments:

```bash
uv run main.py
```

Once started, open the local URL (usually `http://127.0.0.1:7860`) in your browser to interact with the Agent.

---

## 💡 Tech Stack

* **Language:** Python 3.12+
* **Environment & Dependency Manager:** [uv](https://github.com/astral-sh/uv)
* **AI SDK:** `google-genai` (using `gemini-2.5-flash`)
* **Web UI:** [Gradio](https://gradio.app/)
