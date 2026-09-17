import json
import logging
from mcp.server import Server
from mcp.types import Resource, TextContent

log = logging.getLogger(__name__)


def register_resources(app: Server, core):

    @app.list_resources()
    async def list_resources():
        return [
            Resource(
                uri="grep://status",
                name="robot status",
                description="current state of all grep subsystems",
                mimeType="application/json",
            ),
            Resource(
                uri="grep://memory/recent",
                name="recent transmissions",
                description="last 20 conversation entries",
                mimeType="application/json",
            ),
            Resource(
                uri="grep://memory/observations",
                name="recent observations",
                description="last 10 sensor and camera observations",
                mimeType="application/json",
            ),
            Resource(
                uri="grep://config",
                name="active config",
                description="current grep configuration (sanitized)",
                mimeType="application/json",
            ),
        ]

    @app.read_resource()
    async def read_resource(uri: str):
        if uri == "grep://status":
            state = core.get_state()
            return [TextContent(type="text", text=json.dumps(state, indent=2))]

        elif uri == "grep://memory/recent":
            ctx = core.memory.get_context(20)
            return [TextContent(type="text", text=json.dumps(ctx, indent=2))]

        elif uri == "grep://memory/observations":
            obs = core.memory.get_recent_observations(10)
            return [TextContent(type="text", text=json.dumps(obs, indent=2))]

        elif uri == "grep://config":
            safe_cfg = _sanitize_config(core.config)
            return [TextContent(type="text", text=json.dumps(safe_cfg, indent=2))]

        else:
            return [TextContent(type="text", text=f"unknown resource: {uri}")]


def _sanitize_config(cfg: dict) -> dict:
    import copy
    out = copy.deepcopy(cfg)
    # strip any key that might contain credentials
    for section in out.values():
        if isinstance(section, dict):
            for k in list(section.keys()):
                if any(x in k.lower() for x in ("key", "secret", "token", "password")):
                    section[k] = "***"
    return out
