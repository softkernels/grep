import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def servo_config():
    return {
        "i2c_bus": 1,
        "i2c_address": 0x40,
        "pwm_frequency": 50,
        "arms": {
            "left": {
                "shoulder_channel": 0,
                "claw_channel": 1,
                "shoulder_min": 0,
                "shoulder_max": 180,
                "claw_min": 20,
                "claw_max": 90,
            },
            "right": {
                "shoulder_channel": 2,
                "claw_channel": 3,
                "shoulder_min": 0,
                "shoulder_max": 180,
                "claw_min": 20,
                "claw_max": 90,
            },
        },
        "move_delay": 0.0,
        "jitter_threshold": 2,
        "uart_port": "/dev/null",
        "uart_baud": 115200,
    }


@patch("src.servo.busio")
@patch("src.servo.board")
@patch("src.servo.PCA9685")
@patch("src.servo.adafruit_servo")
@patch("src.servo.serial.Serial", side_effect=Exception("no uart"))
def test_move_clamps_to_limits(mock_serial, mock_servo_mod, mock_pca, mock_board, mock_busio, servo_config):
    from src.servo import ServoController

    mock_pca_instance = MagicMock()
    mock_pca.return_value = mock_pca_instance
    mock_servo_instance = MagicMock()
    mock_servo_mod.Servo.return_value = mock_servo_instance

    ctrl = ServoController(servo_config)
    ctrl._last_angles["left_claw"] = -999  # force no jitter skip

    ctrl.move("left", "claw", 200)
    actual = ctrl._last_angles["left_claw"]
    assert actual <= 90, f"claw should be clamped to max 90, got {actual}"


@patch("src.servo.busio")
@patch("src.servo.board")
@patch("src.servo.PCA9685")
@patch("src.servo.adafruit_servo")
@patch("src.servo.serial.Serial", side_effect=Exception("no uart"))
def test_jitter_suppression(mock_serial, mock_servo_mod, mock_pca, mock_board, mock_busio, servo_config):
    from src.servo import ServoController

    mock_pca_instance = MagicMock()
    mock_pca.return_value = mock_pca_instance
    mock_servo_instance = MagicMock()
    mock_servo_mod.Servo.return_value = mock_servo_instance

    ctrl = ServoController(servo_config)
    ctrl._last_angles["left_shoulder"] = 90

    # move by 1 deg - should be suppressed (threshold=2)
    ctrl.move("left", "shoulder", 91)
    assert ctrl._last_angles["left_shoulder"] == 90  # unchanged due to jitter


@patch("src.servo.busio")
@patch("src.servo.board")
@patch("src.servo.PCA9685")
@patch("src.servo.adafruit_servo")
@patch("src.servo.serial.Serial", side_effect=Exception("no uart"))
def test_unknown_servo_returns_false(mock_serial, mock_servo_mod, mock_pca, mock_board, mock_busio, servo_config):
    from src.servo import ServoController

    mock_pca.return_value = MagicMock()
    mock_servo_mod.Servo.return_value = MagicMock()

    ctrl = ServoController(servo_config)
    result = ctrl.move("middle", "elbow", 90)
    assert result is False


@patch("src.servo.busio")
@patch("src.servo.board")
@patch("src.servo.PCA9685")
@patch("src.servo.adafruit_servo")
@patch("src.servo.serial.Serial", side_effect=Exception("no uart"))
def test_get_angle_default(mock_serial, mock_servo_mod, mock_pca, mock_board, mock_busio, servo_config):
    from src.servo import ServoController

    mock_pca.return_value = MagicMock()
    mock_servo_mod.Servo.return_value = MagicMock()

    ctrl = ServoController(servo_config)
    angle = ctrl.get_angle("left", "shoulder")
    assert angle == 90
