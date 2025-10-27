"""Hardware initialization module for T-Deck"""

import machine
import time
import tft_config as tft
import st7789py as st7789

# Keyboard and I2C configuration
KBD_INT_PIN = 46
KBD_I2C_ADDR = 0x55
I2C_SCL_PIN = 8
I2C_SDA_PIN = 18
I2C_FREQ = 400000

def init_hardware():
    """Initialize all hardware components and return configured objects"""

    # Enable peripheral power (keyboard and touch)
    machine.Pin(tft.PERIPHERAL_PIN, machine.Pin.OUT, value=1)
    time.sleep(0.2)

    # Create shared I2C instance
    i2c = machine.SoftI2C(scl=machine.Pin(I2C_SCL_PIN), sda=machine.Pin(I2C_SDA_PIN), freq=I2C_FREQ)

    # Initialize display
    display = tft.config()
    display.fill(st7789.color565(30, 30, 30))  # Dark gray background

    # Initialize touch
    touch = tft.config_touch(i2c)

    # Configure keyboard interrupt pin (not used in current implementation)
    kbd_int = machine.Pin(KBD_INT_PIN, machine.Pin.IN)

    print("Display, Touch e Teclado inicializados.")

    return display, touch, i2c, kbd_int
