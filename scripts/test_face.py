#!/usr/bin/env python3
"""face expression test - cycles through all expressions"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.face import FaceRenderer

config = {
    "width": 1024,
    "height": 600,
    "fps": 30,
    "background": [0, 0, 0],
    "eye_color": [0, 255, 100],
    "mouth_color": [0, 255, 100],
    "idle_blink_interval": 4.0,
}

face = FaceRenderer(config, "config/expressions.yaml")
face.start()

expressions = list(face._expressions.keys())
print(f"testing {len(expressions)} expressions: {expressions}")

for expr in expressions:
    print(f"  -> {expr}")
    face.set_expression(expr)
    end = time.time() + 2.0
    while time.time() < end:
        face.tick()

face.stop()
print("face test done")
