import machine
import st7789py as st7789
from touch import Touch

# Define const para otimização do MicroPython
try:
    from micropython import const
except ImportError:
    const = lambda x: x
    
_DISPLAY_HEIGHT = const(240)
_DISPLAY_WIDTH = const(320)
_DISPLAY_RESET = const(None)
_DISPLAY_ROTATION = const(1)
PERIPHERAL_PIN = const(10)

# --- Touch constants ---
_TOUCH_I2C_INT = const(16)

def config(spi, dc_pin, cs_pin, bl_pin):
    """Configura e retorna o objeto do display, usando um objeto SPI existente."""
    machine.Pin(PERIPHERAL_PIN, machine.Pin.OUT, value=1)
    return st7789.ST7789(spi,
                _DISPLAY_HEIGHT,
                _DISPLAY_WIDTH,
                reset=_DISPLAY_RESET,
                dc=machine.Pin(dc_pin, machine.Pin.OUT),
                cs=machine.Pin(cs_pin, machine.Pin.OUT),
                backlight=machine.Pin(bl_pin, machine.Pin.OUT),
                rotation=_DISPLAY_ROTATION,
                baudrate=spi.baudrate if hasattr(spi, 'baudrate') else 80_000_000)

def config_touch(i2c):
    """Inicializa e retorna o driver de touch GT911."""
    # Garante que a alimentação dos periféricos está ligada
    machine.Pin(PERIPHERAL_PIN, machine.Pin.OUT, value=1)

    return Touch(
        i2c,
        int_pin=_TOUCH_I2C_INT,
        width=_DISPLAY_WIDTH,
        height=_DISPLAY_HEIGHT,
        swap_xy=True,
        mirror_y=True)