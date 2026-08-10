from setuptools import setup, find_packages

setup(
    name="grep",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "adafruit-circuitpython-pca9685",
        "adafruit-circuitpython-motor",
        "adafruit-blinka",
        "RPi.GPIO",
        "picamera2",
        "pygame",
        "numpy",
        "PyYAML",
        "requests",
        "websockets",
        "mcp",
        "anthropic",
        "openai",
        "Pillow",
        "pyserial",
        "aiohttp",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "grep-run=scripts.run:main",
            "grep-mcp=scripts.mcp_server:main",
        ],
    },
)
