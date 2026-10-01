# bill of materials

| qty | part | model | notes |
|-----|------|-------|-------|
| 1 | raspberry pi 5 | pi 5 8gb | main compute |
| 1 | pi camera | camera module 3 noir | ir filter removed, low light |
| 1 | servo driver | pca9685 16ch | i2c 0x40 |
| 1 | microcontroller | esp32-c3 devkit | uart arm bridge |
| 4 | servo | mg996r 180deg | 2 per arm |
| 1 | adc | mcp3008 | spi, for ir sensor |
| 1 | ir sensor | gp2y0a21yk0f | proximity 10-80cm |
| 1 | display | 7" 1024x600 lcd | hdmi, face |
| 1 | speaker | jbl go 3 | 3.5mm or bluetooth |
| 1 | bec | 5v 5a sbec | servo power rail |
| 2 | claw arm | diy servo bracket | 3d printed or aluminium |
| 1 | sd card | 64gb+ | class 10 a2 |
| 1 | usb-c psu | 5v 5a pd | pi 5 power |
| 1 | enclosure | custom | mount all components |

## approximate cost

| category | est. usd |
|----------|----------|
| pi 5 8gb | $80 |
| camera module 3 noir | $35 |
| servos x4 | $20 |
| pca9685 | $8 |
| esp32-c3 devkit | $6 |
| lcd 1024x600 | $55 |
| jbl go 3 | $40 |
| sensors + adc | $15 |
| hardware + misc | $25 |
| **total** | **~$284** |

## sourcing notes

- pi 5: rpilocator.com for stock alerts
- camera module 3 noir: adafruit or pimoroni
- mg996r: aliexpress, ~$4 each in bulk
- pca9685 breakout: adafruit product 815 or clone
- gp2y0a21yk0f: digikey or adafruit
- 1024x600 7" hdmi lcd: waveshare or similar
