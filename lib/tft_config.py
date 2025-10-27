import machine
import st7789py as st7789
from touch import Touch

_DISPLAY_HEIGHT = const(240)
_DISPLAY_WIDTH = const(320)
_DISPLAY_SPI_ID = const(1)
_DISPLAY_BAUDRATE = const(80_000_000)
_DISPLAY_SCK = const(40)
_DISPLAY_MOSI = const(41)
_DISPLAY_MISO = const(38)
_DISPLAY_RESET = const(None)
_DISPLAY_CS = const(12)
_DISPLAY_DC = const(11)
_DISPLAY_BACKLIGHT = const(42)
_DISPLAY_ROTATION = const(1)
PERIPHERAL_PIN = const(10)

# --- Touch constants ---
_TOUCH_I2C_SDA = const(18)
_TOUCH_I2C_SCL = const(8)
_TOUCH_I2C_INT = const(16)
_TOUCH_I2C_FREQ = const(400000)

def config():
    machine.Pin(PERIPHERAL_PIN, machine.Pin.OUT, value=1)
    return st7789.ST7789(machine.SPI(
                _DISPLAY_SPI_ID,
                baudrate=_DISPLAY_BAUDRATE,
                sck=machine.Pin(_DISPLAY_SCK),
                mosi=machine.Pin(_DISPLAY_MOSI),
                miso=machine.Pin(_DISPLAY_MISO),
                ),
                _DISPLAY_HEIGHT,
                _DISPLAY_WIDTH,
                reset=_DISPLAY_RESET,
                dc=machine.Pin(_DISPLAY_DC, machine.Pin.OUT),
                cs=machine.Pin(_DISPLAY_CS, machine.Pin.OUT),
                backlight=machine.Pin(_DISPLAY_BACKLIGHT, machine.Pin.OUT),
                rotation=_DISPLAY_ROTATION)

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