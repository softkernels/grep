# assembly guide

## tools needed

- small phillips screwdriver
- m2/m3 hex standoffs and screws
- zip ties or velcro
- heatshrink tubing
- soldering iron (for power connectors)

## step 1: mount pi 5

mount pi 5 to base plate using m2.5 standoffs (30mm height).
route camera ribbon through slot before securing pi.

## step 2: lcd display

attach 7" lcd on front face of enclosure.
connect hdmi-0 (left port on pi 5) to display hdmi input.
power display from USB or dedicated 5V rail.

## step 3: pca9685 servo driver

mount pca9685 board on m2 standoffs near pi.
wire i2c as per wiring guide. confirm address 0x40 (all addr pads open).

## step 4: mcp3008 adc

mount on breadboard or header strip.
wire spi per wiring guide. keep wires short for signal integrity.

## step 5: ir sensor

mount gp2y0a21yk0f on front of enclosure, pointing outward.
angle: horizontal, at "chest" height.
connect to mcp3008 ch0 per wiring guide.

## step 6: servo arms

attach arm bracket hardware to side mounts.
for each arm:
1. attach shoulder servo to main bracket
2. attach claw servo at end of arm
3. connect signal wires to pca9685 channels (see pinout.txt)
4. connect power to V+ rail

## step 7: esp32-c3 (optional)

if using esp32-c3 as uart bridge:
flash firmware from `firmware/` directory.
mount near pca9685 and wire uart to pi per wiring guide.

## step 8: speaker

jbl go 3 via 3.5mm audio jack to pi 3.5mm output.
or pair via bluetooth (`bluetoothctl`).
test: `aplay /usr/share/sounds/alsa/Front_Left.wav`

## step 9: camera

attach camera module 3 noir to camera mount on top of enclosure.
connect ribbon cable to pi camera port (CAM/DISP 1, use the 15-pin connector).
secure cable with tape or clamp.

## step 10: power up

1. connect BEC to servo rail (NOT pi first)
2. connect pi USB-C power
3. check no hot components
4. `i2cdetect -y 1` should show 0x40
5. run `python scripts/test_servos.py` to verify

## cable management

- bundle servo wires with zip ties
- keep signal wires away from servo power wires
- use heatshrink on all solder joints
