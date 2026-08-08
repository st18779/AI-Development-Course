import asyncio
from contextlib import AsyncExitStack
from typing import Any

from google import genai
from google.genai import types
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()


class ChatHost:
    def __init__(self):
        self.mcp_clients: list[MCPClient] = [MCPClient("./weather_Israel.py")]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()
        self.genai_client = genai.Client()  # קורא את GEMINI_API_KEY מה-.env אוטומטית

    async def connect_mcp_clients(self):
        """Connect all configured MCP clients once."""
        if self.clients_connected:
            return
        for client in self.mcp_clients:
            if client.session is None:
                await client.connect_to_server()
        if not self.mcp_clients:
            raise RuntimeError("No MCP clients are connected")
        self.clients_connected = True

    async def get_available_tools(self) -> list[types.FunctionDeclaration]:
        """Collect tools from all MCP clients and map them back to their owner."""
        await self.connect_mcp_clients()
        self.tool_clients = {}
        available_tools: list[types.FunctionDeclaration] = []

        for client in self.mcp_clients:
            if client.session is None:
                print(f"Warning: MCP client {client.client_name} is not connected, skipping")
                continue
            try:
                response = await client.session.list_tools()
                for tool in response.tools:
                    exposed_name = f"{client.client_name}__{tool.name}"
                    if exposed_name in self.tool_clients:
                        raise RuntimeError(f"Duplicate tool name detected: {exposed_name}")

                    self.tool_clients[exposed_name] = (client, tool.name)
                    available_tools.append(
                        types.FunctionDeclaration(
                            name=exposed_name,
                            description=f"[{client.client_name}] {tool.description}",
                            parameters_json_schema=tool.inputSchema,
                        )
                    )
            except Exception as e:
                print(f"Warning: Failed to get tools from {client.client_name}: {str(e)}")
                continue

        if not available_tools:
            raise RuntimeError("No tools available from any MCP client")

        return available_tools

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        available_tools = await self.get_available_tools()
        gemini_tool = types.Tool(function_declarations=available_tools)

        contents = [types.Content(role="user", parts=[types.Part(text=query)])]
        final_text = []

        system_instruction = """
אתה נותן מענה למשתמש ששואל בצ'אט מה מזג האוויר בעיר מסוימת בישראל
1. אתה מקבל מהמשתמש את שם העיר
2. מנווט לאתר מזג האוויר
3. מזין את שם העיר שהמשתמש ביקש
4. לוחץ על שם העיר בתיבת הבחירה
5. מחכה לטעינת העמוד ומוודא שאכן נפתח העמוד הנכון
6. מחזיר תשובה למשתמש מה מזג האוויר רק לפי המידע שיש לך באתר"""

        while True:
            response = await self.genai_client.aio.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[gemini_tool],
                    system_instruction=system_instruction,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )

            candidate = response.candidates[0]
            contents.append(candidate.content)

            function_calls = response.function_calls or []

            if not function_calls:
                if response.text:
                    final_text.append(response.text)
                break

            function_response_parts = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = fc.args

                if tool_name not in self.tool_clients:
                    raise RuntimeError(f"Unknown tool requested by model: {tool_name}")

                client, original_tool_name = self.tool_clients[tool_name]
                if client.session is None:
                    raise RuntimeError(f"MCP client {client.client_name} is not connected")

                result = await client.session.call_tool(original_tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                result_text = "".join(
                    item.text for item in result.content if hasattr(item, "text")
                )
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result_text},
                    )
                )

            contents.append(types.Content(role="user", parts=function_response_parts))

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()


async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()


if __name__ == "__main__":
    asyncio.run(main())