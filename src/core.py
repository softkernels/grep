import asyncio
import logging
import signal
import yaml
from pathlib import Path

from src.servo import ServoController
from src.camera import Camera
from src.sensor import IRSensor
from src.face import FaceRenderer
from src.voice import Voice
from src.memory import Memory
from src.agent import AgentManager

log = logging.getLogger(__name__)


def load_config(path="config/default.yaml"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with open(p) as f:
        return yaml.safe_load(f)


class GrepCore:
    def __init__(self, config_path="config/default.yaml"):
        self.config = load_config(config_path)
        local = Path("config/local.yaml")
        if local.exists():
            with open(local) as f:
                import copy
                local_cfg = yaml.safe_load(f)
                self._deep_merge(self.config, local_cfg)

        self.servo = None
        self.camera = None
        self.sensor = None
        self.face = None
        self.voice = None
        self.memory = None
        self.agents = None
        self._running = False

    def _deep_merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def init(self):
        log.info("initializing grep")
        self.servo = ServoController(self.config["servo"])
        self.camera = Camera(self.config["camera"])
        self.sensor = IRSensor(self.config["sensor"])
        self.face = FaceRenderer(self.config["face"], self.config.get("expressions_path", "config/expressions.yaml"))
        self.voice = Voice(self.config["voice"])
        self.memory = Memory(self.config["memory"])
        self.agents = AgentManager(self.config, self)
        log.info("grep ready")

    def get_state(self) -> dict:
        return {
            "sensor_distance": self.sensor.read() if self.sensor else None,
            "servo_angles": {
                "left_shoulder": self.servo.get_angle("left", "shoulder"),
                "left_claw": self.servo.get_angle("left", "claw"),
                "right_shoulder": self.servo.get_angle("right", "shoulder"),
                "right_claw": self.servo.get_angle("right", "claw"),
            } if self.servo else {},
            "expression": self.face.current_expression if self.face else None,
            "speaking": self.voice.is_speaking() if self.voice else False,
        }

    async def run(self):
        self._running = True
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop)

        self.face.start()

        idle_task = asyncio.create_task(self._idle_loop())
        sensor_task = asyncio.create_task(self._sensor_loop())

        log.info("core loop started")
        await asyncio.gather(idle_task, sensor_task)

    async def _idle_loop(self):
        while self._running:
            self.face.tick()
            await asyncio.sleep(1.0 / self.config["face"]["fps"])

    async def _proximity_react(self, dist: float):
        if dist < 20:
            self.face.set_expression("alert")
            self.voice.speak("hello there.", block=False)
        elif dist < 40:
            self.face.set_expression("curious")
        else:
            self.face.set_expression("idle")

    async def _sensor_loop(self):
        interval = 1.0 / self.config["sensor"].get("sample_rate", 10)
        while self._running:
            dist = self.sensor.read()
            if dist is not None and dist < 30:
                log.info("proximity alert: %.1f cm", dist)
                self.face.set_expression("alert")
                await asyncio.sleep(2.0)
                self.face.set_expression("idle")
            await asyncio.sleep(interval)

    def _stop(self):
        log.info("shutting down")
        self._running = False
        self.face.stop()
        self.servo.shutdown()
        self.sensor.cleanup()
        self.camera.release()
        self.voice.shutdown()
        self.memory.close()
