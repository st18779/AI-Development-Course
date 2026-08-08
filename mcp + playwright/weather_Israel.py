from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("weather-Israel")

FORECAST_URL = "https://www.weather2day.co.il/forecast"

browser = None
page = None
pw = None


async def init_browser():
    """פותחת דפדפן פעם אחת בלבד - אם כבר פתוח, לא עושה כלום"""
    global browser, page, pw
    if page is None:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """פותחת דפדפן ומנווטת לדף התחזית של אתר מזג האוויר הישראלי"""
    await init_browser()
    await page.goto(FORECAST_URL)
    return "page opened"


@mcp.tool()
async def enter_weather_forecast_city_israel(city_name: str) -> str:
    """מזינה שם עיר בשדה החיפוש (בלי ללחוץ Enter - רק מקלידה)

    Args:
        city_name: שם העיר בעברית, למשל ירושלים
    """
    await init_browser()
    await page.locator("#city_search_forecast").fill(city_name)
    return f"typed {city_name}"


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """בוחרת את הפריט הראשון ברשימה הנפתחת של הערים המוצעות"""
    await init_browser()
    await page.locator("#city_search_forecastautocomplete-list div").first.click()
    await page.wait_for_load_state("networkidle")
    return "city selected"

@mcp.tool()
async def get_weather_forecast_text_israel() -> str:
    """מחלצת את תוכן תיבת מזג האוויר הנוכחי (טמפרטורה, רוח, לחות וכו') מהדף"""
    await init_browser()
    text = await page.locator(".current-weather").inner_text()
    return text

    
def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()