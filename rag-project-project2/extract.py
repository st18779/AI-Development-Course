import os
import json
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# שלב 1: הגדרת הסכמה (Schema) - לפחות 3 סוגי פריטים
# ============================================================
from pydantic import BaseModel, Field
from typing import List


class Decision(BaseModel):
    id: str = Field(description="מזהה ייחודי, לדוגמה dec-001")
    title: str = Field(description="כותרת קצרה להחלטה")
    summary: str = Field(description="תיאור קצר של ההחלטה")
    file: str = Field(description="שם קובץ המקור")


class Rule(BaseModel):
    id: str = Field(description="מזהה ייחודי, לדוגמה rule-001")
    rule: str = Field(description="נוסח הכלל/ההנחיה")
    scope: str = Field(description="תחום הכלל, לדוגמה: testing, api, deployment")
    file: str = Field(description="שם קובץ המקור")


class Warning(BaseModel):
    id: str = Field(description="מזהה ייחודי, לדוגמה warn-001")
    area: str = Field(description="תחום האזהרה, לדוגמה: auth, database")
    message: str = Field(description="תוכן האזהרה")
    severity: str = Field(description="חומרה: low / medium / high")
    file: str = Field(description="שם קובץ המקור")


class ExtractedData(BaseModel):
    decisions: List[Decision]
    rules: List[Rule]
    warnings: List[Warning]


print("Schema defined:", ExtractedData.model_json_schema()["title"])


# ============================================================
# שלב 2: טעינת כל הקבצים וחיבורם לפרומפט אחד
# ============================================================
from llama_index.core import SimpleDirectoryReader

reader = SimpleDirectoryReader(input_dir="docs_sources/claude_code")
documents = reader.load_data()

combined_text = ""
for doc in documents:
    file_name = doc.metadata.get("file_name", "unknown")
    combined_text += f"\n\n===== FILE: {file_name} =====\n{doc.text}"

print(f"Combined text length: {len(combined_text)} characters, from {len(documents)} files")


# ============================================================
# שלב 3: חילוץ מובנה - קריאת LLM אחת עם כל הטקסט
# ============================================================
from llama_index.llms.cohere import Cohere
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")

prompt_template = """\
You are analyzing technical documentation files from a software project.
Extract structured items of 3 types: decisions, rules, warnings.

For each item, include which FILE it came from (use the file name shown after "FILE:").
Only extract items that are clearly stated in the text - do not invent information.
If a category has no relevant items, return an empty list for it.

Documentation:
{docs_text}

{format_instructions}
"""

output_parser = PydanticOutputParser(ExtractedData)

program = LLMTextCompletionProgram.from_defaults(
    output_parser=output_parser,
    prompt_template_str=prompt_template,
    llm=llm,
    verbose=True,
)

result = program(docs_text=combined_text, format_instructions=output_parser.get_format_string())

print(f"\nExtracted: {len(result.decisions)} decisions, {len(result.rules)} rules, {len(result.warnings)} warnings")


# ============================================================
# שלב 4: שמירה לקובץ JSON
# ============================================================
os.makedirs("data", exist_ok=True)
with open("data/extracted_data.json", "w", encoding="utf-8") as f:
    json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

print("Saved to data/extracted_data.json")