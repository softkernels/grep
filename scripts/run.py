#!/usr/bin/env python3
import asyncio
import logging
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import GrepCore
from src.mcp.server import run_sse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("grep.run")


def parse_args():
    p = argparse.ArgumentParser(description="grep robot main process")
    p.add_argument("--config", default="config/default.yaml")
    p.add_argument("--mcp", action="store_true", help="also start mcp server")
    p.add_argument("--mcp-host", default="0.0.0.0")
    p.add_argument("--mcp-port", type=int, default=8765)
    p.add_argument("--no-display", action="store_true", help="skip face display init")
    return p.parse_args()


async def main():
    args = parse_args()
    core = GrepCore(config_path=args.config)
    core.init()

    tasks = [asyncio.create_task(core.run())]

    if args.mcp:
        tasks.append(asyncio.create_task(
            run_sse(core, host=args.mcp_host, port=args.mcp_port)
        ))
        log.info("mcp server on %s:%d", args.mcp_host, args.mcp_port)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        log.info("grep stopped")


if __name__ == "__main__":
    asyncio.run(main())
