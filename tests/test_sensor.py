import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def sensor_config():
    return {
        "gpio_pin": 17,
        "adc_channel": 0,
        "min_distance": 10,
        "max_distance": 80,
        "samples_avg": 3,
    }


def _make_sensor(sensor_config):
    with patch("src.sensor.GPIO"), patch("src.sensor.spidev", create=True) as mock_spi_mod:
        mock_spi = MagicMock()
        mock_spi_mod.SpiDev.return_value = mock_spi
        from src.sensor import IRSensor
        s = IRSensor(sensor_config)
        s._spi = mock_spi
        return s, mock_spi


def test_voltage_to_cm_near():
    from src.sensor import _voltage_to_cm
    cm = _voltage_to_cm(3.0)
    assert cm == 10


def test_voltage_to_cm_far():
    from src.sensor import _voltage_to_cm
    cm = _voltage_to_cm(0.3)
    assert cm == 80


def test_voltage_to_cm_mid():
    from src.sensor import _voltage_to_cm
    cm = _voltage_to_cm(1.5)
    assert 15 < cm < 30


def test_read_clamps_min(sensor_config):
    with patch("src.sensor.GPIO"):
        from src.sensor import IRSensor
        s = IRSensor.__new__(IRSensor)
        s.config = sensor_config
        s.pin = 17
        s._samples = 1
        s._min = 10
        s._max = 80
        s._adc_channel = 0
        s._spi = None
        # with no spi, _read_adc returns 0.0 -> _voltage_to_cm(0) = 80
        result = s.read()
        assert result == 80


def test_is_triggered_far(sensor_config):
    with patch("src.sensor.GPIO"):
        from src.sensor import IRSensor
        s = IRSensor.__new__(IRSensor)
        s.config = sensor_config
        s.pin = 17
        s._samples = 1
        s._min = 10
        s._max = 80
        s._adc_channel = 0
        s._spi = None
        # read returns 80cm when no spi
        assert s.is_triggered(threshold=30) is False
