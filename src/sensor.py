__all__ = ['IRSensor']
import time
import logging
import RPi.GPIO as GPIO

log = logging.getLogger(__name__)

# GP2Y0A21YK0F voltage-to-distance lookup (V -> cm)
# measured at 5V supply
_VTABLE = [
    (3.0, 10),
    (2.5, 12),
    (2.0, 15),
    (1.5, 20),
    (1.1, 30),
    (0.85, 40),
    (0.68, 50),
    (0.57, 60),
    (0.50, 70),
    (0.45, 80),
]


def _voltage_to_cm(voltage: float) -> float:
    if voltage >= _VTABLE[0][0]:
        return _VTABLE[0][1]
    if voltage <= _VTABLE[-1][0]:
        return _VTABLE[-1][1]
    for i in range(len(_VTABLE) - 1):
        v1, d1 = _VTABLE[i]
        v2, d2 = _VTABLE[i + 1]
        if v2 <= voltage <= v1:
            ratio = (voltage - v2) / (v1 - v2)
            return d2 + ratio * (d1 - d2)
    return 80.0


class IRSensor:
    def __init__(self, config):
        self.config = config
        self.pin = config.get("gpio_pin", 17)
        self._samples = config.get("samples_avg", 3)
        self._min = config.get("min_distance", 10)
        self._max = config.get("max_distance", 80)
        self._adc = None
        self._setup()

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        # try to init MCP3008 adc on SPI for analog reading
        try:
            import spidev
            self._spi = spidev.SpiDev()
            self._spi.open(0, 0)
            self._spi.max_speed_hz = 1350000
            self._adc_channel = self.config.get("adc_channel", 0)
            log.info("adc ready on spi channel %d", self._adc_channel)
        except Exception as e:
            log.warning("spi adc not available: %s", e)
            self._spi = None

    def _read_adc(self) -> float:
        if self._spi is None:
            return 0.0
        ch = self._adc_channel
        r = self._spi.xfer2([1, (8 + ch) << 4, 0])
        raw = ((r[1] & 3) << 8) | r[2]
        voltage = (raw / 1023.0) * 3.3
        return voltage

    def read(self) -> float:
        readings = []
        for _ in range(self._samples):
            v = self._read_adc()
            cm = _voltage_to_cm(v)
            readings.append(cm)
            time.sleep(0.005)
        avg = sum(readings) / len(readings)
        avg = max(self._min, min(self._max, avg))
        return round(avg, 1)

    def is_triggered(self, threshold: float = 30.0) -> bool:
        d = self.read()
        return d < threshold

    def cleanup(self):
        if self._spi:
            self._spi.close()
        GPIO.cleanup(self.pin)
        log.info("sensor cleanup done")
