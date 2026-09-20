import asyncio
import base64
import logging
import time
from collections import defaultdict
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent

log = logging.getLogger(__name__)


_last_move: dict = defaultdict(float)
MOVE_RATE_LIMIT = 0.05  # min seconds between moves on same joint

def register_tools(app: Server, core):

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="move_arm",
                description="move a servo joint to an angle. arm: left|right. joint: shoulder|claw. angle: 0-180.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arm": {"type": "string", "enum": ["left", "right"]},
                        "joint": {"type": "string", "enum": ["shoulder", "claw"]},
                        "angle": {"type": "number", "minimum": 0, "maximum": 180},
                    },
                    "required": ["arm", "joint", "angle"],
                },
            ),
            Tool(
                name="get_sensor",
                description="read ir proximity sensor. returns distance in cm (10-80).",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="capture_image",
                description="capture image from pi camera. returns base64 jpeg.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="set_expression",
                description="set grep face expression. options: idle, alert, curious, speaking, squint, sleep, happy, surprised.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="speak",
                description="make grep say something via tts. british accent.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "maxLength": 500},
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="get_status",
                description="get full robot status snapshot.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="wave",
                description="run wave animation with left arm.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="look_at",
                description="turn grep's attention to a direction. direction: left|right|up|down|center.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["left", "right", "up", "down", "center"],
                        },
                    },
                    "required": ["direction"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        log.info("tool: %s %s", name, arguments)

        if name == "move_arm":
            arm = arguments["arm"]
            joint = arguments["joint"]
            angle = float(arguments["angle"])
            ok = core.servo.move(arm, joint, angle)
            return [TextContent(type="text", text=f"moved {arm} {joint} to {angle:.1f} deg" if ok else "move failed")]

        elif name == "get_sensor":
            dist = core.sensor.read()
            core.memory.record_observation(sensor_distance=dist)
            return [TextContent(type="text", text=f"{dist} cm")]

        elif name == "capture_image":
            b64 = core.camera.capture_b64()
            core.memory.record_observation(image_hash=b64[:16])
            return [
                ImageContent(type="image", data=b64, mimeType="image/jpeg"),
                TextContent(type="text", text="image captured"),
            ]

        elif name == "set_expression":
            name_expr = arguments["name"]
            core.face.set_expression(name_expr)
            return [TextContent(type="text", text=f"expression: {name_expr}")]

        elif name == "speak":
            text = arguments["text"]
            core.face.set_expression("speaking")
            ok = core.voice.speak(text, block=False)
            core.memory.record("assistant", text, agent="mcp")
            return [TextContent(type="text", text="speaking" if ok else "tts failed")]

        elif name == "get_status":
            state = core.get_state()
            import json
            return [TextContent(type="text", text=json.dumps(state, indent=2))]

        elif name == "wave":
            await _wave_sequence(core)
            return [TextContent(type="text", text="wave complete")]

        elif name == "look_at":
            direction = arguments["direction"]
            await _look_at(core, direction)
            return [TextContent(type="text", text=f"looking {direction}")]

        else:
            return [TextContent(type="text", text=f"unknown tool: {name}")]


async def _wave_sequence(core):
    core.face.set_expression("happy")
    core.servo.move("left", "shoulder", 90)
    await asyncio.sleep(0.3)
    for _ in range(3):
        core.servo.move("left", "claw", 30)
        await asyncio.sleep(0.25)
        core.servo.move("left", "claw", 80)
        await asyncio.sleep(0.25)
    core.servo.move("left", "shoulder", 90)
    core.servo.move("left", "claw", 60)
    core.face.set_expression("idle")


async def _look_at(core, direction: str):
    # shoulder controls left/right facing; claw adjusts up/down tilt
    angles = {
        "left": ("left", "shoulder", 130),
        "right": ("right", "shoulder", 130),
        "up": ("left", "shoulder", 60),
        "down": ("left", "shoulder", 120),
        "center": ("left", "shoulder", 90),
    }
    if direction in angles:
        arm, joint, angle = angles[direction]
        core.servo.move(arm, joint, angle)
        await asyncio.sleep(0.2)
    if direction == "center":
        core.servo.move("right", "shoulder", 90)
    expr_map = {
        "left": "curious", "right": "curious",
        "up": "alert", "down": "squint", "center": "idle",
    }
    core.face.set_expression(expr_map.get(direction, "idle"))
