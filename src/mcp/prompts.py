from mcp.server import Server
from mcp.types import Prompt, PromptMessage, TextContent


def register_prompts(app: Server):

    @app.list_prompts()
    async def list_prompts():
        return [
            Prompt(
                name="observe",
                description="prompt grep to observe its environment and report",
                arguments=[],
            ),
            Prompt(
                name="greet",
                description="have grep greet whoever is nearby",
                arguments=[
                    {"name": "name", "description": "name of the person", "required": False},
                ],
            ),
            Prompt(
                name="scan",
                description="full environment scan: sensor + image + status report",
                arguments=[],
            ),
            Prompt(
                name="patrol",
                description="look around in all directions",
                arguments=[],
            ),
        ]

    @app.get_prompt()
    async def get_prompt(name: str, arguments: dict):
        if name == "observe":
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            "use get_sensor to check proximity. "
                            "if something is within 40cm, use capture_image to see it. "
                            "report what you observe in one or two sentences."
                        ),
                    ),
                )
            ]

        elif name == "greet":
            person = arguments.get("name", "there")
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            f"greet {person}. use set_expression happy then speak a brief british greeting. "
                            f"then wave."
                        ),
                    ),
                )
            ]

        elif name == "scan":
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            "perform a full environment scan. "
                            "1. get_status. "
                            "2. get_sensor. "
                            "3. capture_image. "
                            "summarise what you find. use set_expression alert if something is within 30cm."
                        ),
                    ),
                )
            ]

        elif name == "patrol":
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            "look left, pause, look right, pause, look center. "
                            "after each direction, capture_image and note what you see. "
                            "return a brief summary of the patrol."
                        ),
                    ),
                )
            ]

        return []
