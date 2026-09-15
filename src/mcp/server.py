import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

from src.mcp.tools import register_tools
from src.mcp.resources import register_resources
from src.mcp.prompts import register_prompts

log = logging.getLogger(__name__)


def create_mcp_server(core) -> Server:
    app = Server("grep")
    register_tools(app, core)
    register_resources(app, core)
    register_prompts(app)
    log.info("mcp server created")
    return app


async def run_stdio(core):
    mcp_app = create_mcp_server(core)
    async with stdio_server() as (read_stream, write_stream):
        log.info("mcp stdio mode")
        await mcp_app.run(read_stream, write_stream, mcp_app.create_initialization_options())


async def run_sse(core, host: str = "0.0.0.0", port: int = 8765):
    mcp_app = create_mcp_server(core)
    transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_app.run(streams[0], streams[1], mcp_app.create_initialization_options())

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=transport.handle_post_message, methods=["POST"]),
        ]
    )

    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    log.info("mcp sse server on %s:%d", host, port)
    await server.serve()
