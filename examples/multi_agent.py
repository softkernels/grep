"""multi-agent example: observer + actor working together"""
import asyncio
import os
import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client


OBSERVER_SYSTEM = """you are the observer agent for grep robot.
your job: watch the environment. use get_sensor and capture_image.
report what you see in one sentence. if something is close (<30cm), say "alert: <distance>cm".
otherwise say "clear: <distance>cm" with a brief note on what you see."""

ACTOR_SYSTEM = """you are the actor agent for grep robot.
you receive environment reports from the observer.
if alert: set_expression alert, speak a brief warning, wave once.
if clear: set_expression idle. no speech unless asked.
keep actions minimal."""


class MultiAgentGrep:
    def __init__(self, host="raspberrypi.local", port=8765):
        self.url = f"http://{host}:{port}/sse"
        self._anthropic = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def run(self, cycles: int = 5, interval: float = 5.0):
        async with sse_client(self.url) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                tools_resp = await session.list_tools()
                all_tools = [
                    {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
                    for t in tools_resp.tools
                ]

                observer_tools = [t for t in all_tools if t["name"] in ("get_sensor", "capture_image", "get_status")]
                actor_tools = [t for t in all_tools if t["name"] in ("move_arm", "set_expression", "speak", "wave", "look_at")]

                print(f"starting {cycles}-cycle multi-agent loop (interval={interval}s)")
                for i in range(cycles):
                    print(f"\n--- cycle {i + 1}/{cycles} ---")
                    report = await self._observer_turn(session, observer_tools)
                    print(f"observer: {report}")
                    await self._actor_turn(session, actor_tools, report)
                    if i < cycles - 1:
                        await asyncio.sleep(interval)

                print("\ndone.")

    async def _observer_turn(self, session, tools) -> str:
        resp = self._anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            system=OBSERVER_SYSTEM,
            tools=tools,
            messages=[{"role": "user", "content": "observe now"}],
        )
        resp = await self._resolve_tools(session, resp, tools, OBSERVER_SYSTEM)
        return next((b.text for b in resp.content if hasattr(b, "text")), "no report")

    async def _actor_turn(self, session, tools, report: str):
        resp = self._anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            system=ACTOR_SYSTEM,
            tools=tools,
            messages=[{"role": "user", "content": f"environment report: {report}"}],
        )
        resp = await self._resolve_tools(session, resp, tools, ACTOR_SYSTEM)
        text = next((b.text for b in resp.content if hasattr(b, "text")), "")
        if text:
            print(f"actor: {text}")

    async def _resolve_tools(self, session, resp, tools, system):
        messages = [{"role": "user", "content": "observe now"}]
        while resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name}({block.input})")
                    result = await session.call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.content[0].text if result.content else "",
                    })
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})
            resp = self._anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=256,
                system=system,
                tools=tools,
                messages=messages,
            )
        return resp


if __name__ == "__main__":
    agent = MultiAgentGrep(
        host=os.environ.get("GREP_HOST", "raspberrypi.local"),
        port=int(os.environ.get("GREP_PORT", 8765)),
    )
    asyncio.run(agent.run(
        cycles=int(os.environ.get("GREP_CYCLES", 10)),
        interval=float(os.environ.get("GREP_INTERVAL", 5.0)),
    ))
