# 🌤️ Weather Israel MCP

MCP Server שמספק ל-LLM גישה לתחזית מזג אוויר עדכנית בערים בישראל, באמצעות שליטה אוטומטית בדפדפן (Playwright) - ולא דרך API קונבנציונלי.

## 🎯 מטרת הפרויקט

הפרויקט נועד להתנסות בפיתוח MCP Server עצמאי, ובהוספת יכולות שליטה בדפדפן ל-LLM. במקום להתחבר ל-API רשמי של מזג אוויר, ה-Server "מדמה" משתמש אנושי: פותח דפדפן, מזין שם עיר באתר weather2day.co.il, בוחר אותה מרשימה נפתחת, וקורא את תוכן הדף בעצמו.

## 🧩 מבנה הפרויקט

- `weather_Israel.py` - MCP Server עם 4 כלים (Tools) לשליטה בדפדפן וחילוץ תחזית
- `client.py` - MCP Client גנרי, מתחבר לכל שרת MCP
- `host.py` - Host: צ'אט טרמינל שמחבר בין המשתמש, ה-LLM (Gemini) וה-MCP Server
- `weather_USA.py` - MCP Server נוסף לדוגמה (תחזית ארה"ב דרך API רשמי)

## 🛠️ הכלים (Tools) שממומשים ב-weather_Israel.py

1. **`open_weather_forecast_israel`** - פותחת דפדפן ומנווטת לדף התחזית
2. **`enter_weather_forecast_city_israel`** - מזינה שם עיר בשדה החיפוש
3. **`select_weather_forecast_city_israel`** - בוחרת את הפריט הראשון ברשימה הנפתחת
4. **`get_weather_forecast_text_israel`** - מחלצת מהדף את הטמפרטורה, הרוח, הלחות ועוד, ומספקת אותם ל-LLM

## 🚀 איך מריצים

### דרישות מוקדמות
- Python מותקן
- מפתח API של Gemini (חינמי, ללא כרטיס אשראי) מ-[aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### שלבים

1. שכפלו/הורידו את הריפו למחשב

2. צרו קובץ `.env` בתיקיית הפרויקט עם המפתח:

GEMINI_API_KEY=your-api-key-here

3. התקינו את התלויות:
```powershell
   uv sync
```

4. התקינו דפדפן Chromium עבור Playwright:
```powershell
   uv run playwright install chromium
```

5. הריצו את הפרויקט:
```powershell
   uv run host.py
```

6. שאלו בצ'אט שבטרמינל שאלה על מזג האוויר בעיר בישראל.

## 💬 דוגמאות לשאלות שה-Agent יודע לענות

- מה מזג האוויר בירושלים?
- מה הטמפרטורה בתל אביב עכשיו?
- מה מצב הרוח והלחות בחיפה?
- איך מזג האוויר בבאר שבע היום?

## ⚙️ טכנולוגיות

- **MCP SDK** - הפרוטוקול לחשיפת Tools ל-LLM
- **Playwright** - אוטומציית דפדפן
- **Google Gemini API** - המודל שמנהל את השיחה ומחליט מתי להפעיל כלים