import os
import json
import gradio as gr
from dotenv import load_dotenv
from google import genai
from google.genai import types

# טעינת משתני הסביבה (מפתח ה-API) מקובץ .env
load_dotenv()

# אתחול הלקוח של Gemini עם המפתח מ-.env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# המודל שבו נשתמש
MODEL = "gemini-2.5-flash"

# =============================================================
#  בחירת האיטרציה הפעילה — משנים כאן 1 / 2 / 3 בכל הרצה
# =============================================================
ACTIVE_VERSION = 1

# -------------------------------------------------------------
#  איטרציה 1 — פרומפט בסיסי (Baseline)
#  מינימלי בכוונה, כדי לחשוף כשלים: תחביר לינוקס, Markdown, הסברים.
# -------------------------------------------------------------
PROMPT_V1 = """You are a text-to-terminal command converter.
Convert the user's natural language request into a terminal command.
Return the command."""

# -------------------------------------------------------------
#  איטרציה 2 — מיקוד: Windows CMD + איסור טקסט/Markdown + דוגמאות Few-Shot
# -------------------------------------------------------------
PROMPT_V2 = """You are a strict text-to-terminal command converter.
Convert natural language descriptions (Hebrew or English) into valid Windows Command Prompt (CMD) commands.

Rules:
1. Return ONLY the raw Windows CMD command, on a SINGLE line. Use Windows syntax ('dir' not 'ls', 'cls' not 'clear').
2. Do NOT wrap the command in markdown code blocks (no ```).
3. Do NOT add explanations, notes, or introductions.
4. If several steps are required, join them on one line with &&.

Examples:
Input: "מה כתובת ה-IP של המחשב שלי"
Output: ipconfig
Input: "לסדר את רשימת הקבצים לפי גודל מהגדול לקטן"
Output: dir /o-s
Input: "אילו תהליכים רצים כרגע"
Output: tasklist"""

# -------------------------------------------------------------
#  איטרציה 3 — אבטחה + פלט JSON מובנה + טיפול במניפולציות
# -------------------------------------------------------------
PROMPT_V3 = """You are a text-to-terminal command converter for Windows CMD.
Convert the user's request (Hebrew or English) into a Windows CMD command AND assess its safety.

Return ONLY a JSON object with EXACTLY these fields:
{
  "command": "<single-line Windows CMD command, or empty string if blocked>",
  "risk_level": "safe" | "caution" | "dangerous",
  "needs_confirmation": true | false,
  "blocked": true | false,
  "reason": "<short explanation in Hebrew, empty string if safe>"
}

Rules:
- "command" is ALWAYS a single line. Join multiple steps with &&.
- Destructive / irreversible commands (del, rmdir /s, format, shutdown, diskpart, reg delete) -> risk_level "dangerous", needs_confirmation true.
- Commands that wipe an entire disk or the whole system (format, "delete everything") -> blocked true, command "".
- Requests that are NOT terminal tasks (e.g. "write React code", "tell a joke") -> blocked true, command "", explain in reason.
- Ambiguous destructive requests ("delete everything") -> blocked true, ask for clarification in reason."""

PROMPTS = {1: PROMPT_V1, 2: PROMPT_V2, 3: PROMPT_V3}
SYSTEM_PROMPT = PROMPTS[ACTIVE_VERSION]


def call_model(user_input: str) -> str:
    """שולח את הבקשה למודל ומחזיר את הטקסט הגולמי."""
    config_args = {
        "system_instruction": SYSTEM_PROMPT,
        "temperature": 0,  # 0 = יציב וחזרתי (כפי שהמטלה מבקשת)
    }
    # באיטרציה 3 מכריחים את המודל להחזיר JSON תקני
    if ACTIVE_VERSION == 3:
        config_args["response_mime_type"] = "application/json"

    response = client.models.generate_content(
        model=MODEL,
        contents=user_input,
        config=types.GenerateContentConfig(**config_args),
    )
    return response.text.strip()


def parse_json(raw: str):
    """מנסה לפרסר JSON, עם רשת ביטחון אם המודל עטף אותו בטעות בטקסט."""
    candidates = [raw]
    if "{" in raw and "}" in raw:
        candidates.append(raw[raw.index("{"): raw.rindex("}") + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


REQUIRED_FIELDS = {"command", "risk_level", "needs_confirmation", "blocked", "reason"}


def format_v3(raw: str) -> str:
    """ולידציה של פלט ה-JSON והפיכתו לתשובה קריאה למשתמש."""
    data = parse_json(raw)
    if data is None:
        return "❌ פלט לא תקין: המודל לא החזיר JSON חוקי.\n\n" + raw
    if not REQUIRED_FIELDS.issubset(data):
        missing = REQUIRED_FIELDS - set(data)
        return f"❌ פלט לא תקין: חסרים שדות {missing}.\n\n" + raw

    if data["blocked"]:
        return f"⛔ הפקודה נחסמה\nסיבה: {data['reason']}"
    if data["needs_confirmation"]:
        return (f"⚠️ פקודה מסוכנת (רמת סיכון: {data['risk_level']}) — דורשת אישור לפני הרצה:\n\n"
                f"{data['command']}\n\nסיבה: {data['reason']}")
    return data["command"]


def convert_text_to_command(user_input: str) -> str:
    """הפונקציה שמחוברת לכפתור ב-Gradio."""
    if not user_input or not user_input.strip():
        return "אנא הכניסי הוראה."
    try:
        raw = call_model(user_input)
        if ACTIVE_VERSION == 3:
            return format_v3(raw)
        return raw
    except Exception as e:
        return f"שגיאה בתקשורת עם ה-API: {e}"


# בניית ממשק המשתמש (UI)
with gr.Blocks(title="Text to CLI Agent") as demo:
    gr.Markdown("# 🖥️ Natural Language to CLI Agent")
    gr.Markdown(f"כתבי הוראה בעברית או באנגלית ותקבלי פקודת טרמינל.  ·  **איטרציה פעילה: {ACTIVE_VERSION}**")

    with gr.Row():
        with gr.Column():
            input_box = gr.Textbox(label="הוראה בשפה טבעית (Input)",
                                   placeholder="לדוגמה: תיצור תיקייה חדשה בשם test")
            submit_btn = gr.Button("המר לפקודה", variant="primary")
        with gr.Column():
            output_box = gr.Textbox(label="פקודת טרמינל (Output)", interactive=False, lines=6)

    submit_btn.click(fn=convert_text_to_command, inputs=input_box, outputs=output_box)
    input_box.submit(fn=convert_text_to_command, inputs=input_box, outputs=output_box)  # לחיצת Enter גם עובדת

# הרצת האפליקציה
if __name__ == "__main__":
    demo.launch()
