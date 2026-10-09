#!/usr/bin/env python3
"""voice test - speaks a test phrase"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.voice import Voice

config = {
    "voice_id": "N2lVS1w4EtoT3dr4eOWO",
    "model": "eleven_turbo_v2",
    "cache_dir": "/tmp/grep_voice_test",
    "api_key_env": "ELEVENLABS_API_KEY",
}

voice = Voice(config)
phrases = [
    "hello. i am grep.",
    "autonomous observation in progress.",
    "i see you.",
]
for p in phrases:
    print(f"speaking: {p}")
    voice.speak(p, block=True)

voice.shutdown()
print("voice test done")
