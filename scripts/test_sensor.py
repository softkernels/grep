#!/usr/bin/env python3
"""ir sensor test - prints distance readings for 10 seconds"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sensor import IRSensor

config = {
    "gpio_pin": 17,
    "adc_channel": 0,
    "min_distance": 10,
    "max_distance": 80,
    "samples_avg": 3,
}

sensor = IRSensor(config)
print("reading ir sensor for 10 seconds (ctrl-c to stop)")
try:
    for _ in range(50):
        d = sensor.read()
        bar = "#" * int(d / 2)
        print(f"  {d:5.1f} cm  {bar}")
        time.sleep(0.2)
finally:
    sensor.cleanup()
    print("done")
