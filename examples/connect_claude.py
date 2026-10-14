"""connect claude to grep via mcp"""
import asyncio
import os
import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client


class GrepClient:
    def __init__(self, host="raspberrypi.local", port=8765):
        self.url = f"http://{host}:{port}/sse"
        self._session = None
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def connect(self):
        async with sse_client(self.url) as streams:
            async with ClientSession(*streams) as session:
                self._session = session
                await session.initialize()
                tools = await session.list_tools()
                print(f"connected to grep. tools: {[t.name for t in tools.tools]}")
                await self._loop(session)

    async def _loop(self, session):
        tools = await session.list_tools()
        mcp_tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in tools.tools
        ]

        messages = []
        print("type to talk to grep. ctrl-c to quit.")
        while True:
            user_input = input("\nyou: ").strip()
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            resp = self._client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system="you are controlling a physical robot called grep. use the available tools to interact with its body and sensors.",
                tools=mcp_tools,
                messages=messages,
            )

            # handle tool calls
            while resp.stop_reason == "tool_use":
                tool_results = []
                for block in resp.content:
                    if block.type == "tool_use":
                        print(f"  [tool] {block.name}({block.input})")
                        result = await session.call_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result.content[0].text if result.content else ""),
                        })

                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user", "content": tool_results})

                resp = self._client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    system="you are controlling a physical robot called grep.",
                    tools=mcp_tools,
                    messages=messages,
                )

            text = next(
                (b.text for b in resp.content if hasattr(b, "text")), ""
            )
            print(f"grep: {text}")
            messages.append({"role": "assistant", "content": resp.content})


if __name__ == "__main__":
    client = GrepClient(
        host=os.environ.get("GREP_HOST", "raspberrypi.local"),
        port=int(os.environ.get("GREP_PORT", 8765)),
    )
    asyncio.run(client.connect())
