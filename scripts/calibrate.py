#!/usr/bin/env python3
"""interactive calibration wizard for grep servo arms"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo as adafruit_servo

SERVO_MIN = 500
SERVO_MAX = 2500

CHANNELS = {
    "left_shoulder": 0,
    "left_claw": 1,
    "right_shoulder": 2,
    "right_claw": 3,
}


def init_pca():
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    return pca


def make_servo(pca, ch):
    return adafruit_servo.Servo(pca.channels[ch], min_pulse=SERVO_MIN, max_pulse=SERVO_MAX)


def sweep(s, name):
    print(f"  sweeping {name}...")
    for angle in range(0, 181, 10):
        s.angle = angle
        time.sleep(0.05)
    for angle in range(180, -1, -10):
        s.angle = angle
        time.sleep(0.05)
    s.angle = 90
    print(f"  {name} center -> 90")


def interactive_set(s, name):
    print(f"\n  {name}: type angle (0-180) or 'q' to skip")
    while True:
        raw = input("    angle> ").strip()
        if raw == "q":
            break
        try:
            a = float(raw)
            a = max(0, min(180, a))
            s.angle = a
            print(f"    -> {a}")
        except ValueError:
            print("    invalid")


def main():
    print("grep servo calibration wizard")
    print("=" * 40)
    pca = init_pca()
    servos = {name: make_servo(pca, ch) for name, ch in CHANNELS.items()}

    print("\n[1] sweep all servos")
    for name, s in servos.items():
        sweep(s, name)

    print("\n[2] interactive joint calibration")
    print("set each joint to its neutral/rest position")
    for name, s in servos.items():
        interactive_set(s, name)

    print("\n[3] center all")
    for s in servos.values():
        s.angle = 90
    print("all servos at 90 deg")
    print("\nrecord any custom min/max values into config/default.yaml")
    print("done.")
    pca.deinit()


if __name__ == "__main__":
    main()
