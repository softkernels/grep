import math
import time
import threading
import logging
import yaml
import pygame
import numpy as np

log = logging.getLogger(__name__)


class FaceRenderer:
    def __init__(self, config, expressions_path="config/expressions.yaml"):
        self.config = config
        self.width = config.get("width", 1024)
        self.height = config.get("height", 600)
        self.fps = config.get("fps", 30)
        self.bg = tuple(config.get("background", [0, 0, 0]))
        self.eye_color = tuple(config.get("eye_color", [0, 255, 100]))
        self.mouth_color = tuple(config.get("mouth_color", [0, 255, 100]))
        self.current_expression = "idle"
        self._expressions = {}
        self._screen = None
        self._clock = None
        self._running = False
        self._thread = None
        self._blink_state = False
        self._blink_timer = 0.0
        self._last_blink = time.time()
        self._osc_phase = 0.0
        self._pupil_target = [0, 0]
        self._pupil_pos = [0.0, 0.0]
        self._load_expressions(expressions_path)

    def _load_expressions(self, path):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            self._expressions = data.get("expressions", {})
            log.info("loaded %d expressions", len(self._expressions))
        except Exception as e:
            log.error("failed to load expressions: %s", e)
            self._expressions = {}

    def start(self):
        pygame.init()
        self._screen = pygame.display.set_mode(
            (self.width, self.height), pygame.NOFRAME
        )
        pygame.display.set_caption("grep")
        self._clock = pygame.time.Clock()
        self._running = True
        log.info("face display started %dx%d", self.width, self.height)

    def stop(self):
        self._running = False
        pygame.quit()

    def set_expression(self, name: str):
        if name not in self._expressions:
            log.warning("unknown expression: %s", name)
            return
        self.current_expression = name
        log.debug("expression -> %s", name)

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

        self._screen.fill(self.bg)
        expr = self._expressions.get(self.current_expression, {})
        self._draw_eyes(expr.get("eyes", {}))
        self._draw_mouth(expr.get("mouth", {}))
        pygame.display.flip()
        self._osc_phase += 0.05
        self._clock.tick(self.fps)

    def _draw_eyes(self, eye_cfg):
        if not eye_cfg:
            return

        shape = eye_cfg.get("shape", "circle")
        blink_enabled = eye_cfg.get("blink", True)
        blink_interval = self.config.get("idle_blink_interval", 4.0)

        now = time.time()
        if blink_enabled and now - self._last_blink > blink_interval:
            self._blink_state = True
            self._last_blink = now

        if self._blink_state:
            self._blink_timer += 1
            if self._blink_timer > 3:
                self._blink_state = False
                self._blink_timer = 0

        # eye positions
        left_x = self.width // 3
        right_x = 2 * self.width // 3
        eye_y = self.height // 2 - 30
        offset_y = eye_cfg.get("offset_y", 0)
        eye_y += offset_y

        if shape == "circle":
            r = eye_cfg.get("radius", 40)
            pr = eye_cfg.get("pupil_radius", 15)
            for ex in (left_x, right_x):
                if self._blink_state:
                    pygame.draw.line(self._screen, self.eye_color,
                                     (ex - r, eye_y), (ex + r, eye_y), 4)
                else:
                    pygame.draw.circle(self._screen, self.eye_color, (ex, eye_y), r, 3)
                    pygame.draw.circle(self._screen, self.eye_color, (ex, eye_y), pr)
        elif shape == "ellipse":
            w = eye_cfg.get("width", 60)
            h = eye_cfg.get("height", 20)
            for ex in (left_x, right_x):
                rect = pygame.Rect(ex - w // 2, eye_y - h // 2, w, h)
                pygame.draw.ellipse(self._screen, self.eye_color, rect, 3)
        elif shape == "line":
            w = eye_cfg.get("width", 60)
            for ex in (left_x, right_x):
                pygame.draw.line(self._screen, self.eye_color,
                                 (ex - w // 2, eye_y), (ex + w // 2, eye_y), 4)

    def _draw_mouth(self, mouth_cfg):
        if not mouth_cfg:
            return

        mtype = mouth_cfg.get("type", "oscilloscope")
        amplitude = mouth_cfg.get("amplitude", 10)
        frequency = mouth_cfg.get("frequency", 0.5)
        points_n = mouth_cfg.get("points", 64)

        cx = self.width // 2
        my = int(self.height * 0.72)
        mouth_w = 300

        if mtype in ("oscilloscope", "waveform"):
            pts = []
            for i in range(points_n):
                t = i / (points_n - 1)
                x = cx - mouth_w // 2 + int(t * mouth_w)
                wave = math.sin(t * math.pi * 2 * frequency + self._osc_phase) * amplitude
                if mtype == "waveform":
                    wave += math.sin(t * math.pi * 4 * frequency + self._osc_phase * 1.3) * (amplitude * 0.4)
                y = my + int(wave)
                pts.append((x, y))
            if len(pts) > 1:
                pygame.draw.lines(self._screen, self.mouth_color, False, pts, 2)

        elif mtype == "flat":
            amp = mouth_cfg.get("amplitude", 2)
            pts = []
            for i in range(points_n):
                t = i / (points_n - 1)
                x = cx - mouth_w // 2 + int(t * mouth_w)
                y = my + int(math.sin(self._osc_phase * frequency + t * 2) * amp)
                pts.append((x, y))
            if len(pts) > 1:
                pygame.draw.lines(self._screen, self.mouth_color, False, pts, 2)

        elif mtype == "arc":
            rect = pygame.Rect(cx - 60, my - 20, 120, 60)
            pygame.draw.arc(self._screen, self.mouth_color, rect, 0, math.pi, 3)

        elif mtype == "oval":
            w = mouth_cfg.get("width", 40)
            h = mouth_cfg.get("height", 30)
            rect = pygame.Rect(cx - w // 2, my - h // 2, w, h)
            pygame.draw.ellipse(self._screen, self.mouth_color, rect, 3)

    def set_pupil_target(self, dx: float, dy: float):
        self._pupil_target = [dx, dy]
