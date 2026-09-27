#!/usr/bin/env python3
"""standalone mcp server launcher. starts grep hardware and serves mcp over sse."""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import GrepCore
from src.mcp.server import run_sse, run_stdio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("grep.mcp")


def parse_args():
    p = argparse.ArgumentParser(description="grep mcp server")
    p.add_argument("--config", default="config/default.yaml")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--stdio", action="store_true", help="use stdio transport instead of sse")
    return p.parse_args()


async def main():
    args = parse_args()
    log.info("starting grep mcp server")
    core = GrepCore(config_path=args.config)
    core.init()

    if args.stdio:
        await run_stdio(core)
    else:
        log.info("sse transport on %s:%d", args.host, args.port)
        await run_sse(core, host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main())
