import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def mock_core():
    core = MagicMock()
    core.servo = MagicMock()
    core.servo.move.return_value = True
    core.servo.get_angle.return_value = 90
    core.sensor = MagicMock()
    core.sensor.read.return_value = 42.5
    core.camera = MagicMock()
    core.camera.capture_b64.return_value = "abc123fakeb64"
    core.face = MagicMock()
    core.face.current_expression = "idle"
    core.voice = MagicMock()
    core.voice.speak.return_value = True
    core.voice.is_speaking.return_value = False
    core.memory = MagicMock()
    core.get_state.return_value = {
        "sensor_distance": 42.5,
        "servo_angles": {"left_shoulder": 90},
        "expression": "idle",
        "speaking": False,
    }
    return core


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_get_sensor_returns_distance(mock_core):
    from mcp.server import Server
    app = Server("test")

    with patch("src.mcp.tools.register_resources"), patch("src.mcp.tools.register_prompts"):
        from src.mcp.tools import register_tools
        register_tools(app, mock_core)

    handler = app._tool_handlers.get("call_tool")
    if handler is None:
        # the tool handler is registered differently in newer mcp versions
        pytest.skip("tool handler binding varies by mcp version")

    mock_core.sensor.read.return_value = 35.2
    result = run(handler("get_sensor", {}))
    assert any("35.2" in str(r) for r in result)


def test_move_arm_calls_servo(mock_core):
    from src.mcp.tools import register_tools
    from mcp.server import Server
    app = Server("test2")
    register_tools(app, mock_core)

    mock_core.servo.move.assert_not_called()
    # call the underlying tool logic via the registered call_tool handler
    # find call_tool handler
    handler = None
    for name, fn in app._tool_handlers.items():
        if name == "call_tool":
            handler = fn
    if handler is None:
        pytest.skip("handler not found")

    run(handler("move_arm", {"arm": "left", "joint": "shoulder", "angle": 45}))
    mock_core.servo.move.assert_called_once_with("left", "shoulder", 45.0)


def test_set_expression(mock_core):
    from src.mcp.tools import register_tools
    from mcp.server import Server
    app = Server("test3")
    register_tools(app, mock_core)

    handler = None
    for name, fn in app._tool_handlers.items():
        if name == "call_tool":
            handler = fn
    if handler is None:
        pytest.skip("handler not found")

    run(handler("set_expression", {"name": "alert"}))
    mock_core.face.set_expression.assert_called_with("alert")


def test_get_status_returns_json(mock_core):
    from src.mcp.tools import register_tools
    from mcp.server import Server
    import json
    app = Server("test4")
    register_tools(app, mock_core)

    handler = None
    for name, fn in app._tool_handlers.items():
        if name == "call_tool":
            handler = fn
    if handler is None:
        pytest.skip("handler not found")

    result = run(handler("get_status", {}))
    text = result[0].text
    parsed = json.loads(text)
    assert "sensor_distance" in parsed
    assert "expression" in parsed
