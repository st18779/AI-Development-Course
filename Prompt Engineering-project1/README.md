# 🖥️ Natural Language to Windows CMD Agent

An iterative, safety-conscious AI Agent built with Python, the Google GenAI SDK, and Gradio. This project demonstrates the power of systematic Prompt Engineering by evolving a simple text-to-terminal model into a robust, structured, and secure Windows Command Prompt (CMD) assistant.

---

## 📊 Experiment Tracking & Evaluation
The complete prompt engineering process, including test cases, model outputs, and evaluation metrics across all three iterations, is documented in detail:

👉 **[Click Here to View the Google Sheet Evaluation Document](https://docs.google.com/spreadsheets/d/1vCSapzUc_zQjFzzgU0N59mlLizsLtVPbvErIHKeWk_M/edit?usp=sharing)**

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
