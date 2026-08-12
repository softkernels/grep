import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo as adafruit_servo
import serial
import logging

log = logging.getLogger(__name__)

SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500


class ServoController:
    def __init__(self, config):
        self.config = config
        self.pwm = None
        self.servos = {}
        self._last_angles = {}
        self._uart = None
        self._setup()

    def _setup(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pwm = PCA9685(i2c, address=self.config.get("i2c_address", 0x40))
        self.pwm.frequency = self.config.get("pwm_frequency", 50)

        arms = self.config.get("arms", {})
        for arm_name, arm_cfg in arms.items():
            for joint in ("shoulder", "claw"):
                ch = arm_cfg[f"{joint}_channel"]
                s = adafruit_servo.Servo(
                    self.pwm.channels[ch],
                    min_pulse=SERVO_MIN_PULSE,
                    max_pulse=SERVO_MAX_PULSE,
                )
                key = f"{arm_name}_{joint}"
                self.servos[key] = s
                self._last_angles[key] = 90

        uart_port = self.config.get("uart_port", "/dev/ttyUSB0")
        uart_baud = self.config.get("uart_baud", 115200)
        try:
            self._uart = serial.Serial(uart_port, uart_baud, timeout=0.1)
            log.info("uart connected: %s", uart_port)
        except serial.SerialException as e:
            log.warning("uart not available: %s", e)

    def move(self, arm: str, joint: str, angle: float) -> bool:
        key = f"{arm}_{joint}"
        if key not in self.servos:
            log.error("unknown servo: %s", key)
            return False

        arm_cfg = self.config["arms"].get(arm, {})
        min_a = arm_cfg.get(f"{joint}_min", 0)
        max_a = arm_cfg.get(f"{joint}_max", 180)
        angle = max(min_a, min(max_a, angle))

        # jitter suppression
        threshold = self.config.get("jitter_threshold", 2)
        last = self._last_angles.get(key, -999)
        if abs(angle - last) < threshold:
            return True

        self.servos[key].angle = angle
        self._last_angles[key] = angle
        delay = self.config.get("move_delay", 0.02)
        time.sleep(delay)

        log.debug("move %s %s -> %.1f deg", arm, joint, angle)
        return True

    def move_smooth(self, arm: str, joint: str, target: float, steps: int = 10):
        key = f"{arm}_{joint}"
        current = self._last_angles.get(key, 90)
        delta = (target - current) / steps
        for i in range(steps):
            self.move(arm, joint, current + delta * (i + 1))
            time.sleep(0.01)

    def get_angle(self, arm: str, joint: str) -> float:
        key = f"{arm}_{joint}"
        return self._last_angles.get(key, 90)

    def center_all(self):
        for key in self.servos:
            parts = key.split("_", 1)
            self.move(parts[0], parts[1], 90)

    def shutdown(self):
        self.center_all()
        if self.pwm:
            self.pwm.deinit()
        if self._uart:
            self._uart.close()
