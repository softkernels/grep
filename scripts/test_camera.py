#!/usr/bin/env python3
"""camera test - captures a photo and saves it"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.camera import Camera

config = {
    "resolution": [1920, 1080],
    "format": "jpeg",
    "quality": 85,
    "autofocus": True,
    "tuning": "noir",
}

cam = Camera(config)
print("capturing image...")
data = cam.capture()
out = Path("/tmp/grep_test.jpg")
out.write_bytes(data)
print(f"saved {len(data)} bytes to {out}")
cam.release()
