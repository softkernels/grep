import io
import base64
import logging
from picamera2 import Picamera2
from PIL import Image

log = logging.getLogger(__name__)


class Camera:
    def __init__(self, config):
        self.config = config
        self._cam = None
        self._setup()

    def _setup(self):
        self._cam = Picamera2()
        w, h = self.config.get("resolution", [1920, 1080])
        cfg = self._cam.create_still_configuration(
            main={"size": (w, h), "format": "RGB888"},
            lores={"size": (640, 480)},
            display="lores",
        )
        self._cam.configure(cfg)
        if self.config.get("autofocus", True):
            self._cam.set_controls({"AfMode": 2, "AfSpeed": 1})
        self._cam.start()
        log.info("camera ready %dx%d", w, h)

    def capture(self) -> bytes:
        buf = io.BytesIO()
        arr = self._cam.capture_array("main")
        img = Image.fromarray(arr)
        quality = self.config.get("quality", 85)
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()

    def capture_b64(self) -> str:
        data = self.capture()
        return base64.b64encode(data).decode("utf-8")

    def capture_thumbnail(self, size=(320, 240)) -> bytes:
        arr = self._cam.capture_array("lores")
        img = Image.fromarray(arr).resize(size)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()

    def release(self):
        if self._cam:
            self._cam.stop()
            self._cam.close()
            log.info("camera released")
