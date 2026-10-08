#!/usr/bin/env python3
"""quick servo test - moves each joint through its range"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import board, busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo as adafruit_servo

CHANNELS = {"left_shoulder": 0, "left_claw": 1, "right_shoulder": 2, "right_claw": 3}

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

for name, ch in CHANNELS.items():
    s = adafruit_servo.Servo(pca.channels[ch], min_pulse=500, max_pulse=2500)
    print(f"testing {name} (ch {ch})")
    s.angle = 0;   time.sleep(0.5)
    s.angle = 90;  time.sleep(0.5)
    s.angle = 180; time.sleep(0.5)
    s.angle = 90;  time.sleep(0.3)
    print(f"  {name} ok")

pca.deinit()
print("all servos tested")
