# wiring guide

## overview

```
pi 5
├── i2c  ──► pca9685 (0x40)
│              ├── ch0 ──► left shoulder servo
│              ├── ch1 ──► left claw servo
│              ├── ch2 ──► right shoulder servo
│              └── ch3 ──► right claw servo
├── spi  ──► mcp3008 adc
│              └── ch0 ──► gp2y0a21yk0f ir sensor
├── uart ──► esp32-c3 (optional arm bridge)
├── hdmi ──► 1024x600 lcd
└── 3.5mm ──► jbl go 3
```

## i2c: pi to pca9685

| pi pin | pca9685 pin |
|--------|-------------|
| pin 1 (3.3v) | vcc |
| pin 6 (gnd) | gnd |
| pin 3 (sda) | sda |
| pin 5 (scl) | scl |

pca9685 V+ rail: connect to 5V BEC (not pi 5V - servos draw too much current)

## spi: pi to mcp3008

| pi pin | mcp3008 pin |
|--------|-------------|
| pin 1 (3.3v) | vdd, vref |
| pin 6 (gnd) | agnd, dgnd |
| pin 19 (mosi) | din |
| pin 21 (miso) | dout |
| pin 23 (sclk) | clk |
| pin 24 (ce0) | cs/shdn |

## ir sensor: gp2y0a21yk0f to mcp3008

| sensor wire | connects to |
|-------------|-------------|
| red (vcc) | 5v |
| black (gnd) | gnd |
| yellow (signal) | mcp3008 ch0 (pin 1) |

note: sensor needs 5V supply. signal output is 0-3V, safe for mcp3008 with 3.3V vref.

## uart: pi to esp32-c3 (optional)

| pi pin | esp32-c3 |
|--------|----------|
| pin 8 (tx gpio14) | rx |
| pin 10 (rx gpio15) | tx |
| pin 6 (gnd) | gnd |

esp32-c3 runs at 3.3V logic - compatible with pi 5.

## servos to pca9685

each servo:
- red (vcc) -> V+ rail (5V BEC, NOT pca9685 vcc)
- brown/black (gnd) -> shared ground
- orange/yellow (signal) -> pca9685 channel pin

## power

```
wall ──► usb-c pd adapter (5v 5a) ──► pi 5
battery ──► 5V BEC ──► servo V+ rail + pca9685 V+
```

run separate ground wire from BEC gnd to pi gnd (common ground).
