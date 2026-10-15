"""connect gpt-4o to grep via mcp"""
import asyncio
import os
import json
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    host = os.environ.get("GREP_HOST", "raspberrypi.local")
    port = int(os.environ.get("GREP_PORT", 8765))
    url = f"http://{host}:{port}/sse"

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    async with sse_client(url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()

            # convert mcp tools to openai function format
            functions = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,
                    },
                }
                for t in mcp_tools.tools
            ]

            print(f"connected to grep at {url}")
            print(f"tools: {[t.name for t in mcp_tools.tools]}")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "you control a physical robot called grep. "
                        "it has arms, a camera, an ir sensor, and a british voice. "
                        "use tools to interact with the environment."
                    ),
                }
            ]

            print("type to talk to grep. ctrl-c to quit.")
            while True:
                user_input = input("\nyou: ").strip()
                if not user_input:
                    continue

                messages.append({"role": "user", "content": user_input})

                resp = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=functions,
                    tool_choice="auto",
                )

                msg = resp.choices[0].message
                messages.append(msg)

                while msg.tool_calls:
                    tool_outputs = []
                    for call in msg.tool_calls:
                        args = json.loads(call.function.arguments)
                        print(f"  [tool] {call.function.name}({args})")
                        result = await session.call_tool(call.function.name, args)
                        content = result.content[0].text if result.content else ""
                        tool_outputs.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": content,
                        })

                    messages.extend(tool_outputs)
                    resp = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=functions,
                        tool_choice="auto",
                    )
                    msg = resp.choices[0].message
                    messages.append(msg)

                print(f"grep: {msg.content}")


if __name__ == "__main__":
    asyncio.run(main())
