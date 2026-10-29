![grep](bg.gif)

```
  ██████╗ ██████╗ ███████╗██████╗
 ██╔════╝ ██╔══██╗██╔════╝██╔══██╗
 ██║  ███╗██████╔╝█████╗  ██████╔╝
 ██║   ██║██╔══██╗██╔══╝  ██╔═══╝
 ╚██████╔╝██║  ██║███████╗██║
  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝
```

**autonomous observation machine**

grep is a physical robot that sits in a room and watches. it has two arms with claws, a camera, an ir sensor, a face on an lcd, and a british voice. any llm agent can control it remotely via mcp.

---

## hardware

| part | model | notes |
|------|-------|-------|
| compute | raspberry pi 5 (8gb) | main brain |
| servo driver | pca9685 | i2c 0x40, 16-channel pwm |
| arms | 2x dual-servo claw arms | shoulder + claw joints |
| arm driver | esp32-c3 | uart bridge to pca9685 |
| camera | pi camera module 3 noir | no-ir-filter, low light |
| ir sensor | gp2y0a21yk0f | gpio 17 via adc, 10-80cm |
| display | 7" 1024x600 lcd | hdmi, oscilloscope face |
| speaker | jbl go 3 | bluetooth/3.5mm |

---

## architecture

```
                    ┌─────────────────┐
  mcp client ──────►│   mcp server    │
  (any llm)         │  (port 8765)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   core loop     │
                    │  (src/core.py)  │
                    └─┬──┬──┬──┬──┬──┘
                      │  │  │  │  │
              ┌───────┘  │  │  │  └────────┐
              ▼          ▼  ▼  ▼           ▼
         ┌────────┐ ┌──────┐ ┌─────┐ ┌────────┐
         │ servo  │ │ face │ │ tts │ │ camera │
         └────────┘ └──────┘ └─────┘ └────────┘
              │
         ┌────▼────┐
         │ esp32c3 │
         │ (uart)  │
         └─────────┘
```

---

## quick start

```bash
git clone https://github.com/softkernels/grep.git
cd grep
pip install -e .

# edit config
cp config/default.yaml config/local.yaml
nano config/local.yaml

# run
python scripts/run.py
```

to expose the mcp server:

```bash
python scripts/mcp_server.py --host 0.0.0.0 --port 8765
```

---

## mcp tools

| tool | args | description |
|------|------|-------------|
| `move_arm` | `arm, joint, angle` | move a servo joint to angle (degrees) |
| `get_sensor` | none | read ir proximity distance (cm) |
| `capture_image` | none | take photo, return base64 jpeg |
| `set_expression` | `name` | set face expression by name |
| `speak` | `text` | say something via tts |
| `get_status` | none | full robot state snapshot |
| `wave` | none | wave animation sequence |
| `look_at` | `direction` | turn camera/face direction |

---

## agent config

```yaml
# config/agents.yaml
agents:
  observer:
    model: claude-3-5-sonnet-20241022
    system: "you are controlling a physical robot called grep. observe and report."
    tools: [get_sensor, capture_image, get_status]
  actor:
    model: gpt-4o
    system: "you control grep's body. move arms, set expressions, speak."
    tools: [move_arm, set_expression, speak, wave, look_at]
```

---

## connecting an llm

```python
from examples.connect_claude import GrepClient

client = GrepClient(host="raspberrypi.local", port=8765)
client.connect()
```

see `examples/` for claude, gpt-4, and multi-agent setups.

run with env vars:
```bash
GREP_HOST=raspberrypi.local python examples/connect_claude.py
```

---

built by [@softkernels](https://github.com/softkernels)

## license

mit. see [LICENSE](LICENSE).
