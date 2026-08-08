# 🌤️ Weather Israel MCP

An independent MCP Server that fetches live Israeli weather forecasts by driving a real browser with Playwright, instead of a conventional API. 
The system lets you chat with an LLM (a large language model) and get up-to-date weather answers for any city in Israel.

## 🎯 Project Goal

Practicing independent MCP Server development, and gaining hands-on experience giving an LLM browser-control abilities through Playwright - simulating a real user browsing a website with no official API.

## 🧩 Project Structure

- `weather_Israel.py` - MCP Server with 4 Tools for browser control and forecast extraction
- `client.py` - Generic MCP Client, connects to any MCP server
- `host.py` - Host: terminal chat that connects the user, the LLM (Gemini), and the MCP Server
- `weather_USA.py` - Additional example MCP Server (USA forecast via official API)

## 🛠️ Tools Implemented in weather_Israel.py

1. **`open_weather_forecast_israel`** - Opens the browser and navigates to the forecast page
2. **`enter_weather_forecast_city_israel`** - Types a city name into the search field
3. **`select_weather_forecast_city_israel`** - Selects the first item from the dropdown list
4. **`get_weather_forecast_text_israel`** - Extracts temperature, wind, humidity, and more from the page, and provides it to the LLM

## 🚀 How to Run

### Prerequisites
- Python installed
- Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Steps

1. Clone/download the repo to your machine

2. Create a `.env` file in the project folder with the key:
GEMINI_API_KEY=your-api-key-here

3. Install dependencies:
   
```powershell
   uv sync
```

4. Install the Chromium browser for Playwright:
```powershell
   uv run playwright install chromium
```

5. Run the project:
```powershell
   uv run host.py
```

6. Ask a question in the terminal chat about the weather in an Israeli city.

## 💬 Example Questions the Agent Can Answer

- What's the weather like in Jerusalem?
- What's the temperature in Tel Aviv right now?
- What are the wind and humidity conditions in Haifa?
- How's the weather in Beer Sheva today?

## ⚙️ Technologies

- **MCP SDK** - Protocol for exposing Tools to the LLM
- **Playwright** - Browser automation
- **Google Gemini API** - The model that manages the conversation and decides when to call tools
